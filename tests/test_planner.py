import copy
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hd184_apply as hd

def enc(s):return s.encode('utf-8-sig')

def fixture(duke='hd_fictional_duke', people=True):
    land='''h_china={ k_test={ capital=c_seat d_longxi={ capital=c_seat c_seat={ b_seat={ province=1 } } c_extra={ b_extra={ province=2 } } c_protected={ b_protected={ province=3 } } } d_other={ capital=c_other c_other={ b_other={ province=4 } } } } }'''
    hist=f'''h_china={{184.1.1={{ holder=emperor }} }}
k_test={{184.1.1={{holder=king liege=h_china}}}}
d_longxi={{180.1.1={{ holder=historical_past }}184.1.1={{holder={duke} liege=k_test government=celestial_government}} 190.1.1={{holder=historical_future}}}}
c_seat={{184.1.1={{ holder={duke} liege=d_longxi }} }}
c_extra={{184.1.1={{ holder=hd_fictional_count liege=d_longxi }} }}
c_protected={{184.1.1={{holder=protected_count liege=d_longxi}}}}
d_other={{184.1.1={{holder=other_duke liege=k_test}}}}
c_other={{184.1.1={{holder=other_duke liege=d_other}}}}'''
    chars=''
    names={'emperor':'皇帝','king':'国王','protected_count':'旧县令','other_duke':'他郡守','historical_past':'前任','historical_future':'后任','li_xiang_ru':'李相如','li_can':'李参','historical_duke':'原历史太守'}
    for cid,name in names.items():
        if not people and cid in ('li_xiang_ru','li_can'):continue
        chars+=f'\n# 【{name}】\n{cid}={{name="name_{cid}" dynasty_house=h_{cid} culture=han faith=jingxue 140.1.1={{birth=yes}}}}\n'
    houses='\n'.join(f'h_{cid}={{name="dyn_{cid}" dynasty=d_{cid}}}' for cid in names)
    dyn='\n'.join(f'd_{cid}={{name="dyn_{cid}"}}' for cid in names)
    loc='l_simp_chinese:\n d_longxi:0 "陇西"\n d_other:0 "他郡"\n c_seat:0 "襄武"\n c_extra:0 "狄道"\n c_protected:0 "受保护县"\n c_other:0 "他县"\n'
    for cid,name in names.items():loc+=f' name_{cid}:0 "{name[1:]}"\n dyn_{cid}:0 "{name[0]}"\n'
    files={'common/landed_titles/geo.txt':enc(land),'history/titles/start.txt':enc(hist),'history/characters/people.txt':enc(chars),'common/dynasty_houses/houses.txt':enc(houses),'common/dynasties/dyn.txt':enc(dyn),'localization/simp_chinese/test_l_simp_chinese.yml':enc(loc)}
    manifest={'date':'184.1.1','sources':{},'offices':{'longxi':{'name':'陇西太守','kind':'territory','tier':'d','keys':['d_longxi'],'labels':['陇西']}},'persons':{'李相如':{'name':'李相如','slug':'li_xiang_ru','id_candidates':['li_xiang_ru'],'name_aliases':['李相如'],'birth':'140.1.1','family':None,'sources':[]},'李参':{'name':'李参','slug':'li_can','id_candidates':['li_can'],'name_aliases':['李参'],'birth':'140.1.1','family':None,'sources':[]}},'families':{},'ancestors':{},'rows':[{'row':31,'office':'陇西太守','office_id':'longxi','person':'李相如','order':0},{'row':32,'office':'陇西太守','office_id':'longxi','person':'李参','order':1}]}
    return files,manifest

def run(files,manifest,overrides=None):
    p=hd.Planner(hd.Snapshot(files),manifest,overrides or {})
    result=p.run()
    merged=dict(files);merged.update(result.files)
    return result,hd.Snapshot(merged)

