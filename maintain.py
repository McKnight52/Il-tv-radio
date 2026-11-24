import concurrent.futures as cf
import datetime as dt
import json, re, subprocess, unicodedata
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl
from collections import Counter
import requests

ROOT=Path(__file__).resolve().parent
SPORT={'5Gold','5Live','5Max','5Plus','5Sport4K','5Sport','5Stars','One','One2','OneDoco','OneEdge','Sport1','Sport2','Sport3','Sport4'}
def attr(s,k):
    m=re.search(r'\b'+re.escape(k)+r'="([^"]*)"',s)
    return m.group(1) if m else ''
def parse(s):
    entries=[]; block=[]
    for line in s.splitlines():
        line=line.strip()
        if line.startswith('#EXTINF:'): block=[line]
        elif block and line.startswith('#'): block.append(line)
        elif block and line:
            entries.append({'meta':block,'url':line}); block=[]
    return entries
def key(e): return attr(e['meta'][0],'tvg-id') or name(e)
def name(e): return re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)',e['meta'][0],maxsplit=1)[-1]
def radio(e): return attr(e['meta'][0],'radio')=='true'
def sports(e): return not radio(e) and (key(e).split('.')[0] in SPORT or bool(re.search(r'\bsports?\b',attr(e['meta'][0],'group-title'),re.I)))
def clean(es):
    seen=set(); out=[]
    for e in es:
        k=(key(e),e['url'])
        if not sports(e) and k not in seen: out.append(e); seen.add(k)
    return out
def playlist(es,header='#EXTM3U'): return header+'\n'+'\n'.join('\n'.join(e['meta']+[e['url']]) for e in es)+'\n'
def load(p,default): return json.loads(p.read_text()) if p.exists() else default
def save(p,v):
    tmp=p.with_suffix(p.suffix+'.tmp'); tmp.write_text(v,encoding='utf-8'); tmp.replace(p)
def norm(s): return ''.join(c for c in unicodedata.normalize('NFKC',s).casefold() if c.isalnum())
def check(e):
    u=e['url']; ua=attr(e['meta'][0],'http-user-agent') or next((x.split('=',1)[1] for x in e['meta'][1:] if x.startswith('#EXTVLCOPT:http-user-agent=')), 'IPTV-Maintainer/1.0')
    if urlsplit(u).scheme not in ('http','https'): return 'unsupported protocol'
    try:
        with requests.get(u,headers={'User-Agent':ua},stream=True,timeout=(6,10)) as r:
            if r.status_code!=200: return f'HTTP {r.status_code}'
            data=next(r.iter_content(4096),b'')
            if not data: return 'empty response'
            if b'<html' in data.lower() or b'<!doctype html' in data.lower(): return 'HTML instead of media'
        cmd=['ffprobe','-v','error','-tls_verify','1','-protocol_whitelist','http,https,tcp,tls,crypto','-rw_timeout','10000000','-user_agent',ua,'-show_entries','stream=codec_type,codec_name,nb_read_packets','-of','json','-read_intervals','%+2','-count_packets',u]
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=25)
        streams=json.loads(p.stdout or '{}').get('streams',[])
        wanted='audio' if radio(e) else 'video'
        if p.returncode==0 and any(s.get('codec_type')==wanted and str(s.get('nb_read_packets','0')).isdigit() and int(s['nb_read_packets'])>0 for s in streams): return 'ok'
        return 'media probe failed: '+p.stderr.strip()[:160]
    except requests.exceptions.SSLError: return 'TLS error'
    except requests.exceptions.Timeout: return 'HTTP timeout'
    except requests.exceptions.ConnectionError as ex: return 'connection/DNS error: '+str(ex)[:120]
    except subprocess.TimeoutExpired: return 'media probe timeout'
    except Exception as ex: return str(ex)[:160]
def retry(e):
    result=check(e)
    return result if result=='ok' else check(e)
def sources(cfg):
    tv=[]; radios=[]; errors=[]; counts={}
    def get(url):
        r=requests.get(url,timeout=(8,30),headers={'User-Agent':'IPTV-Maintainer/2.0'}); r.raise_for_status(); return r
    for url in cfg['tv_sources']:
        try:
            items=parse(get(url).text); counts[url]=len(items)
            tv += [{'id':key(x),'url':x['url'],'source':'IPTV-org M3U',
                    'headers':any(any(t in line.lower() for t in ('http-referrer','http-referer','http-user-agent','#kodiprop:')) for line in x['meta'])} for x in items]
        except Exception as ex: errors.append(f'{url}: {ex}')
    if cfg.get('tv_api'):
        url=cfg['tv_api']
        try:
            items=get(url).json(); counts[url]=len(items)
            tv += [{'id':x['channel']+('@'+x['feed'] if x.get('feed') else ''),'url':x.get('url'),'source':'IPTV-org API',
                    'headers':bool(x.get('referrer') or x.get('user_agent'))} for x in items if x.get('channel')]
        except Exception as ex: errors.append(f'{url}: {ex}')
    for url in cfg.get('radio_sources',[cfg['radio_source']]):
        try:
            radios=get(url).json()
            if not isinstance(radios,list) or not radios: raise ValueError('empty or invalid station database')
            counts[url]=len(radios); break
        except Exception as ex: errors.append(f'{url}: {ex}'); radios=[]
    return tv,radios,errors,counts

