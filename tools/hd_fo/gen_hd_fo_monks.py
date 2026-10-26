# -*- coding: utf-8 -*-
"""佛教东传（hd_fo）高僧生成器。2026-10-25。

数据来自 docs/佛教东传_高僧属性表.md（boki 已审）。输出：
  common/scripted_effects/zz_hd_fo_monks_generated_effects.txt   每人一个 hd_fo_make_<id>_effect = { AGE = n }
  localization/simp_chinese/zz_hd_fo_monks_l_simp_chinese.yml   人名
  localization/english/zz_hd_fo_monks_l_english.yml             人名

人物不写进 history：开局摆放和出场事件都在运行时生成（未来日期的 history 人物引擎不生成）。
ID 只用作全局指针 hd_fo_p_<id> 和本地化键。改数据后重跑：python -I tools/hd_fo/gen_hd_fo_monks.py
"""
import os

MOD = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# id, 中文名, 英文名, 文化, (外, 军, 管, 谋, 学, 武), 教育档, 性格×3, 其他特质, 出场年龄
MONKS = [
    # 东汉
    ('she_mo_teng', '摄摩腾', 'Kasyapa Matanga', 'hindustani', (7, 1, 4, 3, 12, 3), 3, ('brave', 'patient', 'calm'), (), 52),
    ('zhu_fa_lan', '竺法兰', 'Zhu Falan', 'hindustani', (5, 0, 3, 2, 13, 2), 3, ('diligent', 'brave', 'humble'), (), 57),
    ('an_shi_gao', '安世高', 'An Shigao', 'persian', (9, 2, 8, 4, 16, 3), 4, ('humble', 'content', 'generous'), ('intellect_good_2', 'lifestyle_physician'), 30),
    ('zhi_lou_jia_chen', '支娄迦谶', 'Lokaksema', 'tocharian', (6, 1, 4, 3, 15, 2), 4, ('diligent', 'honest', 'temperate'), (), 27),
    ('zhu_fo_shuo', '竺佛朔', 'Zhu Foshuo', 'hindustani', (5, 1, 3, 2, 11, 2), 3, ('diligent', 'content', 'honest'), (), 42),
    ('an_xuan', '安玄', 'An Xuan', 'persian', (8, 4, 10, 4, 11, 4), 3, ('honest', 'calm', 'diligent'), (), 41),
    ('yan_fo_tiao', '严佛调', 'Yan Fotiao', 'xuzhou', (7, 1, 4, 3, 12, 2), 3, ('diligent', 'gregarious', 'humble'), ('intellect_good_1',), 31),
    ('zhi_yao', '支曜', 'Zhi Yao', 'tocharian', (5, 1, 3, 2, 11, 2), 3, ('diligent', 'calm', 'humble'), (), 40),
    ('kang_ju', '康巨', 'Kang Ju', 'kangju', (6, 1, 3, 2, 11, 2), 3, ('honest', 'zealous', 'diligent'), (), 42),
    ('kang_meng_xiang', '康孟详', 'Kang Mengxiang', 'kangju', (8, 1, 3, 3, 13, 2), 3, ('diligent', 'gregarious', 'calm'), (), 39),
    ('mou_zi', '牟子', 'Mouzi', 'jiaozhou', (10, 2, 6, 5, 13, 3), 3, ('content', 'honest', 'patient'), (), 30),
    # 三国、两晋、十六国
    ('zhi_qian', '支谦', 'Zhi Qian', 'tocharian', (9, 1, 5, 4, 16, 2), 4, ('diligent', 'humble', 'content'), ('intellect_good_2',), 27),
    ('wei_qi_nan', '维祇难', 'Vighna', 'hindustani', (5, 1, 3, 2, 12, 2), 3, ('zealous', 'diligent', 'humble'), (), 44),
    ('kang_seng_hui', '康僧会', 'Kang Senghui', 'kangju', (11, 1, 6, 5, 15, 3), 4, ('brave', 'patient', 'diligent'), (), 47),
    ('tan_ke_jia_luo', '昙柯迦罗', 'Dharmakala', 'hindustani', (5, 1, 6, 3, 13, 2), 3, ('just', 'diligent', 'honest'), ('intellect_good_1',), 50),
    ('kang_seng_kai', '康僧铠', 'Kang Sengkai', 'kangju', (5, 1, 3, 2, 12, 2), 3, ('diligent', 'calm', 'content'), (), 52),
    ('zhu_shi_xing', '朱士行', 'Zhu Shixing', 'yuzhou', (6, 2, 4, 3, 14, 4), 4, ('stubborn', 'brave', 'honest'), ('lifestyle_traveler',), 47),
    ('zhu_fa_hu', '竺法护', 'Dharmaraksa', 'tocharian', (8, 1, 5, 3, 16, 2), 5, ('diligent', 'generous', 'compassionate'), ('intellect_good_2', 'theologian', 'lifestyle_traveler'), 35),
    ('bo_yuan', '帛远', 'Bo Yuan', 'hd_henei', (8, 1, 3, 3, 13, 2), 3, ('stubborn', 'brave', 'honest'), ('intellect_good_1',), 40),
    ('fo_tu_cheng', '佛图澄', 'Fotudeng', 'kucha', (12, 6, 6, 10, 15, 3), 4, ('compassionate', 'calm', 'patient'), ('lifestyle_mystic',), 78),
    ('zhu_dao_qian', '竺道潜', 'Zhu Daoqian', 'xuzhou', (10, 1, 4, 3, 13, 2), 3, ('calm', 'content', 'gregarious'), ('beauty_good_1',), 18),
    ('dao_an', '道安', "Dao'an", 'jizhou', (9, 1, 12, 4, 18, 2), 5, ('diligent', 'just', 'temperate'), ('intellect_good_2', 'theologian', 'beauty_bad_1'), 23),
    ('zhi_dun', '支遁', 'Zhi Dun', 'yanzhou', (12, 1, 4, 4, 15, 2), 4, ('gregarious', 'eccentric', 'compassionate'), ('intellect_good_2',), 24),
    ('hui_yuan', '慧远', 'Huiyuan', 'bingzhou', (11, 1, 8, 4, 17, 2), 5, ('zealous', 'stubborn', 'temperate'), ('theologian', 'intellect_good_2'), 20),
    ('jiu_mo_luo_shi', '鸠摩罗什', 'Kumarajiva', 'kucha', (10, 1, 4, 4, 18, 2), 5, ('patient', 'diligent', 'humble'), ('intellect_good_3', 'theologian'), 7),
    ('seng_zhao', '僧肇', 'Sengzhao', 'han', (7, 1, 3, 3, 16, 2), 4, ('diligent', 'humble', 'calm'), ('intellect_good_2',), 16),
    ('fa_xian', '法显', 'Faxian', 'hd_hedong', (7, 2, 5, 3, 15, 5), 4, ('brave', 'stubborn', 'diligent'), ('lifestyle_traveler',), 20),
    ('dao_sheng', '道生', 'Daosheng', 'jizhou', (9, 1, 4, 3, 16, 2), 4, ('stubborn', 'brave', 'honest'), ('intellect_good_2', 'theologian'), 15),
    ('tan_wu_chen', '昙无谶', 'Dharmaksema', 'hindustani', (8, 1, 4, 8, 16, 3), 4, ('zealous', 'brave', 'stubborn'), ('lifestyle_mystic',), 27),
    # 南北朝、隋
    ('tan_yao', '昙曜', 'Tanyao', 'liangzhou', (7, 1, 12, 4, 13, 2), 3, ('zealous', 'diligent', 'brave'), (), 42),
    ('ba_tuo', '跋陀', 'Batuo', 'hindustani', (5, 1, 4, 2, 12, 5), 3, ('content', 'calm', 'patient'), (), 50),
    ('pu_ti_liu_zhi', '菩提流支', 'Bodhiruci', 'kashmiri', (6, 1, 4, 3, 16, 2), 4, ('diligent', 'stubborn', 'zealous'), (), 38),
    ('pu_ti_da_mo', '菩提达摩', 'Bodhidharma', 'hindustani', (6, 1, 2, 3, 15, 4), 4, ('patient', 'calm', 'stubborn'), ('lifestyle_mystic',), 80),
    ('hui_ke', '慧可', 'Huike', 'hd_han_state', (7, 1, 3, 3, 15, 6), 4, ('brave', 'zealous', 'patient'), (), 33),
    ('bao_zhi', '宝志', 'Baozhi', 'yangzhou', (10, 1, 2, 9, 12, 2), 3, ('eccentric', 'gregarious', 'compassionate'), ('lifestyle_mystic',), 47),
    ('seng_you', '僧祐', 'Sengyou', 'yangzhou', (7, 1, 10, 3, 15, 2), 4, ('diligent', 'just', 'temperate'), ('architect',), 14),
    ('tan_luan', '昙鸾', 'Tanluan', 'bingzhou', (6, 1, 4, 3, 15, 3), 4, ('diligent', 'zealous', 'humble'), ('lifestyle_physician',), 14),
    ('zhen_di', '真谛', 'Paramartha', 'hindustani', (7, 1, 3, 3, 17, 2), 5, ('diligent', 'patient', 'humble'), ('theologian', 'lifestyle_traveler'), 47),
    ('hui_si', '慧思', 'Huisi', 'yuzhou', (7, 1, 5, 3, 15, 3), 4, ('patient', 'brave', 'diligent'), ('theologian',), 15),
    ('zhi_yi', '智顗', 'Zhiyi', 'jingzhou', (10, 1, 9, 4, 18, 2), 5, ('diligent', 'calm', 'compassionate'), ('intellect_good_2', 'theologian'), 17),
    ('ji_zang', '吉藏', 'Jizang', 'persian', (9, 1, 6, 4, 16, 2), 4, ('gregarious', 'ambitious', 'diligent'), ('intellect_good_2', 'theologian'), 7),
    ('xin_xing', '信行', 'Xinxing', 'jizhou', (7, 1, 5, 3, 13, 2), 3, ('humble', 'zealous', 'compassionate'), (), 17),
    ('dao_xin', '道信', 'Daoxin', 'hd_henei', (7, 1, 10, 3, 14, 3), 4, ('patient', 'diligent', 'humble'), (), 12),
    ('du_shun', '杜顺', 'Dushun', 'han', (8, 1, 4, 3, 15, 3), 4, ('calm', 'compassionate', 'humble'), ('lifestyle_mystic',), 18),
    ('dao_xuan', '道宣', 'Daoxuan', 'yangzhou', (7, 1, 7, 3, 16, 2), 5, ('just', 'diligent', 'temperate'), ('theologian',), 15),
]