class Assignment(unittest.TestCase):
    def test_primary_gets_duchy_and_secondary_is_direct_count_vassal(self):
        f,m=fixture();r,s=run(f,m)
        self.assertEqual(s.state('d_longxi').values['holder'],'li_xiang_ru')
        self.assertEqual(s.state('c_seat').values['holder'],'li_xiang_ru')
        self.assertEqual(s.state('c_extra').values['holder'],'li_can')
        self.assertEqual(s.state('c_extra').values['liege'],'d_longxi')
        self.assertEqual(s.state('c_protected').values['holder'],'protected_count')
    def test_historical_duke_is_kept_and_first_gets_county(self):
        f,m=fixture('historical_duke');r,s=run(f,m)
        self.assertEqual(s.state('d_longxi').values['holder'],'historical_duke')
        self.assertEqual(s.state('c_seat').values['holder'],'historical_duke')
        self.assertEqual(s.state('c_extra').values['holder'],'li_xiang_ru')
        self.assertTrue(any(x['status']=='blocked' and x.get('person')=='李参' for x in r.rows))
    def test_empty_title_not_filled(self):
        f,m=fixture('0');r,s=run(f,m)
        self.assertEqual(s.state('d_longxi').values['holder'],'0')
        self.assertNotIn('history/titles/start.txt',r.files)
    def test_past_future_and_protected_title_are_byte_equivalent(self):
        f,m=fixture();r,s=run(f,m)
        old=hd.Snapshot(f)
        for t in ('c_protected','k_test','h_china','d_other','c_other'):
            self.assertEqual(old.titles[t][0].source(),s.titles[t][0].source(),t)
        self.assertIn('180.1.1={ holder=historical_past }',s.docs['history/titles/start.txt'].text)
        self.assertIn('190.1.1={holder=historical_future}',s.docs['history/titles/start.txt'].text)
        self.assertNotIn('history/characters/people.txt',r.files)
    def test_never_steals_other_dukes_last_county(self):
        f,m=fixture('historical_duke')
        text=f['history/titles/start.txt'].decode('utf-8-sig').replace('holder=hd_fictional_count','holder=hd_fictional_other').replace('holder=other_duke','holder=hd_fictional_other')
        # Keep only one county of that duke, namely the county being requested.
        text=text.replace('c_other={184.1.1={holder=hd_fictional_other','c_other={184.1.1={holder=protected_count')
        f['history/titles/start.txt']=enc(text)
        r,s=run(f,m)
        self.assertEqual(s.state('c_extra').values['holder'],'hd_fictional_other')
    def test_missing_people_get_distinct_new_ids_houses_and_dynasties(self):
        f,m=fixture(people=False);r,s=run(f,m)
        primary=s.state('d_longxi').values['holder'];second=s.state('c_extra').values['holder']
        self.assertNotEqual(primary,second)
        self.assertTrue(primary.startswith('hd184_char_'))
        self.assertIn(primary,s.people);self.assertIn(second,s.people)
        self.assertIn(s.people[primary].house,s.houses)
        self.assertIn(s.people[primary].dynasty,s.dynasties)
    def test_same_name_chronology_conflict_is_not_duplicated_or_resurrected(self):
        f,m=fixture();f['history/characters/people.txt']=enc(f['history/characters/people.txt'].decode('utf-8-sig').replace('li_xiang_ru={','li_xiang_ru={175.1.1={death=yes} '))
        r,s=run(f,m)
        self.assertEqual(s.state('d_longxi').values['holder'],'hd_fictional_duke')
        self.assertNotIn('hd184_char_li_xiang_ru',s.people)
        self.assertEqual(s.people['li_xiang_ru'].death,(175,1,1))
    def test_same_name_two_viable_characters_is_blocked(self):
        f,m=fixture();f['history/characters/dup.txt']=enc('# 【李相如】\nother_li={name=x 130.1.1={birth=yes}}')
        r,s=run(f,m)
        self.assertEqual(s.state('d_longxi').values['holder'],'hd_fictional_duke')
    def test_id_hint_never_confuses_chen_yi_with_chen_yi(self):
        f,m=fixture();m['persons']['李相如']['name']='陈逸';m['persons']['李相如']['name_aliases']=['陈逸'];m['persons']['李相如']['id_candidates']=['chen_yi'];m['persons']['李相如']['slug']='chen_yi_lu';m['persons']['陈逸']=m['persons'].pop('李相如');m['rows'][0]['person']='陈逸'
        f['history/characters/chen.txt']=enc('# 【陈懿】\nchen_yi={name="Yi" 140.1.1={birth=yes}}')
        r,s=run(f,m)
        self.assertNotEqual(s.state('d_longxi').values['holder'],'chen_yi')
    def test_junior_with_equal_rank_is_not_made_vassal(self):
        f,m=fixture('historical_duke');f['history/titles/start.txt']=enc(f['history/titles/start.txt'].decode('utf-8-sig').replace('holder=other_duke','holder=li_xiang_ru'))
        r,s=run(f,m)
        self.assertEqual(s.state('c_extra').values['holder'],'li_can')
        self.assertTrue(any(x['status']=='blocked' and x.get('person')=='李相如' for x in r.rows))
    def test_source_conflict_row_never_gets_allocation(self):
        f,m=fixture();m['rows'][1]['defer']='source conflict'
        r,s=run(f,m)
        self.assertEqual(s.state('c_extra').values['holder'],'hd_fictional_count')
    def test_second_run_is_idempotent(self):
        f,m=fixture(people=False);r,s=run(f,m)
        f.update(r.files);r2,s2=run(f,m)
        self.assertEqual(r2.files,{})
    def test_repeated_office_rows_use_global_not_adjacent_order(self):
        f,m=fixture();m['rows'].insert(1,{'row':40,'office':'注释','office_id':'irrelevant','person':None})
        r,s=run(f,m)
        self.assertEqual(s.state('d_longxi').values['holder'],'li_xiang_ru')
        self.assertEqual(s.state('c_extra').values['holder'],'li_can')
    def test_duplicate_history_current_holders_conflict_is_quarantined(self):
        f,m=fixture();f['history/titles/other.txt']=enc('d_longxi={184.1.1={holder=protected_count}}')
        r,s=run(f,m)
        self.assertNotIn('history/titles/start.txt',r.files)
    def test_same_date_duplicate_equal_values_are_rewritten_together(self):
        f,m=fixture();f['history/titles/other.txt']=enc('d_longxi={184.1.1={holder=hd_fictional_duke}}')
        r,s=run(f,m)
        self.assertEqual(s.state('d_longxi').values['holder'],'li_xiang_ru')
        self.assertNotIn('holder',s.state('d_longxi').ambiguous)
    def test_initial_history_before_184_is_not_rewritten(self):
        f,m=fixture();f['history/titles/start.txt']=enc(f['history/titles/start.txt'].decode('utf-8-sig').replace('184.1.1={holder=hd_fictional_duke','183.1.1={holder=hd_fictional_duke'))
        r,s=run(f,m)
        self.assertEqual(s.state('d_longxi').values['holder'],'li_xiang_ru')
        self.assertIn('183.1.1={holder=hd_fictional_duke',s.docs['history/titles/start.txt'].text)