def host(u): return (urlsplit(u).hostname or '').lower()
def on_domain(h,d): return h==d or h.endswith('.'+d)
def compatible_id(a,b):
    x,_,f=a.partition('@'); y,_,g=b.partition('@')
    return x==y and (f==g or {f.lower(),g.lower()} <= {'','sd','hd','fhd','uhd','4k'})
def safe_candidate(u):
    try:
        p=urlsplit(u)
        return p.scheme in ('http','https') and bool(p.hostname) and not (p.username or p.password or p.fragment or any(k.casefold() in {'token','auth','signature','sig','key','expires','hdnea','hdnts','jwt','session','access_token'} for k,v in parse_qsl(p.query))) and not any(c in u for c in '\r\n')
    except ValueError: return False

def candidates(e,tv,radios,cfg):
    k=key(e); items=[]; seen=set(); approved=cfg.get('approved_hosts',{}).get(k,[])
    explicit=cfg.get('official_urls',{}).get(k,[])
    def add(u,source,headers=False,allow=False):
        if not u or u==e['url'] or not safe_candidate(u): return
        if u in seen: return
        seen.add(u)
        reason=''
        if any(on_domain(host(u),d) for d in cfg.get('suspect_hosts',[])): reason='suspect provider; not used for repairs'
        elif headers: reason='requires special headers; manual review'
        elif not (allow or any(on_domain(host(u),d) for d in approved)): reason='source authorization needs review'
        items.append({'url':u if not reason else f'{urlsplit(u).scheme}://{host(u)}/[path withheld]', 'source':source,'skip':reason})
    for u in explicit: add(u,'configured broadcaster candidate',allow=True)
    if radio(e):
        uid=k.removeprefix('radio-'); names={norm(x) for x in [name(e),*cfg.get('radio_aliases',{}).get(k,[])]}
        exact=[r for r in radios if r.get('countrycode')=='IL' and r.get('stationuuid')==uid]
        named=[r for r in radios if r.get('countrycode')=='IL' and norm(r.get('name','')) in names and r not in exact]
        for group,src in [(exact,'Radio Browser UUID'),(named,'Radio Browser exact name/alias')]:
            for r in sorted(group,key=lambda r:(r.get('lastcheckok')==1,r.get('votes') or 0),reverse=True):
                # Name match alone is not proof of authorization. Explicit domains or URLs are required.
                for u in (r.get('url_resolved'),r.get('url')): add(u,src)
    else:
        ids=[k,*cfg.get('tv_aliases',{}).get(k,[])]
        for x in sorted(tv,key=lambda x:(x['id']!=k,not str(x.get('url','')).startswith('https://'))):
            if any(compatible_id(i,x['id']) for i in ids): add(x['url'],x['source'],x['headers'])
    return items

def repair(task,tv,radios,cfg):
    e,result=task; attempts=[]
    if result=='ok': return e,result,attempts,None
    used=0
    for c in candidates(e,tv,radios,cfg):
        if c['skip']: outcome=c['skip']
        elif used>=cfg['max_candidates']: outcome='candidate limit reached'
        else:
            used+=1
            # Never carry provider-specific headers/DRM options to a new provider.
            meta=[re.sub(r'\s+(?:http-user-agent|http-referrer|http-referer)="[^"]*"','',e['meta'][0])]
            meta+= [m for m in e['meta'][1:] if not m.lower().startswith(('#extvlcopt:','#kodiprop:'))]
            alt={'meta':meta,'url':c['url']}; outcome=retry(alt)
            if outcome=='ok':
                attempts.append({**c,'result':outcome})
                return alt,'ok',attempts,{'channel':name(e),'old':e['url'],'new':alt['url'],'source':c['source']}
        attempts.append({**c,'result':outcome})
    return e,result,attempts,None

def advance(st,day,result,uncertain,freeze,url):
    # A manual rerun on the same UTC day cannot increase a streak twice.
    if st.get('url') and st['url']!=url:
        for field in ('failures','observed_failures','last_failed_day','last_counted_day'): st.pop(field,None)
    if result=='ok':
        st.update(failures=0,observed_failures=0,last_success=day,last_check=day,url=url,result=result)
        st.pop('last_failed_day',None); st.pop('last_counted_day',None)
    else:
        yesterday=(dt.date.fromisoformat(day)-dt.timedelta(days=1)).isoformat()
        if st.get('last_failed_day')!=day:
            st['observed_failures']=(st.get('observed_failures',0) if st.get('last_failed_day')==yesterday else 0)+1
            st['last_failed_day']=day
        if not uncertain and not freeze and st.get('last_counted_day')!=day:
            st['failures']=(st.get('failures',0) if st.get('last_counted_day')==yesterday else 0)+1
            st['last_counted_day']=day
        st.update(last_check=day,url=url,result=result)
    return st