# 出场调度：id -> (出场年, 史实城市县头衔, 史实接纳者)。接纳者：tianzi = 汉天子（e_han 持有者）；
# char:<history id> = 指定人物；follow:<高僧 id> = 跟随该高僧所在宫廷的最高领主；None = 按第 13 项退路。
SPAWN = {
    'she_mo_teng': (67, 'c_luoyang', 'tianzi'), 'zhu_fa_lan': (67, 'c_luoyang', 'tianzi'),
    'an_shi_gao': (148, 'c_luoyang', 'tianzi'), 'zhi_lou_jia_chen': (167, 'c_luoyang', 'tianzi'),
    'zhu_fo_shuo': (172, 'c_luoyang', 'tianzi'), 'an_xuan': (181, 'c_luoyang', 'tianzi'),
    'yan_fo_tiao': (181, 'c_luoyang', 'tianzi'), 'zhi_yao': (185, 'c_luoyang', 'tianzi'),
    'kang_ju': (187, 'c_luoyang', 'tianzi'), 'kang_meng_xiang': (194, 'c_luoyang', 'tianzi'),
    'mou_zi': (195, 'c_uuii_p_6569', 'char:shi_xie'),
    'zhi_qian': (221, 'c_uuii_p_4990', 'char:sun_quan'), 'wei_qi_nan': (224, 'c_uuii_p_4990', 'char:sun_quan'),
    'kang_seng_hui': (247, 'c_uuii_p_4389', 'char:sun_quan'),
    'tan_ke_jia_luo': (250, 'c_luoyang', None), 'kang_seng_kai': (252, 'c_luoyang', None),
    'zhu_shi_xing': (250, 'c_luoyang', None), 'zhu_fa_hu': (266, 'c_uuii_p_867', None),
    'bo_yuan': (290, 'c_uuii_p_867', None), 'fo_tu_cheng': (310, 'c_luoyang', None),
    'zhu_dao_qian': (304, 'c_luoyang', None), 'dao_an': (335, 'c_uuii_p_1172', None),
    'zhi_dun': (338, 'c_uuii_p_6471', None), 'hui_yuan': (354, 'c_uuii_p_1172', 'follow:dao_an'),
    'jiu_mo_luo_shi': (351, 'c_uuii_p_2766', None), 'seng_zhao': (400, 'c_uuii_p_1564', 'follow:jiu_mo_luo_shi'),
    'fa_xian': (357, 'c_uuii_p_867', None), 'dao_sheng': (370, 'c_uuii_p_4389', None),
    'tan_wu_chen': (412, 'c_uuii_p_1564', None), 'tan_yao': (452, 'c_uuii_p_1265', None),
    'ba_tuo': (490, 'c_uuii_p_1265', None), 'pu_ti_liu_zhi': (508, 'c_luoyang', None),
    'pu_ti_da_mo': (520, 'c_uuii_p_6157', None), 'hui_ke': (520, 'c_luoyang', None),
    'bao_zhi': (465, 'c_uuii_p_4389', None), 'seng_you': (459, 'c_uuii_p_4389', None),
    'tan_luan': (490, 'c_uuii_p_1262', None), 'zhen_di': (546, 'c_uuii_p_6157', None),
    'hui_si': (530, 'c_uuii_p_1626', None), 'zhi_yi': (555, 'c_uuii_p_1813', None),
    'ji_zang': (556, 'c_uuii_p_4389', None), 'xin_xing': (557, 'c_uuii_p_1172', None),
    'dao_xin': (592, 'c_uuii_p_2066', None), 'du_shun': (575, 'c_uuii_p_867', None),
    'dao_xuan': (611, 'c_uuii_p_867', None),
}

