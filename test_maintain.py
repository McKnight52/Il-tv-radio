import json, tempfile, unittest
from unittest.mock import patch
from pathlib import Path
import maintain as m

def entry(k,n='Test',url='https://old.example/stream',radio=False):
    return {'meta':[f'#EXTINF:-1 tvg-id="{k}" tvg-logo="logo.png" group-title="Israel"'+(' radio="true"' if radio else '')+','+n],'url':url}

class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.cfg=json.loads(Path(__file__).with_name('config.json').read_text())
    def test_radio_fallback_alias(self):
        e=entry('radio-fallback-makan','Makan Radio',radio=True)
        rows=[{'stationuuid':'new','countrycode':'IL','name':'מכאן','url':'https://radio.kan.org.il/live.mp3'}, {'stationuuid':'bad','countrycode':'IL','name':'Makan 33','url':'https://radio.kan.org.il/wrong.mp3'}]
        cs=m.candidates(e,[],rows,self.cfg)
        self.assertTrue(any(c['url']==rows[0]['url'] and not c['skip'] for c in cs))
        self.assertFalse(any(c['url']==rows[1]['url'] for c in cs))
    def test_feed_and_alias(self):
        self.assertTrue(m.compatible_id('Channel13.il@SD','Channel13.il'))
        self.assertFalse(m.compatible_id('i24NEWSHebrew.il@SD','i24NEWSArabic.il@SD'))
        self.assertFalse(m.compatible_id('AngelTV.in@Hebrew','AngelTV.in@English'))
        e=entry('KnessetChannel.il@SD')
        cs=m.candidates(e,[{'id':'Knesset.il','url':'https://www.knesset.tv/public.m3u8','source':'fixture','headers':False}],[],self.cfg)
        self.assertEqual(len(cs),1); self.assertFalse(cs[0]['skip'])
    def test_repair_and_metadata(self):
        e=entry('KanEducational.il@SD','Kan Educational')
        with patch.object(m,'retry',return_value='ok'):
            alt,result,attempts,change=m.repair((e,'HTTP 403'),[],[],self.cfg)
        self.assertEqual(result,'ok'); self.assertEqual(alt['meta'],e['meta']); self.assertNotEqual(alt['url'],e['url']); self.assertIsNotNone(change)
    def test_unauthorized_never_probed(self):
        e=entry('HOTDrama.il@SD')
        rows=[{'id':'HOTDrama.il','url':'https://unknown.example/live.m3u8','source':'fixture','headers':False}]
        with patch.object(m,'retry') as check:
            alt,result,attempts,change=m.repair((e,'HTTP 403'),rows,[],self.cfg)
        check.assert_not_called(); self.assertIsNone(change); self.assertEqual(result,'HTTP 403'); self.assertIn('review',attempts[0]['result'])
    def test_days(self):
        s={}
        for day in ['2026-11-24','2026-11-24','2026-11-25','2026-11-26']:
            m.advance(s,day,'HTTP 403',False,False,'url')
        self.assertEqual(s['failures'],3); self.assertEqual(s['observed_failures'],3)
        m.advance(s,'2026-11-27','ok',False,False,'url'); self.assertEqual(s['failures'],0)
        m.advance(s,'2026-11-28','HTTP 403',True,False,'url'); self.assertEqual(s['failures'],0); self.assertEqual(s['observed_failures'],1)
    def test_safe_candidate(self):
        for u in ['file:///etc/passwd','https://user:pass@example.com/live','https://example.com/live?token=abc']:
            self.assertFalse(m.safe_candidate(u))
    def test_full_main_and_restore(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); cfg=dict(self.cfg); cfg['mass_failure_fraction']=0.9
            (p/'config.json').write_text(json.dumps(cfg)); a=entry('KanEducational.il@SD','Kan Educational'); b=entry('Kan11.il@SD','Kan 11'); c=entry('radio-fallback-makan','Makan Radio',radio=True)
            (p/'israel.m3u').write_text(m.playlist([a,b])); (p/'unavailable.m3u').write_text(m.playlist([c]));
            with patch.object(m,'ROOT',p), patch.object(m,'sources',return_value=([],[],[],{})), patch.object(m,'retry',side_effect=lambda e:'HTTP 403' if e['url']==a['url'] and m.key(e)==m.key(a) else 'ok'):
                m.main()
            self.assertEqual(len(m.parse((p/'israel.m3u').read_text())),3); self.assertEqual(len(json.loads((p/'replacements.json').read_text())),1)
            self.assertEqual(len(m.parse((p/'unavailable.m3u').read_text())),0)
    def test_freeze(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td); (p/'config.json').write_text(json.dumps(self.cfg)); a=entry('KanEducational.il@SD'); b=entry('Kan11.il@SD'); text=m.playlist([a,b]); (p/'israel.m3u').write_text(text); (p/'unavailable.m3u').write_text('#EXTM3U\n')
            with patch.object(m,'ROOT',p),patch.object(m,'sources',return_value=([],[],[],{})),patch.object(m,'retry',return_value='HTTP 403'):
                m.main()
            self.assertEqual((p/'israel.m3u').read_text(),text); self.assertIn('Mass failure freeze: True',(p/'report.md').read_text())
if __name__=='__main__': unittest.main()