class Families(unittest.TestCase):
    def add_family(self,f,m,existing=False):
        m['persons']['李相如']['family']='陇西李氏'
        m['families']['陇西李氏']={'name':'陇西李氏','slug':'longxi_li','labels':['陇西李氏'],'origin':{'tier':'d','keys':['d_longxi'],'labels':['陇西'],'kind':'territory'},'county_labels':['襄武']}
        if existing:
            f['common/landed_titles/family.txt']=enc('c_old_family={landless=yes noble_family=yes capital=c_seat}')
            f['history/titles/family.txt']=enc('c_old_family={184.1.1={holder=historical_duke liege=h_china government=celestial_government}}')
            f['localization/simp_chinese/family_l_simp_chinese.yml']=enc('l_simp_chinese:\n c_old_family:0 "陇西李氏"\n')
        return f,m
    def test_existing_family_historical_head_preserved_no_duplicate(self):
        f,m=self.add_family(*fixture(),existing=True);r,s=run(f,m)
        self.assertEqual(s.state('c_old_family').values['holder'],'historical_duke')
        self.assertEqual([t for t in s.landed if s.is_family(t)],['c_old_family'])
    def test_missing_family_title_is_landless_and_has_local_capital(self):
        f,m=self.add_family(*fixture());r,s=run(f,m)
        families=[t for t in s.landed if s.is_family(t)]
        self.assertEqual(len(families),1)
        self.assertTrue(s.is_landless(families[0]))
        self.assertEqual(s.capital(families[0]),'c_seat')
        self.assertEqual(s.state(families[0]).values['holder'],'li_xiang_ru')
        self.assertNotIn('common/landed_titles/geo.txt',r.files)
    def test_origin_without_unique_geography_does_not_invent_location(self):
        f,m=self.add_family(*fixture());m['families']['陇西李氏']['origin']['keys']=[];m['families']['陇西李氏']['origin']['labels']=['不存在的地方']
        r,s=run(f,m)
        self.assertFalse(any(s.is_family(t) for t in s.landed))
    def test_existing_fictional_family_head_replaced_without_new_title(self):
        f,m=self.add_family(*fixture(),existing=True)
        f['history/titles/family.txt']=enc('c_old_family={184.1.1={holder=hd_fictional_family liege=h_china government=celestial_government}}')
        f['history/characters/fake_family.txt']=enc('hd_fictional_family={name=x dynasty_house=h_li_xiang_ru 140.1.1={birth=yes}}')
        r,s=run(f,m)
        self.assertEqual(s.state('c_old_family').values['holder'],'li_xiang_ru')
        self.assertEqual(s.state('c_old_family').values['liege'],'k_test')
        self.assertEqual([t for t in s.landed if s.is_family(t)],['c_old_family'])
        self.assertEqual(r.families[0]['status'],'fictional_replaced')
    def test_fictional_family_head_different_existing_house_not_rehoused(self):
        f,m=self.add_family(*fixture(),existing=True)
        f['history/titles/family.txt']=enc('c_old_family={184.1.1={holder=hd_fictional_family liege=h_china}}')
        f['history/characters/fake_family.txt']=enc('hd_fictional_family={name=x dynasty_house=h_historical_duke 140.1.1={birth=yes}}')
        r,s=run(f,m)
        self.assertEqual(s.state('c_old_family').values['holder'],'hd_fictional_family')
        self.assertEqual(s.people['li_xiang_ru'].house,'h_li_xiang_ru')
        self.assertEqual(r.families[0]['status'],'existing_family_mismatch')
    def test_future_family_is_not_activated_without_fictional_head(self):
        f,m=self.add_family(*fixture(),existing=True)
        f['history/titles/family.txt']=enc('c_old_family={346.1.1={holder=historical_duke liege=h_china}}')
        r,s=run(f,m)
        self.assertNotIn('holder',s.state('c_old_family').values)
        self.assertEqual([t for t in s.landed if s.is_family(t)],['c_old_family'])
    def test_pending_family_note_is_not_a_title(self):
        f,m=fixture();m['rows'][0]['family_raw']='与南阳来氏关系不明,待考'
        r,s=run(f,m)
        self.assertFalse(any(s.is_family(t) for t in s.landed))

if __name__=='__main__':unittest.main()