# 开局摆放（docs/佛教东传_开局推导表.md）：开局日期 -> [(id, 当时所在县, 年龄, 史实接纳者)]
START = {
    '190.1.1': [('an_xuan', 'c_luoyang', 50, 'tianzi'), ('yan_fo_tiao', 'c_luoyang', 40, 'tianzi'),
                ('zhi_yao', 'c_luoyang', 45, 'tianzi'), ('kang_ju', 'c_luoyang', 45, 'tianzi')],
    '218.1.1': [('mou_zi', 'c_uuii_p_6569', 53, 'char:shi_xie')],
    '253.3.1': [('zhi_qian', 'c_uuii_p_4389', 59, None), ('kang_seng_hui', 'c_uuii_p_4389', 53, None),
                ('tan_ke_jia_luo', 'c_luoyang', 53, None), ('kang_seng_kai', 'c_luoyang', 53, None),
                ('zhu_shi_xing', 'c_luoyang', 50, None)],
    '263.9.20': [('kang_seng_hui', 'c_uuii_p_4389', 63, None), ('kang_seng_kai', 'c_luoyang', 63, None),
                 ('zhu_shi_xing', 'c_uuii_p_6152', 60, None)],
    '304.11.20': [('zhu_fa_hu', 'c_uuii_p_867', 73, None), ('bo_yuan', 'c_uuii_p_867', 54, None),
                  ('zhu_dao_qian', 'c_luoyang', 18, None)],
    '346.12.10': [('fo_tu_cheng', 'c_uuii_p_1172', 114, None), ('dao_an', 'c_uuii_p_1172', 34, None),
                  ('zhu_dao_qian', 'c_uuii_p_6471', 60, None), ('zhi_dun', 'c_uuii_p_6471', 32, None)],
    '370.2.13': [('zhu_dao_qian', 'c_uuii_p_6471', 84, None), ('dao_an', 'c_uuii_p_1788', 58, None),
                 ('hui_yuan', 'c_uuii_p_1788', 36, None), ('jiu_mo_luo_shi', 'c_uuii_p_2766', 26, None),
                 ('fa_xian', 'c_uuii_p_867', 33, None), ('dao_sheng', 'c_uuii_p_4389', 15, None)],
    '404.3.24': [('hui_yuan', 'c_uuii_p_6364', 70, None), ('jiu_mo_luo_shi', 'c_uuii_p_867', 60, None),
                 ('seng_zhao', 'c_uuii_p_867', 20, None), ('dao_sheng', 'c_uuii_p_6364', 49, None)],
    '531.7.1': [('pu_ti_liu_zhi', 'c_luoyang', 61, None), ('pu_ti_da_mo', 'c_uuii_p_776', 91, None),
                ('hui_ke', 'c_uuii_p_776', 44, None), ('tan_luan', 'c_uuii_p_1502', 55, None),
                ('hui_si', 'c_uuii_p_1626', 16, None)],
    '617.6.23': [('ji_zang', 'c_uuii_p_867', 68, None), ('dao_xin', 'c_uuii_p_6364', 37, None),
                 ('du_shun', 'c_uuii_p_867', 60, None), ('dao_xuan', 'c_uuii_p_867', 21, None)],
}