def main():
    cfg=load(ROOT/'config.json',{}); state=load(ROOT/'status.json',{}); history=load(ROOT/'replacements.json',[])
    active=ROOT/'israel.m3u'; unavailable=ROOT/'unavailable.m3u'; header=active.read_text().splitlines()[0]
    old=clean(parse(active.read_text())); es=clean(old+parse(unavailable.read_text() if unavailable.exists() else ''))
    if not old: raise RuntimeError('Empty input playlist')
    day=dt.datetime.now(dt.timezone.utc).date().isoformat()
    tv,radios,errors,counts=sources(cfg)
    with cf.ThreadPoolExecutor(max_workers=cfg['workers']) as pool: results=list(pool.map(retry,es))
    oldkeys={(key(e),e['url']) for e in old}; failed=sum(r!='ok' and (key(e),e['url']) in oldkeys for e,r in zip(es,results))
    freeze=failed/len(old)>=cfg['mass_failure_fraction']; good=[]; bad=[]; rows=[]; changes=[]; details=[]; hosts=Counter()
    if freeze: repaired=[(e,r,[],None) for e,r in zip(es,results)]
    else:
        with cf.ThreadPoolExecutor(max_workers=cfg['workers']) as pool: repaired=list(pool.map(lambda t:repair(t,tv,radios,cfg),zip(es,results)))
    for original,initial,(e,result,attempts,change) in zip(es,results,repaired):
        k=key(e); st=state.setdefault(k,{}); was_active=(key(original),original['url']) in oldkeys
        if initial!='ok': hosts[host(original['url'])]+=1
        if change:
            change['date']=day; history.append(change); changes.append(change)
        local=original['url'] in cfg.get('locally_failed_urls',[]) and result=='HTTP 403'
        uncertain=bool(cfg['foreign_runner'] and not local and ('403' in result or '451' in result or 'timeout' in result.lower() or 'connection' in result.lower()))
        advance(st,day,result,uncertain,freeze,e['url'])
        if result=='ok' or (was_active and (freeze or uncertain or st.get('failures',0)<cfg['failure_days'])): good.append(e); disposition='active'
        else: bad.append(e); disposition='unavailable'
        if freeze: disposition='active' if was_active else 'unavailable'
        st.update(uncertain=uncertain,disposition=disposition,attempts=attempts)
        rows.append((name(e),result,st.get('last_success','never'),st.get('observed_failures',0),st.get('failures',0),disposition+(' / uncertain' if uncertain else ''),radio(e)))
        if initial!='ok': details.append((name(e),initial,attempts,cfg.get('official_pages',{}).get(k,'')))
    if not good: raise RuntimeError('Refusing empty playlist')
    if not freeze:
        save(active,playlist(good,header)); save(unavailable,playlist(bad,header))
    save(ROOT/'status.json',json.dumps(state,ensure_ascii=False,indent=2)+'\n'); save(ROOT/'replacements.json',json.dumps(history,ensure_ascii=False,indent=2)+'\n')
    report=[f'# IPTV report — {day}',f'Total: {len(es)}',f'Working TV: {sum(r[1]=="ok" and not r[6] for r in rows)}',f'Working radio: {sum(r[1]=="ok" and r[6] for r in rows)}',f'Failed: {sum(r[1]!="ok" for r in rows)}',f'Replacements: {len(changes)}',f'Mass failure freeze: {freeze}',f'Unavailable entries: {len(bad)} (proposed only during freeze)','', '## Sources',*[f'- {url}: {count} entries' for url,count in counts.items()],*[f'- Source error: {x}' for x in errors],'','## Initial failures by host',*[f'- {h}: {n}' for h,n in hosts.most_common()],'','| Channel | Result | Last success | Observed failed days | Counted failed days | Disposition |','|---|---|---|---|---|---|']
    report += ['| '+' | '.join(str(x).replace('|','/').replace('\n',' ') for x in r[:6])+' |' for r in rows]
    report += ['','## Replacements']+[f'- {c["channel"]}: {c["old"]} → {c["new"]} ({c["source"]})' for c in changes]
    report += ['','## Repair attempts']
    for n,r,attempts,page in details:
        report += [f'### {n} — {r}',f'Candidates discovered: {len(attempts)}' + (' (search stopped after success)' if any(a['result']=='ok' for a in attempts) else ''),*( [f'Official viewing/reference page: {page}'] if page else [])]
        report += [f'- {a["source"]}: {a["url"]} — {a["result"]}' for a in attempts] or ['- No distinct eligible candidate found, or mass-failure freeze is active.']
    save(ROOT/'report.md','\n'.join(report)+'\n')
if __name__=='__main__': main()
