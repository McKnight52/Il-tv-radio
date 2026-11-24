import concurrent.futures as cf
import datetime as dt
import json, re, subprocess, unicodedata
from pathlib import Path
from urllib.parse import urlsplit
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
    u=e['url']; ua=attr(e['meta'][0],'http-user-agent') or 'IPTV-Maintainer/1.0'
    if urlsplit(u).scheme not in ('http','https'): return 'unsupported protocol'
    try:
        with requests.get(u,headers={'User-Agent':ua},stream=True,timeout=(6,10)) as r:
            if r.status_code!=200: return f'HTTP {r.status_code}'
            data=next(r.iter_content(4096),b'')
            if not data: return 'empty response'
            if b'<html' in data.lower() or b'<!doctype html' in data.lower(): return 'HTML instead of media'
        cmd=['ffprobe','-v','error','-tls_verify','1','-rw_timeout','10000000','-user_agent',ua,'-show_entries','stream=codec_type,codec_name,nb_read_packets','-of','json','-read_intervals','%+2','-count_packets',u]
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=25)
        streams=json.loads(p.stdout or '{}').get('streams',[])
        wanted='audio' if radio(e) else 'video'
        if p.returncode==0 and any(s.get('codec_type')==wanted and int(s.get('nb_read_packets','0'))>0 for s in streams): return 'ok'
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
    tv=[]; radios=[]; errors=[]
    for url in cfg['tv_sources']:
        try:
            r=requests.get(url,timeout=20); r.raise_for_status(); tv+=parse(r.text)
        except Exception as ex: errors.append(str(ex))
    try:
        r=requests.get(cfg['radio_source'],timeout=20); r.raise_for_status(); radios=r.json()
    except Exception as ex: errors.append(str(ex))
    return tv,radios,errors
def candidates(e,tv,radios,cfg):
    urls=list(cfg['official_urls'].get(key(e),[]))
    if radio(e):
        uid=key(e).removeprefix('radio-')
        urls += [r.get('url_resolved') or r.get('url') for r in radios if r.get('stationuuid')==uid]
    else:
        urls += [x['url'] for x in tv if key(x)==key(e) and attr(x['meta'][0],'tvg-id')]
    return list(dict.fromkeys(u for u in urls if u and u!=e['url'] and urlsplit(u).scheme in ('https','http')))[:cfg['max_candidates']]
def main():
    cfg=load(ROOT/'config.json',{}); state=load(ROOT/'status.json',{}); history=load(ROOT/'replacements.json',[])
    active=ROOT/'israel.m3u'; unavailable=ROOT/'unavailable.m3u'; header=active.read_text().splitlines()[0]
    old=clean(parse(active.read_text())); es=clean(old+parse(unavailable.read_text() if unavailable.exists() else ''))
    if not old: raise RuntimeError('Empty input playlist')
    day=dt.datetime.now(dt.timezone.utc).date().isoformat()
    tv,radios,errors=sources(cfg)
    with cf.ThreadPoolExecutor(max_workers=cfg['workers']) as pool: results=list(pool.map(retry,es))
    oldkeys={(key(e),e['url']) for e in old}; failed=sum(r!='ok' and (key(e),e['url']) in oldkeys for e,r in zip(es,results))
    freeze=failed/len(old)>=cfg['mass_failure_fraction']; good=[]; bad=[]; rows=[]; changes=[]
    for e,result in zip(es,results):
        k=key(e); st=state.setdefault(k,{}); was_active=(k,e['url']) in oldkeys
        if result!='ok' and not freeze:
            for u in candidates(e,tv,radios,cfg):
                alt={'meta':[re.sub(r'\s+http-user-agent="[^"]*"','',e['meta'][0])],'url':u}
                if check(alt)=='ok':
                    change={'date':day,'channel':name(e),'old':e['url'],'new':u}; history.append(change); changes.append(change); e=alt; result='ok'; break
        if result=='ok': st.update(failures=0,last_success=day,last_check=day); good.append(e)
        else:
            # Foreign runners cannot distinguish geo-blocking from access denial.
            uncertain=cfg['foreign_runner'] and ('403' in result or '451' in result or 'timeout' in result.lower() or 'connection' in result.lower())
            if not freeze and not uncertain and st.get('last_check')!=day: st['failures']=st.get('failures',0)+1
            if was_active and (freeze or uncertain or st.get('failures',0)<cfg['failure_days']): good.append(e)
            else: bad.append(e)
            st['last_check']=day
        st['result']=result; rows.append((name(e),result,st.get('last_success','never'),st.get('failures',0),radio(e)))
    if not good: raise RuntimeError('Refusing empty playlist')
    if not freeze:
        save(active,playlist(good,header)); save(unavailable,playlist(bad,header))
    save(ROOT/'status.json',json.dumps(state,ensure_ascii=False,indent=2)+'\n'); save(ROOT/'replacements.json',json.dumps(history,ensure_ascii=False,indent=2)+'\n')
    report=[f'# IPTV report — {day}',f'Total: {len(es)}',f'Working TV: {sum(r[1]=="ok" and not r[4] for r in rows)}',f'Working radio: {sum(r[1]=="ok" and r[4] for r in rows)}',f'Failed: {sum(r[1]!="ok" for r in rows)}',f'Replacements: {len(changes)}',f'Mass failure freeze: {freeze}',*errors,'','| Channel | Result | Last success | Failed days |','|---|---|---|---|']
    report += ['| '+' | '.join(str(x).replace('|','/').replace('\n',' ') for x in r[:4])+' |' for r in rows]
    report += ['','## Replacements']+[f'- {c["channel"]}: {c["old"]} → {c["new"]}' for c in changes]
    save(ROOT/'report.md','\n'.join(report)+'\n')
if __name__=='__main__': main()