# 出场事件里的一句介绍（中、英）
BIO = {
    'she_mo_teng': ('中天竺沙门，善风仪，随汉使以白马驮经东来。', 'A monk of central India who came east with the Han envoys, sutras loaded on a white horse.'),
    'zhu_fa_lan': ('天竺学者之师，诵经论数万章，不顾学徒挽留，间行而来。', 'A teacher of Indian scholars who knew tens of thousands of verses and slipped away from his pupils to follow.'),
    'an_shi_gao': ('安息王子，让国于叔，出家东游，通医方异术、七曜五行。', 'A Parthian prince who yielded his throne to his uncle, versed in medicine, omens and the five phases.'),
    'zhi_lou_jia_chen': ('月氏沙门，操行纯深，以精勤著称，传大乘般若之学。', 'A Yuezhi monk of pure conduct and great diligence, bringing the Mahayana Perfection of Wisdom.'),
    'zhu_fo_shuo': ('天竺沙门，携《道行经》至洛，与支谶共译。', 'An Indian monk who carried the Daoxing Sutra to Luoyang and translated it with Lokaksema.'),
    'an_xuan': ('安息优婆塞，经商至洛，以功号骑都尉，性贞白而深沉。', 'A Parthian lay believer who came to trade, earned the title of Cavalry Commandant, upright and deep.'),
    'yan_fo_tiao': ('临淮人，少年颖悟，敏而好学，剃度为汉人沙门之始。', 'A man of Linhuai, quick and studious, the first Han to take the tonsure.'),
    'zhi_yao': ('月氏沙门，于洛阳译《成具光明定意经》。', 'A Yuezhi monk who translated the Chengju Guangming Sutra in Luoyang.'),
    'kang_ju': ('康居沙门，心存游化，译文言直理旨，不加润饰。', 'A Sogdian monk bent on wandering teaching, whose translations were plain and true.'),
    'kang_meng_xiang': ('康居沙门，译《中本起经》，文辞弘赡雅畅。', 'A Sogdian monk whose translation of the Zhongben Qi Sutra was rich and elegant.'),
    'mou_zi': ('苍梧学者，博通经传，兼研老子，避乱交趾，作《理惑论》答难。', 'A scholar of Cangwu, learned in the classics and Laozi, who wrote the Disposing of Error in Jiaozhi.'),
    'zhi_qian': ('月氏后裔，生于汉地，通六国语，博览经籍，人称「支郎眼中黄」。', 'Of Yuezhi descent but born in Han lands, he spoke six languages and read everything.'),
    'wei_qi_nan': ('天竺沙门，本事火神，见沙门神术而改宗，携《法句经》而来。', 'An Indian monk, once a fire worshipper, converted by a monk\'s wonders, bringing the Dharmapada.'),
    'kang_seng_hui': ('先世康居，父商于交趾，设像行道，誓求舍利以示吴主。', 'Of Sogdian stock, raised in Jiaozhi, he vowed to bring forth relics to convince the ruler of Wu.'),
    'tan_ke_jia_luo': ('中天竺沙门，幼而才悟，善四韦陀，欲立中土受戒之法。', 'A central Indian monk, gifted from youth, who sought to establish ordination in China.'),
    'kang_seng_kai': ('外国沙门，嘉平末至洛阳，传译《无量寿经》。', 'A foreign monk who reached Luoyang late in the Jiaping era and translated the Sutra of Infinite Life.'),
    'zhu_shi_xing': ('颍川人，坚正方直，劝阻不能移其志，誓往西域求经。', 'A man of Yingchuan, upright and unshakable, who vowed to seek scripture in the Western Regions.'),
    'zhu_fa_hu': ('世居敦煌的月氏人，通西域三十六国语，号「敦煌菩萨」。', 'A Yuezhi of Dunhuang who spoke thirty-six tongues, called the Bodhisattva of Dunhuang.'),
    'bo_yuan': ('河内人，聪敏，日诵八九千言，筑精舍于长安讲经。', 'A man of Henei, so quick he recited thousands of words a day, preaching from his hermitage in Chang\'an.'),
    'fo_tu_cheng': ('西域沙门，善诵神咒，能知吉凶，欲以道术化导胡主。', 'A monk of the Western Regions, a master of spells and omens, set on converting the barbarian lords.'),
    'zhu_dao_qian': ('琅琊王氏子弟，风姿堂堂，舍朱门而入空门。', 'A son of the Wang clan of Langya, of noble bearing, who left the vermilion gates for the gate of emptiness.'),
    'dao_an': ('常山人，形貌甚陋而过目成诵，志在整饬僧团。', 'A man of Changshan, ugly of face yet able to recite anything at a glance, bent on ordering the sangha.'),
    'zhi_dun': ('陈留人，精于清谈，注《逍遥游》，名士争与之交。', 'A man of Chenliu, master of pure conversation, whose commentary on Free Wandering the literati prized.'),
    'hui_yuan': ('雁门人，少为儒生，闻道安讲经而叹「儒道九流，皆糠秕耳」。', 'A Confucian youth of Yanmen who, hearing Dao\'an, called all other schools mere chaff.'),
    'jiu_mo_luo_shi': ('父天竺人，母龟兹王妹，七岁出家，日诵千偈。', 'Son of an Indian father and a Kuchean princess, a monk at seven who recited a thousand verses a day.'),
    'seng_zhao': ('京兆人，家贫以替人抄书为业，遍读经史，闻罗什在凉州而往从之。', 'A poor copyist of Jingzhao who read everything, and set off to follow Kumarajiva.'),
    'fa_xian': ('平阳人，年幼出家，慨律藏残缺，立志西行。', 'A man of Pingyang, a monk from childhood, grieved at the incomplete Vinaya and resolved to go west.'),
    'dao_sheng': ('钜鹿人，幼而颖悟，十五登座讲经。', 'A man of Julu, so precocious he lectured from the high seat at fifteen.'),
    'tan_wu_chen': ('中天竺沙门，号「大咒师」，携《大般涅槃经》前分而来。', 'A central Indian monk called the Great Spellmaster, carrying the first part of the Nirvana Sutra.'),
    'tan_yao': ('凉州沙门，灭佛之时坚守法服，誓待复兴。', 'A monk of Liangzhou who kept his robes through the persecution, waiting for the Dharma to return.'),
    'ba_tuo': ('天竺沙门，性爱幽栖，来游北土。', 'An Indian monk who loved secluded places and came wandering to the north.'),
    'pu_ti_liu_zhi': ('北天竺沙门，遍通三藏，志在弘法。', 'A monk of north India versed in all three baskets, devoted to spreading the Dharma.'),
    'pu_ti_da_mo': ('南天竺沙门，渡海至南越，传壁观禅法。', 'A monk of south India who crossed the sea to the far south, teaching wall-gazing meditation.'),
    'hui_ke': ('虎牢人，少为儒生，博览诗书，后弃俗出家。', 'A man of Hulao, once a Confucian scholar, who renounced the world.'),
    'bao_zhi': ('神异之僧，赤足锦袍，杖头挂剪刀与镜，言多预兆。', 'A wonder-working monk, barefoot in brocade, with scissors and a mirror hung from his staff.'),
    'seng_you': ('建业人，入定林寺，精于律学，擅造佛像。', 'A man of Jianye at Dinglin Temple, learned in monastic law and skilled in making images.'),
    'tan_luan': ('雁门人，少游五台，学四论。', 'A man of Yanmen who studied the Four Treatises in youth on Mount Wutai.'),
    'zhen_di': ('西天竺优禅尼人，携梵本二百四十夹渡海而来。', 'A man of Ujjain who crossed the sea with two hundred and forty bundles of Sanskrit texts.'),
    'hui_si': ('武津人，十五出家，专修禅定。', 'A man of Wujin, a monk at fifteen, devoted to meditation.'),
    'zhi_yi': ('荆州华容人，十八出家，聪慧过人。', 'A man of Huarong in Jingzhou, a monk at eighteen, brilliant beyond others.'),
    'ji_zang': ('安息后裔，生于金陵，貌象西梵而言实东华。', 'Of Parthian descent, born in Jinling, Indian in looks but Chinese in speech.'),
    'xin_xing': ('魏郡人，十七出家，以苦行著称。', 'A man of Weijun, a monk at seventeen, known for his austerities.'),
    'dao_xin': ('河内人，少年即从僧璨习禅。', 'A man of Henei who studied meditation with Sengcan as a boy.'),
    'du_shun': ('雍州万年人，十八出家，以神异治病著称。', 'A man of Wannian who became a monk at eighteen and was famed for healing wonders.'),
    'dao_xuan': ('吴兴人，十六落发，专精律部。', 'A man of Wuxing, tonsured at sixteen, devoted to the Vinaya.'),
}

OPPOSITES = [
    {'brave', 'craven'}, {'calm', 'wrathful'}, {'patient', 'impatient'}, {'humble', 'arrogant'},
    {'content', 'ambitious'}, {'generous', 'greedy'}, {'diligent', 'lazy'}, {'honest', 'deceitful'},
    {'temperate', 'gluttonous'}, {'gregarious', 'shy'}, {'zealous', 'cynical'}, {'just', 'arbitrary'},
    {'stubborn', 'fickle'}, {'stubborn', 'eccentric'}, {'eccentric', 'fickle'}, {'compassionate', 'callous'},
]


def preset(p, ind):
    """存 scope:hd_fo_receiver 的史实接纳者。"""
    if p is None:
        return ''
    if p == 'tianzi':
        return f'{ind}title:e_han.holder ?= {{ save_scope_as = hd_fo_receiver }}\n'
    kind, who = p.split(':')
    if kind == 'char':
        return f'{ind}character:{who} ?= {{ if = {{ limit = {{ is_alive = yes }} save_scope_as = hd_fo_receiver }} }}\n'
    if kind == 'follow':
        return (f'{ind}global_var:hd_fo_p_{who} ?= {{\n{ind}\tif = {{\n{ind}\t\tlimit = {{ is_alive = yes exists = court_owner }}\n'
                f'{ind}\t\tcourt_owner.top_liege = {{ save_scope_as = hd_fo_receiver }}\n{ind}\t}}\n{ind}}}\n')
    raise ValueError(p)


def check():
    ids = [m[0] for m in MONKS]
    assert len(ids) == len(set(ids)) == 45, len(ids)
    assert set(SPAWN) == set(ids) == set(BIO), set(ids) ^ set(SPAWN) ^ set(BIO)
    for lst in START.values():
        for e in lst:
            assert e[0] in ids, e
    for m in MONKS:
        p = set(m[6])
        assert len(p) == 3, m[0]
        for o in OPPOSITES:
            assert not o <= p, (m[0], o)


def write(rel, text):
    path = os.path.join(MOD, rel)
    with open(path, 'w', encoding='utf-8-sig', newline='\n') as f:
        f.write(text)
    print('wrote', rel)


def main():
    check()
    names = ('diplomacy', 'martial', 'stewardship', 'intrigue', 'learning', 'prowess')
    eff = ['# 自动生成：tools/hd_fo/gen_hd_fo_monks.py（数据见 docs/佛教东传_高僧属性表.md）。不要手改，改生成器后重跑。\n',
           '# 调用前须已存好 scope:hd_fo_receiver（雇主）。生成后存 scope:hd_fo_monk；成年才给教育，未成年打 hd_fo_edu_pending，成年后由 hd_fo_adult_edu_effect 补。\n\n']
    adult = []
    for (mid, zh, en, cul, attrs, edu, pers, others, sage) in MONKS:
        b = [f'# {zh}\nhd_fo_make_{mid}_effect = {{\n\tscope:hd_fo_receiver = {{\n\t\tcreate_character = {{\n',
             f'\t\t\tname = hd_fo_name_{mid}\n\t\t\tage = $AGE$\n\t\t\tgender = male\n\t\t\tdynasty = none\n',
             f'\t\t\tculture = culture:{cul}\n\t\t\tfaith = faith:mahayana_faith\n\t\t\trite = rite:mahayana\n\t\t\trandom_traits = no\n']
        for k, v in zip(names, attrs):
            b.append(f'\t\t\t{k} = {v}\n')
        for t in ('historical_character', 'devoted') + tuple(pers) + tuple(others):
            b.append(f'\t\t\ttrait = {t}\n')
        b.append('\t\t\temployer = this\n\t\t\tsave_scope_as = hd_fo_monk\n\t\t}\n\t}\n')
        b.append(f'\tscope:hd_fo_monk ?= {{\n\t\tadd_character_flag = hd_fo_id_{mid}\n\t\tif = {{\n\t\t\tlimit = {{ is_adult = yes }}\n\t\t\tadd_trait = education_learning_{edu}\n\t\t}}\n'
                 f'\t\telse = {{ add_character_flag = hd_fo_edu_pending }}\n\t}}\n}}\n\n')
        eff.append(''.join(b))
        if sage < 16:
            adult.append((mid, zh, edu))
    eff.append('# 出场或开局时未成年的高僧：成年后补学识教育（年度脉冲调用）。\nhd_fo_adult_edu_effect = {\n')
    for mid, zh, edu in adult:
        eff.append(f'\tglobal_var:hd_fo_p_{mid} ?= {{ # {zh}\n\t\tif = {{\n\t\t\tlimit = {{ is_alive = yes is_adult = yes has_character_flag = hd_fo_edu_pending }}\n'
                   f'\t\t\tremove_character_flag = hd_fo_edu_pending\n\t\t\tadd_trait = education_learning_{edu}\n\t\t}}\n\t}}\n')
    eff.append('}\n\n')

    # 出场调度：开局年早于出场年才由此出场；出场年与开局同年或更早的由开局摆放处理（第 39 项）。
    eff.append('# 出场调度（年度脉冲调用）：到出场年、开局早于出场年、还没出场的，按史实城市和接纳者出场。\nhd_fo_dispatch_spawns_effect = {\n')
    by_year = sorted(MONKS, key=lambda m: SPAWN[m[0]][0])
    for m in by_year:
        mid, zh, sage = m[0], m[1], m[8]
        y, place, p = SPAWN[mid]
        eff.append(f'\tif = {{ # {zh}\n\t\tlimit = {{\n\t\t\tcurrent_year >= {y}\n\t\t\tgame_start_date < {y}.1.1\n'
                   f'\t\t\tNOT = {{ has_global_variable = hd_fo_s_{mid} }}\n\t\t}}\n')
        eff.append(preset(p, '\t\t'))
        eff.append(f'\t\thd_fo_spawn_monk_effect = {{ ID = {mid} PLACE = {place} AGE = {sage} }}\n\t}}\n')
    eff.append('}\n\n')

    eff.append('# 开局摆放（docs/佛教东传_开局推导表.md，开局即在的高僧）。\nhd_fo_startup_monks_effect = {\n')
    for date, lst in START.items():
        eff.append(f'\tif = {{\n\t\tlimit = {{ game_start_date = {date} }}\n')
        for mid, place, age, p in lst:
            zh = next(m[1] for m in MONKS if m[0] == mid)
            eff.append(f'\t\t# {zh}\n')
            eff.append(preset(p, '\t\t'))
            eff.append(f'\t\thd_fo_place_monk_effect = {{ ID = {mid} PLACE = {place} AGE = {age} }}\n')
        eff.append('\t}\n')
    eff.append('}\n')
    write('common/scripted_effects/zz_hd_fo_monks_generated_effects.txt', ''.join(eff))

    cl = ['# 自动生成：tools/hd_fo/gen_hd_fo_monks.py。出场事件里的高僧介绍：[hd_fo_monk.Custom(\'HdFoBio\')]\n',
          'HdFoBio = {\n\ttype = character\n']
    for m in MONKS:
        cl.append(f'\ttext = {{ trigger = {{ has_character_flag = hd_fo_id_{m[0]} }} localization_key = hd_fo_bio_{m[0]} }}\n')
    cl.append('\ttext = { localization_key = hd_fo_bio_unknown }\n}\n')
    write('common/customizable_localization/zz_hd_fo_custom_loc.txt', ''.join(cl))

    zh = ['l_simp_chinese:\n # 自动生成：tools/hd_fo/gen_hd_fo_monks.py。佛教东传高僧人名（无家族，写全称）。\n']
    en = ['l_english:\n # Generated by tools/hd_fo/gen_hd_fo_monks.py. Buddhist transmission (hd_fo): monk names.\n']
    for m in MONKS:
        zh.append(f' hd_fo_name_{m[0]}:0 "{m[1]}"\n')
        en.append(f' hd_fo_name_{m[0]}:0 "{m[2]}"\n')
    for m in MONKS:
        z, e = BIO[m[0]]
        zh.append(f' hd_fo_bio_{m[0]}:0 "{z}"\n')
        en.append(f' hd_fo_bio_{m[0]}:0 "{e}"\n')
    zh.append(' hd_fo_bio_unknown:0 "一位远道而来的僧人。"\n')
    en.append(' hd_fo_bio_unknown:0 "A monk who has come from afar."\n')
    write('localization/simp_chinese/zz_hd_fo_monks_l_simp_chinese.yml', ''.join(zh))
    write('localization/english/zz_hd_fo_monks_l_english.yml', ''.join(en))


if __name__ == '__main__':
    main()
