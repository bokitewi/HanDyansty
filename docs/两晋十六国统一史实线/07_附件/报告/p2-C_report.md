## p2-C 新建人物与王朝：任务报告

暂存任务名 `p2-C`，4 个新文件已登记（stage new），都是 UTF-8 带 BOM、LF。没有改任何现有 mod 文件，所以和别的会话的未提交改动不冲突。

**结论：** 新建史实人物 122 人、新王朝 25 个；库中已有而改用库 ID 的 2 人（另有 10 人在设计里已定为引用库 ID）。没跑 gen_hbirth、popclean、hd_fo 和纹章生成器，没开游戏，没提交。

**闸门：** `gate.py --overlay p2-C --compare baseline.json --only-changed` 结果 error 0、warn 0、counts 为空，输出在 `D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p2-C_gate.txt`。

### 一、做了什么

1. **建前查库。** 先重建了人物索引（49,422 个 ID，UTF-8/GBK 双解码），再对全部人选按以下方式检索：
   - 简繁全名，在人物注释和中文 killer/mother 字符串里查（raw 行检索，GBK 原始字节）；
   - 名字键：本地化值等于名、十六进制序列匹配，并按同姓王朝过滤；
   - 拼音 ID 与英文注释（OE 的「Zhang Bin」式写法）；
   - 女性另按封号补查（贵嫔、贵人、明德、太后、东海王妃等）。
   
   命中两人：
   - #58 刘太后（石虎后）= `xiongnu_liu_047`：01_shiliuguozhu.txt:3913 注「刘皇后 安定公主」，石虎 338 年 add_spouse、石世的 mother 都已指向她。
   - #50 司马越妃裴氏 = `hedong_pei_037`：00_sili.txt:1503 注「东海王妃」，293 年已 add_spouse = hd_304_si_ma_yue。
   
   这两人都没建。其余各条都是假阳性：同名不同人（冯该/feng_gai、蒋干/jiang_gan、韩范/han_fan、刘显/henan_dugu_002、刘允/OE 刘宋宗室等），或者只是注释、中文 killer 字符串。另外：
   - 在 common、events、tools 里查过 create_character 和中文全名，这批人都不是运行时生成的。
   - gen_hbirth 的「同人异 ID」去重只读 `docs/人物审查/同一人物多ID.csv`，新 ID 不在表里，不会被误并。

2. **人物文件** `history/characters/zz_hd_j16_characters.txt`：按 15 个政权分组，每人上方一行中文注释（名、生卒、用途、出处、注、来源表行）。写法：
   - name 一律用名字键；挂王朝或家族；culture、`rite =` 照 05/06 表；
   - 父母、配偶只引用存在的 ID；
   - 都加 `trait = historical_character`，教育、性格照 05 表，06 的人自拟；能力未给的项按 ID 哈希取 5–8；
   - 「约」年份写成 x.1.1；死亡块的 killer 都是存在的 ID。
   
   生成脚本自检全部通过：父母与子女年龄差 ≥13 且性别正确，婚期双方都满 16 岁且在世，凶手在卒日在世，对立特质、性格超过 3 个的情况都没有。

3. **王朝文件** `common/dynasties/zz_hd_j16_dynasties.txt`：25 个王朝，写法照 hd_nbc_ran_dyn（name 键加 culture），显示名只写姓。

4. **名字键：**
   - 中文 yml：新名字键 18 个、王朝名键 25 个；
   - 英文 yml：同样 43 个键，另补 0 个缺英文的旧键；
   - 另有 85 个名字键直接复用库中值相同的现成键（含原版用繁体编码的键）。已核实复用键的来源文件没有被 mod 同名文件遮蔽，中英文两侧都在。

### 二、附表（122 人）

列：中文名｜ID｜生卒｜王朝/家族｜父母｜用途｜可见范围（304/346/370/404）。

公师藩｜hd_j16_gongshi_fan｜约260–306.9｜hd_j16_gongshi（新）｜—｜B3 为成都王颖起兵｜原生/已死/已死/已死
汲桑｜hd_j16_ji_sang｜约265–307.12｜baijia213（汲）｜—｜B3、B9；00_yanzhou:517 killer｜原生/已死×3
田甄｜hd_j16_tian_zhen｜约265–约315｜tian_7530_1｜—｜B9 乞活帅、杀汲桑｜原生/已死×3
李恽｜hd_j16_li_yun｜约265–约310｜li_674E_1｜—｜B9 乞活、决议E｜原生/已死×3
祁弘｜hd_j16_qi_hong｜约265–约308｜qi_7941_1｜—｜B2｜原生/已死×3
何伦｜hd_j16_he_lun｜约265–约312｜he_4F55_1｜—｜B10–B12｜原生/已死×3
缪播｜hd_j16_miu_bo｜约260–309.3｜hd_j16_lanling_miu（新）｜—｜B10｜原生/已死×3
缪胤｜hd_j16_miu_yin｜约265–309.3｜hd_j16_lanling_miu（新）｜—｜B10｜原生/已死×3
刘暾｜hd_j16_liu_tun｜约250–约311｜donglai_liu（家族）｜—｜晋廷朝官｜原生/已死×3
和峤｜hd_j16_he_qiao｜约235–292｜hd_j16_runan_he（新）｜—（妻 taiyuan_wang_041）｜家谱｜已死×4
和郁｜hd_j16_he_yu｜约250–约311｜hd_j16_runan_he（新）｜—｜晋廷朝官｜原生/已死×3
山简｜hd_j16_shan_jian｜253–312｜house_111010225001013｜shan_tao｜晋廷、镇襄阳｜原生/已死×3
裴邈｜hd_j16_pei_miao｜约265–约315｜hedong_pei｜—｜越僚属｜原生/已死×3
冯嵩｜hd_j16_feng_song｜约260–约315｜feng_99AE_1｜—｜B7｜原生/已死×3
梁臣｜hd_j16_liang_chen｜约265–约315｜liang_6881_1｜—｜B8 杀司马颙｜原生/已死×3
刘伯根｜hd_j16_liu_bogen｜约260–306.6｜liu_5289_1｜—｜B13｜原生/已死×3
箕澹｜hd_j16_ji_dan｜约270–约316｜xin322（箕）｜—｜Z5｜原生/已死×3
北宫纯｜hd_j16_beigong_chun｜约270–约317｜dyn_113020030001002（北宫）｜—｜B14｜原生/已死×3
麴允｜hd_j16_qu_yun｜约265–316.12｜hd_j16_jincheng_qu（新）｜—｜J1、J2｜原生/已死×3
阎鼎｜hd_j16_yan_ding｜约265–约313｜hd_j16_tianshui_yan（新）｜—｜J1｜原生/已死×3
梁综｜hd_j16_liang_zong｜约265–约312｜liang_6881_1｜—｜见偏差 3｜原生/已死×3
焦嵩｜hd_j16_jiao_song｜约265–约320｜jiao_7126_1｜—｜J1｜原生/已死×3
张春｜hd_j16_zhang_chun｜约275–约325｜zhang_5F35_1｜—｜司马保凶手（si_ma_bao_2 卒年行）｜原生/已死×3
陈安｜hd_j16_chen_an｜约280–323.7｜chen_9673_1｜—｜J4、H6｜原生/已死×3
赵染｜hd_j16_zhao_ran｜约270–约314｜zhao_8D99_1｜—｜司马模凶手｜原生/已死×3
呼延翼｜hd_j16_huyan_yi｜约236–309.11｜hd_j16_huyan（新）｜—｜刘渊岳父、S4｜原生/已死×3
呼延氏｜hd_j16_huyan_hou｜约253–约312｜hd_j16_huyan（新）｜huyan_yi（夫 xiongnu_liu_020）｜刘渊皇后｜原生/已死×3
呼延攸｜hd_j16_huyan_you｜约270–310.8｜hd_j16_huyan（新）｜huyan_yi｜H1｜原生/已死×3
呼延晏｜hd_j16_huyan_yan｜约265–约320｜hd_j16_huyan（新）｜—｜S4｜原生/已死×3
陈元达｜hd_j16_chen_yuanda｜约265–约316｜chen_9673_1｜—｜刘聪诤臣｜原生/已死×3
崔游｜hd_j16_cui_you｜约212–约305｜cui_5D14_1｜—｜刘渊之师｜原生/已死×3
靳准｜hd_j16_jin_zhun｜约265–318.12｜hd_j16_jin（新）｜—｜H2–H4｜原生/已死×3
靳康｜hd_j16_jin_kang｜约275–约319｜hd_j16_jin（新）｜—｜H4｜原生/已死×3
靳明｜hd_j16_jin_ming｜约275–约319｜hd_j16_jin（新）｜—｜H4｜原生/已死×3
刘殷｜hd_j16_liu_yin｜约240–约312｜hd_j16_xinxing_liu（新）｜—｜汉太保｜原生/已死×3
刘英｜hd_j16_liu_ying｜约292–约312｜hd_j16_xinxing_liu（新）｜liu_yin｜刘聪左贵嫔｜原生（未成年）/已死×3
刘娥｜hd_j16_liu_e｜约294–314.3｜hd_j16_xinxing_liu（新）｜liu_yin（夫 xiongnu_liu_023）｜刘聪皇后｜原生（未成年）/已死×3
张瑶｜hd_j16_zhang_yao｜约240–约300｜hd_j16_zhongqiu_zhang（新）｜—｜家谱｜已死×4
张宾｜hd_j16_zhang_bin｜约270–约322｜hd_j16_zhongqiu_zhang（新）｜zhang_yao｜E1-Z10、石勒卡｜原生/已死×3
张背督｜hd_j16_zhang_beidu｜约270–约320｜zhang_5F35_1｜—｜S2｜原生/已死×3
支雄｜hd_j16_zhi_xiong｜约275–约335｜zhi_652F_1｜—｜十八骑｜原生/已死×3
逯明｜hd_j16_lu_ming｜约275–约330｜hd_j16_lu_9006（新）｜—｜十八骑｜原生/已死×3
石堪｜hd_j16_shi_kan｜约290–333.10｜shangdang_shi｜—（养子）｜H7、Z11｜原生（未成年）/已死×3
石聪｜hd_j16_shi_cong｜约290–约335｜shangdang_shi｜—（养子）｜Z 段领兵｜原生（未成年）/已死×3
程遐｜hd_j16_cheng_xia｜约270–333.10｜cheng_7A0B_1｜—｜Z6、Z11｜原生/已死×3
程氏｜hd_j16_cheng_shi｜约290–约334｜cheng_7A0B_1｜—（夫 shangdang_shi_003）｜石弘之母｜原生（未成年）/已死×3
徐光｜hd_j16_xu_guang｜约275–333.10｜xu_5F90_1｜—｜Z11｜原生/已死×3
邵续｜hd_j16_shao_xu｜约260–约321｜shao_90B5_1｜—｜Z7｜原生/已死×3
曹嶷｜hd_j16_cao_yi｜约270–约323｜cao_66F9_1｜—｜卒年表｜原生/已死×3
麻秋｜hd_j16_ma_qiu｜约300–350.4｜hd_j16_ma（新）｜—｜E2-L90/91、E3-Q05｜原生（未成年）/原生/已死/已死
石宁｜hd_j16_shi_ning｜约310–约355｜shangdang_shi｜—｜E2-L91｜hb326/原生/已死/已死
张豺｜hd_j16_zhang_chai｜约290–349.6｜zhang_5F35_1｜—｜E3-Z10/Z20｜原生（未成年）/原生/已死/已死
杨杯｜hd_j16_yang_bei｜约310–348.9｜yang_694A_1｜—｜石韬凶手（见偏差 4）｜hb326/原生/已死/已死
李农｜hd_j16_li_nong｜约300–350.8｜li_674E_1｜—｜E3-Z20、R05、R10｜原生（未成年）/原生/已死/已死
孙伏都｜hd_j16_sun_fudu｜约310–350.1｜sun_5B6B_1｜—｜E3-R05｜hb326/原生/已死/已死
刘显｜hd_j16_liu_xian｜约310–约352｜liu_5289_1｜—｜E3-Z60｜hb326/原生/已死/已死
蒋干｜hd_j16_jiang_gan｜约310–约353｜jiang_8523_1｜—｜E3-M25｜hb326/原生/已死/已死
范长生｜hd_j16_fan_changsheng｜约220–约318｜hd_j16_fuling_fan（新）｜—｜E1-C10｜原生/已死×3
范贲｜hd_j16_fan_ben｜约280–约349｜hd_j16_fuling_fan（新）｜fan_changsheng｜347 称帝｜原生/原生/已死/已死
李氏｜hd_j16_li_shi_liuxuan｜约300–约350｜bacong_li｜—（夫 zhuojun_liu_010）｜刘玄妻【自拟】｜原生（未成年）/原生/已死/已死
阎沙｜hd_j16_yan_sha｜约280–约320｜yan_95BB_1｜—｜L2 杀张寔｜原生/已死×3
谢艾｜hd_j16_xie_ai｜约310–约354｜xie_8B1D_1｜—｜E2-L90–92、E3-L10｜hb326/原生/已死/已死
张弘｜hd_j16_zhang_hong｜约310–约360｜zhang_5F35_1｜—｜E3-L08｜hb326/原生/已死/已死
宋氏｜hd_j16_song_shi_zzh｜约328–约380｜dunhuang_song｜—（夫 zhang_zhong_hua）｜张重华妻【自拟】｜hb344/原生/原生/已死
钱凤｜hd_j16_qian_feng｜约280–324.8｜wuxing_qian_dyn｜—｜J6、J8｜原生/已死×3
戴渊｜hd_j16_dai_yuan｜约270–322.5｜hd_j16_guangling_dai（新）｜—｜J6｜原生/已死×3
戴邈｜hd_j16_dai_miao｜约275–约330｜hd_j16_guangling_dai（新）｜—｜广陵戴氏｜原生/已死×3
韩晃｜hd_j16_han_huang｜约290–约329｜han_97D3_1｜—｜J10｜原生（未成年）/已死×3
匡术｜hd_j16_kuang_shu｜约290–约335｜baijia353（匡）｜—｜J10｜原生（未成年）/已死×3
周玘｜hd_j16_zhou_qi｜258–313｜uuii_book_house_72ee81bb35cd｜zhou_chu｜三定江南｜原生/已死×3
甘卓｜hd_j16_gan_zhuo｜约265–322.6｜hd_j16_danyang_gan（新）｜—｜J6｜原生/已死×3
周虑｜hd_j16_zhou_lv｜约280–约340｜zhou_5468_1｜—｜甘卓凶手｜原生/已死×3
杜弢｜hd_j16_du_tao｜约265–约315｜du_675C_1｜—｜卒年表｜原生/已死×3
郭默｜hd_j16_guo_mo｜约270–约330｜guo_90ED_1｜—｜卒年表｜原生/已死×3
卢氏｜hd_j16_lu_shi_liuqun｜约305–约350｜fanyang_lu｜lu_chen_zi_zi_liang（夫 zhongshan_liu_006）｜刘群妻【自拟】｜hb321/原生/已死/已死
刘允｜hd_j16_liu_qun_zi｜约328–约385｜zhongshan_liu｜zhongshan_liu_006 / hd_j16_lu_shi_liuqun｜刘群继承人【自拟】｜hb344/原生/原生/已死
张贵人｜hd_j16_zhang_guiren｜约367–约397｜zhang_5F35_1｜—｜E5-J10｜hb383/hb383/原生（未成年）/已死
冯该｜hd_j16_feng_gai｜约350–约404｜feng_99AE_1｜—｜杀苻丕、桓玄部将｜hb366/hb366/原生/原生
阳骛｜hd_j16_yang_wu｜约300–约370｜hd_j16_youbeiping_yang（新）｜—｜E3-M10、M70｜原生（未成年）/原生/已死/已死
悦绾｜hd_j16_yue_wan｜约310–369.12｜hd_j16_yue（新）｜—｜E3-R20｜hb326/原生/已死/已死
可足浑氏｜hd_j16_kezuhun_shi｜约325–约370｜hd_j16_kezuhun（新）｜—（夫 changli_murong_018）｜E3-M70、M75｜hb341/原生/已死/已死
慕舆文｜hd_j16_muyu_wen｜约340–约390｜hd_j16_muyu（新）｜—｜杀刘库仁｜hb356/原生（未成年）/原生/已死
高盖｜hd_j16_gao_gai｜约330–约386｜gao_9AD8_1｜—｜杀慕容泓｜hb346/原生/原生/已死
韩延｜hd_j16_han_yan｜约340–约386｜han_97D3_1｜—｜杀慕容冲｜hb356/原生（未成年）/原生/已死
苟氏（苻坚母）｜hd_j16_gou_shi_mu｜约315–约375｜hd_j16_lueyang_gou（新）｜—（夫 lueyang_fu_004）｜E3-Q20｜hb331/原生/原生/已死
苟氏（苻坚后）｜hd_j16_gou_shi_hou｜约340–约385｜hd_j16_lueyang_gou（新）｜—（夫 lueyang_fu_020）｜E3-Q20｜hb356/原生（未成年）/原生/已死
苟苌｜hd_j16_gou_chang｜约320–约385｜hd_j16_lueyang_gou（新）｜—｜E4-Q30、Q40｜hb336/原生/原生/已死
苟池｜hd_j16_gou_chi｜约320–约380｜hd_j16_lueyang_gou（新）｜—｜E3-J60｜hb336/原生/原生/已死
薛赞｜hd_j16_xue_zan｜约320–约370｜xue_859B_1｜—｜E3-Q20｜hb336/原生/已死/已死
邓羌｜hd_j16_deng_qiang｜约320–约380｜hd_j16_anding_deng（新）｜—｜E3-Y40、Q40、E4｜hb336/原生/原生/已死
张蚝｜hd_j16_zhang_hao｜约330–约390｜zhang2_dyn｜—（养子）｜E3-Q30/Q40、E4-Q50/Q70｜hb346/原生/原生/已死
梁熙｜hd_j16_liang_xi｜约320–约386｜hd_j16_liang（新）｜—｜E4-Q30｜hb336/原生/原生/已死
梁成｜hd_j16_liang_cheng｜约330–383.12｜hd_j16_liang（新）｜—｜E4-Q50｜hb346/原生/原生/已死
朱肜｜hd_j16_zhu_rong｜约330–约385｜zhu_6731_1｜—｜E4-Q20｜hb346/原生/原生/已死
彭超｜hd_j16_peng_chao｜约330–约379｜peng_5F6D_1｜—｜E4-X10｜hb346/原生/原生/已死
俱难｜hd_j16_ju_nan｜约330–约385｜hd_j16_ju（新）｜—｜E4-X10｜hb346/原生/原生/已死
梁式王｜hd_j16_liang_shiwang｜约320–约355｜liang_6881_1｜—｜E3-X20｜hb336/原生/已死/已死
强氏｜hd_j16_qiang_shi_yangchu｜约310–约365｜hd_j16_qiang（新）｜—（夫 chouchi_yang_052）｜杨初妻【自拟】｜hb326/原生/已死/已死
祁氏（惟氏）｜hd_j16_wei_shi｜约270–约325｜qi_7941_1｜—（夫 tuoba_026）｜郁律凶手｜原生/已死×3
燕凤｜hd_j16_yan_feng｜约325–约395｜baijia315（燕）｜—｜E4-T10｜hb341/原生/原生/已死
许谦｜hd_j16_xu_qian｜约333–约396｜xu_8A31_1｜—｜E4-T30｜hb349/原生（未成年）/原生/已死
姜聪｜hd_j16_jiang_cong｜约290–约340｜jiang_59DC_1｜—｜吐延凶手｜原生（未成年）/已死×3
段速骨｜hd_j16_duan_sugu｜约360–398.8｜liaoxi_duan｜—｜E5-M35｜hb376/hb376/原生（未成年）/已死
丁氏（丁太后）｜hd_j16_ding_taihou｜约365–约402｜ding_4E01_1｜—｜E5-M50｜hb381/hb381/原生（未成年）/已死
慕容镇｜hd_j16_murong_zhen｜约350–约410｜changli_murong｜—｜E5-M55、J70｜hb366/hb366/原生/原生
韩范｜hd_j16_han_fan｜约360–约425｜han_97D3_1｜—｜E5-M55、J70｜hb376/hb376/原生（未成年）/原生
辟闾浑｜hd_j16_pilv_hun｜约340–约399｜hd_j16_pilv（新）｜—｜E5-M40｜hb356/原生（未成年）/原生/已死
离班｜hd_j16_li_ban｜约370–约409｜hd_j16_li_79bb（新）｜—｜E5-M65、高云凶手｜hb386/hb386/原生（未成年）/原生
桃仁｜hd_j16_tao_ren｜约370–约409｜fanyang_tao_dyn｜—｜E5-M65｜同上
尹纬｜hd_j16_yin_wei｜约340–约397｜yin_5C39_1｜—｜E4-Y30｜hb356/原生（未成年）/原生/已死
姚赞｜hd_j16_yao_zan｜约370–约417｜yao｜—｜E5-J80｜hb386/hb386/原生（未成年）/原生
姚恢｜hd_j16_yao_hui｜约390–约417｜yao｜—｜E5-J80｜hb406/hb406/hb406/原生（未成年）
杜进｜hd_j16_du_jin｜约330–约389｜du_675C_1｜—｜E4-X40｜hb346/原生/原生/已死
段业｜hd_j16_duan_ye｜约350–401.6｜duan_6BB5_1｜—｜北凉建立者｜hb366/hb366/原生/已死
王买德｜hd_j16_wang_maide｜约370–约430｜wang_738B_1｜—｜E5-X58｜hb386/hb386/原生（未成年）/原生
刘穆之｜hd_j16_liu_muzhi｜约360–417.12｜liu_5289_1｜—｜刘裕心腹｜hb376/hb376/原生（未成年）/原生
魏咏之｜hd_j16_wei_yongzhi｜约360–约410｜wei_9B4F_1｜—｜E5-J50｜同上
孙处｜hd_j16_sun_chu｜约360–约412｜sun_5B6B_1｜—｜E5-J73、徐道覆凶手｜同上
谯道福｜hd_j16_qiao_daofu｜约360–约413｜baxi_qiao｜—｜E5-J76｜同上
毛德祖｜hd_j16_mao_dezu｜约370–约424｜xingyang_mao｜—｜E5-J82｜hb386/hb386/原生（未成年）/原生
冯迁｜hd_j16_feng_qian｜约370–约425｜feng_99AE_1｜—｜桓玄凶手｜同上
丁旿｜hd_j16_ding_wu｜约370–约425｜ding_4E01_1｜—｜诸葛长民凶手｜同上

**库中已有、未建，节点和卒年表改用以下 ID：**
- 刘太后（拟 hd_j16_liu_shi_shihu）→ `xiongnu_liu_047`
- 司马越妃裴氏（拟 hd_j16_pei_fei）→ `hedong_pei_037`
- 设计里已定为引用库 ID 的 10 人：兰汗 changli_lan_han、吕超 lueyang_lv_015、乞伏公府 qifu_006、沈田子 1802134、段玑 liaoxi_duan_074、褚淡之 chu_dan_zhi、祖焕 fanyang_zu_huan、近肖古王 korean_buyeo_49、佛图澄 fo_tu_cheng（hd_fo 生成）、袁宏 yuan_hong

旧 ID 仍出现在文档的位置：
- 02_304左国称王.md:494（hd_j16_pei_fei）
- 03_346戡定岷峨.md:384、:468（hd_j16_liu_shi_shihu）
- 05_人物与卒年.md:138、:146、:534

2-D 和第 3、4 期引用时要改指新 ID。

### 三、自拟项与偏差

1. **未建家族文件。** 任务第 2 步列了 `common/dynasty_houses/zz_hd_j16_houses.txt`，没有建也没有暂存。新王朝的人直接挂王朝，有 hd_nbc_ran_dyn 先例；挂库中家族的写 dynasty_house。没有必须单独建家族的情况。
2. **新王朝名只写姓。** 例如 hd_j16_zhongqiu_zhang 显示「张」，不写「中丘张氏」；写全会显示成「中丘张氏宾」。郡望写在王朝注释里。
3. **阎鼎与梁综（交 2-D 改卒年行）。** 05 定梁综为阎鼎的凶手。但《晋书·阎鼎传》记阎鼎先杀梁综，后来为梁纬、麴允等所攻，出奔，被氐人窦首所杀【记忆·待核】。
   - history 里梁综卒于 312.10，凶手写阎鼎；阎鼎的 death_murder 不写 killer。
   - 按现状，05 那条 K 行永远不成立，会按 D15 顺延 10 年再转 N。2-D 须改成 murder、killer 留空，或者另定凶手。
4. **石韬的凶手（交 2-B、2-D 拍板）。** 05 §3 #3 写 `shangdang_shi_012`（石宣），05 文首写杨杯，两处冲突。杨杯已按文首建出。
5. **改过的生年：**
   - 呼延翼 245→236、呼延后 255→253：保证父女差 ≥13 岁，且呼延后在刘和 270 年出生时已满 13 岁。
   - 范长生 218→220：避开 218 开局当天出生。
6. **补了约数卒年的人：** 宋氏、强氏、刘允、张春、周虑、张弘、韩范、王买德、冯迁、丁旿、姜聪、戴邈、毛德祖（424）。05/06 原写「不进」或「不详」，补上是为了不让他们活进 531、617 开局。
7. **改名两处：**
   - 张㔨督改写「张背督」：㔨 是 U+3528，字体可能缺字。名字键 Beidu_80CC_7763。
   - 惟氏按《魏书》显示为「祁氏」，ID 仍用 hd_j16_wei_shi。库中 hd_rp_tuoba_003_mother 注「原引用桓帝皇后祁氏」，但她卒于 300、是拓跋弗之母的占位，不是本人。
8. **通用同姓王朝的取法：**
   - 优先原版 05_tgp 的 `<拼音>_<繁体编码>_1`（例如 zhang_5F35_1、liu_5289_1）；
   - 没有的，取 mod 00_baijia、uuii 的同姓通用王朝：汲 baijia213、箕 xin322、匡 baijia353、燕 baijia315、北宫 dyn_113020030001002（文化 qiang）；
   - 库中无同姓王朝的，新建：公师 hd_j16_gongshi、逯 hd_j16_lu_9006、俱 hd_j16_ju、悦 hd_j16_yue、离 hd_j16_li_79bb。
   - 05 示例用的是 mod 的 zhang2_dyn 一类；只有张蚝照 05 挂 zhang2_dyn。
9. **桃仁的王朝。** 06 写挂 `141210007000001_Tao`，那是名字键，库中没有这个王朝，改挂库中的桃姓王朝 fanyang_tao_dyn。
10. **配偶：**
   - 刘聪的信仰是一夫一妻加妾（doctrine_concubines），所以只有刘娥（皇后）写 add_spouse。刘英（左贵嫔）没写配偶，需要 2-B 在刘聪条目加 `312.2.1 = { add_concubine = hd_j16_liu_ying }`。
   - 张贵人同理，孝武帝条目可加 add_concubine，交 2-B 决定。
   - 丁太后的丈夫是慕容宝还是慕容盛待核，未写。
11. **张宾不写 employer。** 05 #1 写「石勒宫廷 employer」。但 304 开局时石勒还没有宫廷，归附由 E1-Z10 节点做；写在开局后的日期，哪个开局都不会生效。
12. **开局时未满 16 岁的人。** 出生块给童年特质，16 岁块 remove_trait；成年性格和教育写在顶层，因为 hbirth 只读顶层特质。
   - 开局时未成年的人同时带童年特质和成年特质，和 mod 现有先例一致。
   - 原版的童年机制会在成年时覆盖 history 写的教育。要角（370 局的刘穆之、404 局的姚恢、304 局的麻秋、张豺、李农）可作为 tools/hd_hbirth/gen_adult_attrs.py 的 IDS 候选，由汇总人决定。
13. **文化、信仰待核：**
   - 刘伯根 taipingdao、范长生和范贲 diren/zhengyi、段业 mahayana：照 05 的 ★。
   - 姜聪 qiang/dhyana：照库中羌人现值。
   - 06 写「照某某现值」的人，取同政权的值，各人注释里写了。
14. **其余：**
   - 06 的 19 人和补遗里 05 未给特质、能力的，都是自拟。
   - 名字键「伏都」手工指定拼音 Fudu（pypinyin 给的是 Fudou）。
   - 05 §1.1 原写名字键放进 zz_hd_history_name_keys，按 08 和本任务改放 zz_hd_j16_names。

### 四、需汇总人处理

1. **纹章：** 对 25 个新王朝跑 `tools/gen_dynasty_fixed_coas.py`。键为：hd_j16_zhongqiu_zhang、hd_j16_fuling_fan、hd_j16_huyan、hd_j16_jin、hd_j16_xinxing_liu、hd_j16_guangling_dai、hd_j16_danyang_gan、hd_j16_lanling_miu、hd_j16_runan_he、hd_j16_jincheng_qu、hd_j16_tianshui_yan、hd_j16_ma、hd_j16_youbeiping_yang、hd_j16_kezuhun、hd_j16_lueyang_gou、hd_j16_anding_deng、hd_j16_qiang、hd_j16_liang、hd_j16_muyu、hd_j16_pilv、hd_j16_gongshi、hd_j16_lu_9006、hd_j16_ju、hd_j16_yue、hd_j16_li_79bb。
2. **生成器重跑：** 第 2 期末重跑 gen_hbirth 和 popclean，新人里有大量 hbN 出场者。
3. **交 2-B（只改现有文件）：**
   - mother 恢复或补：刘和 xiongnu_liu_021 → hd_j16_huyan_hou（刘恭 :3541 待核）；石弘 shangdang_shi_005 → hd_j16_cheng_shi；苻坚 lueyang_fu_020 → hd_j16_gou_shi_mu；苻宏 lueyang_fu_026 → hd_j16_gou_shi_hou（待核）；慕容暐 changli_murong_077 → hd_j16_kezuhun_shi；tuoba_028、029、032 的 `#mother = 祁氏` 改指 hd_j16_wei_shi（031 原注「不确定」）。
   - 中文 killer 改指：00_yanzhou.txt:517 → hd_j16_ji_sang；00_yangzhou.txt:305 → hd_j16_han_huang；01_shiliuguozhu.txt:3626–3763 共 10 处 → hd_j16_jin_zhun；:8043 → hd_j16_zhang_chai；:7523 → hd_j16_gou_shi_mu；:8109、:8122 → hd_j16_liu_xian；:8016 → 见偏差 4；01_dishishixing.txt:3120 tuoba_004「桓帝皇后祁氏」→ hd_j16_wei_shi。
   - 慕容朗、慕容鉴（changli_murong_046、047）只在注释写了「#段速骨」，可补 killer = hd_j16_duan_sugu。
   - hedong_pei_037 的 name 直接写了中文「氏」，应改为 Shi_6C0F。
   - 刘英、张贵人的 add_concubine，见偏差 10。
4. **交 2-A：** OE `1415103`（劉皇后，henan_liu_dyn）与 `xiongnu_liu_047` 是同一人的重复。
5. **交 2-D：**
   - 阎鼎、梁综一行的处理，见偏差 3。
   - 张春的用途已查明，是司马保卒年行的凶手。
   - 慕容镇（凶手刘裕）、离班和桃仁（凶手冯跋 beiyan_0001）待核。
   - 梁成的卒年由结局决定。
6. **事件号、变量：** 本期没有新增事件号、变量，也没有面板行。"

# REVIEW
{
 "gate_summary": "我按任务给的命令复跑了闸门，只把输出改到 D:\\Temp\\claude\\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\\scratchpad\\stage\\p2-C_gate_review(.txt)：error 0、warn 0、counts 为空，与实施报告一致。\n\n我另写了核对脚本，放在 D:\\Temp\\claude\\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\\scratchpad\\rv_p2C\\（build.py、check.py、dup.py、q*.py；全量结果在 check.out）。下面各项都由脚本核过：\n\n- 122 个新 ID、25 个新王朝键，都不和库中 49,422 个人物 ID 或已有王朝键重复，暂存文件内部也没有重复。\n- name 全部是名字键；人物名字键、新王朝名键中英两侧都齐。新增键与库中同名键没有异值冲突。复用的 175 个键都不在被 mod 遮蔽的原版文件里。\n- 王朝、家族、culture、rite（mod 的 rite_types）、特质、death_reason 键都存在。\n- 特质：同一特质没写两遍，没有对立特质，性格不超过 3 个，每人恰好 1 个教育特质，都带 historical_character。开局时未满 16 岁的人都有童年特质，没有早于出生或晚于死亡的条目。\n- 父母：存在，性别对，年龄差 ≥13，母亲在子女出生时在世。\n- 配偶：存在，异性，婚期双方都满 16 岁且在世。\n- 凶手：存在，在卒日已出生且在世。\n- 生卒和 05 §1.2、06 附表逐行比过，只有已说明的偏差和下面两条 minor。\n\n查重：我把简繁全名按 UTF-8、GBK、Big5 字节搜了 history/characters、scripted_effects 和 events，又查了同姓同名的名字键和拼音 ID。实施报告认定的刘太后 → xiongnu_liu_047、裴妃 → hedong_pei_037 我核过，没问题。\n\n漏判的是 UUII 书库里生卒为 195.7.1–260.7.1 的人。这组年份是占位值，库里有 2,710 人共用。实施报告和 05 §1.3 恰恰拿这组年份当「同名不同人」的依据，结果把和峤漏判成了新人（major，见 issues），陈安、冯该、韩范、张弘 4 人也待核。\n\n结论：唯一阻塞的是和峤一条，改掉后可以交汇总。其余都是 minor，可以随后处理。",
 "issues": [
  {
   "severity": "major",
   "file": "history/characters/zz_hd_j16_characters.txt",
   "where": "hd_j16_he_qiao（约189行）；连带 hd_j16_he_yu、common/dynasties/zz_hd_j16_dynasties.txt 的 hd_j16_runan_he",
   "problem": "和峤在库里已经有了：he_jiao，在 east_asian_han_180_200.txt:28863，name 键 uuii_book_he_jiao_name，值是「峤」，姓和。它的生卒 195.7.1–260.7.1 是 UUII 占位值（库中 2,710 人共用）。库里还有他父亲和逌 he_you（同样是占位生卒），祖父和洽 he_qia（147–230，dyn_111010095001002），说明汝南和氏这一支库中已有。05 文首补遗规定「命中则改为引用库 ID」，这里却新建了。后果不只是数据重复：脚本按开局日期算，253 开局时 he_jiao 和 hd_j16_he_qiao 同时在世；190、218 开局由 hbirth 出场后，两人在 251–260 年并存，游戏里会出现两个和峤。实施报告的查重和 05 都没发现这一条。",
   "fix": "不新建 hd_j16_he_qiao，改用 he_jiao。由 2-B 在现有文件里把 he_jiao 的生卒改为约 235–292，father 挂 he_you；原来写在 hd_j16_he_qiao 上的 262 年 add_spouse = taiyuan_wang_041 移到 he_jiao 上。hd_j16_he_yu（和峤之弟）的 father 改为 he_you，王朝改挂和逌或和洽一系的库中王朝。没人用了，hd_j16_runan_he 就删掉，删掉后应剩 24 个新王朝。在 07 和 05 §1.3 记上「和峤 → he_jiao」。"
  },
  {
   "severity": "minor",
   "file": "history/characters/zz_hd_j16_characters.txt",
   "where": "hd_j16_chen_an、hd_j16_feng_gai、hd_j16_han_fan、hd_j16_zhang_hong",
   "problem": "库里有同姓同名、生卒为 UUII 占位值的 4 人：chen_an（194.7.1–259.7.1，在 east_asian_diren_180_200.txt，文化 diren、rite shamanism，和陇上的陈安很吻合）、feng_gai、han_fan、zhang_hong_3（都是 195.7.1–260.7.1）。05 §1.3 和实施报告根据这组年份判定冯该等是「三国人、不同人」，但这组年份不是史实，依据不成立。05 §1.3 还建议在去重脚本里把冯该这一对标为「不同人」，也就不该照做。这 4 对和新 ID 的寿命都不重叠，游戏里不会同时出现，所以不阻塞。",
   "fix": "把这 4 对交给 2-A，标「高度疑似同人、待核」，记入 docs/人物审查/同一人物多ID.csv 的待核项，不要标成「不同人」。陈安一对最可能是同一人：核实后可以改用 chen_an（改它的生卒），或者删掉 UUII 那个副本。韩范一对的库中人物，可能是三国时袁尚的易阳令韩范，核过之后可以排除。"
  },
  {
   "severity": "minor",
   "file": "common/dynasties/zz_hd_j16_dynasties.txt",
   "where": "hd_j16_lanling_miu（缪播、缪胤）",
   "problem": "库里有缪袭 mou_xi（186–245，dyn_111010170001002，父 mou_fei）。按《晋书·缪播传》，缪播是缪袭之孙【记忆·待核】。新建兰陵缪氏会把同一家族拆成两个王朝。不过 05 §1.4 已经定了新建，实施是照设计做的。",
   "fix": "交汇总人或 2-A 定。如果要合并，缪播、缪胤改挂 dyn_111010170001002，删掉 hd_j16_lanling_miu；不合并，就在 07 记一笔「不连缪袭」。"
  },
  {
   "severity": "minor",
   "file": "history/characters/zz_hd_j16_characters.txt",
   "where": "hd_j16_xu_qian 生年；hd_j16_liang_cheng 卒日",
   "problem": "许谦的生年，06 附表写约 330，暂存写成 333.1.1，实施报告第三节的生年改动清单里没有这一条。梁成的卒日，05 写 383.11，暂存是 383.12.15（可能是按农历换算的，但报告没说明）。",
   "fix": "在实施报告的偏差清单里补上这两条的理由，或者改回表里的值。"
  },
  {
   "severity": "minor",
   "file": "history/characters/zz_hd_j16_characters.txt",
   "where": "hd_j16_zhang_hao（dynasty = zhang2_dyn）",
   "problem": "zhang2_dyn 的简中名是繁体「張」，所以张蚝显示成「張蚝」，和其他人的简体姓不统一。这是照 05 挂的王朝，不算实施错误。",
   "fix": "可选：交汇总人决定是否把 zhang2_dyn 的简中名改成「张」。这是改现有本地化，会影响张平一系的显示。"
  },
  {
   "severity": "minor",
   "file": "history/characters/zz_hd_j16_characters.txt",
   "where": "生年早于 263 的新人：崔游、范长生、呼延翼、和峤、张瑶、刘殷、刘暾、和郁、山简等",
   "problem": "05 和实施报告只算了 304、346、370、404 四个开局的可见范围。这些人在 218、253、263 开局里原生在场，重跑 hbirth 后，在 190、218 开局里也会出场。和峤撞人就是在 253 开局暴露的。",
   "fix": "汇总人重跑 gen_hbirth 时，顺带检查这些人在早期开局里出场是否合适。需要的话，在 07 记上「早开局可见」。"
  }
 ]
}

# FIX
## p2-C 修正报告

所有改动只落在暂存区 stage\p2-C 的 4 个已登记文件里，没有新登记文件，也没碰 mod 和现有人物文件。替换由脚本 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\fix_p2C\fix.py 完成：每处原文须恰好出现 1 次才替换，写回后仍为 UTF-8 带 BOM、LF 换行。

### 一、逐条处理

**1. major：和峤重复。已修。**
- 删掉了 `hd_j16_he_qiao` 整块及注释，连同其中 262 年的 `add_spouse = taiyuan_wang_041`。
- 删掉了王朝 `hd_j16_runan_he`，以及中英两份 yml 里的 `dynn_hd_j16_runan_he` 键。
- `Jiao_5DA0` 没删：它是库里复用的键，hbirth 模板还有 10 处在用。
- `hd_j16_he_yu`（和郁）的改法：
  - `dynasty` 改为 `dynasty_house = house_111010095001013`，即和洽一系，王朝 dyn_111010095001002「和」。
  - 新增 `father = he_you`（和逌）。he_you 卒于 260.7.1，和郁 250 年出生时他在世，年龄差 55，check.py 核过没有问题。
  - 注释改为：和峤即库中 he_jiao；父亲是 he_you，祖父是 he_qia；he_you 和 he_jiao 迁家族由 2-B 做。
- 结果：新人物 121 个，新王朝 24 个。
- **移交 2-B**（属于改现有文件 east_asian_han_180_200.txt，不在 2-C 的范围，暂存区也放不下）：
  - he_jiao：
    - 生卒由 195.7.1–260.7.1 改为约 235.1.1–292.1.1；
    - 加 `father = he_you`；
    - `dynasty_house` 由 uuii_book_house_32e4e142961d 改为 house_111010095001013；
    - 生卒改完后，再加 `262.1.1 = { add_spouse = taiyuan_wang_041 }`（现在加会成为死后成婚）。
  - he_you：
    - 加 `father = he_qia`（he_qia 147–230）；
    - `dynasty_house` 由 uuii_book_house_1377e67198ef 改为 house_111010095001013；
    - 以后若改卒年，必须晚于 250，否则和郁出生时父亲已死。
  - 2-B 做完前，和郁和父亲 he_you 暂时不在同一家族。这不会报错，只是显示上有差异。
- **移交汇总人**：docs 里还写着新建 hd_j16_he_qiao 和 hd_j16_runan_he，与现在的实现矛盾，涉及：
  - 05 第 37、129、213 行；
  - 02 第 501 行的「汝南和氏」。

  请在 07 和 05 §1.3 记上「和峤 → he_jiao；和郁挂 house_111010095001013，父 he_you」。docs 我没改，以免和其他会话冲突。

**2. minor：陈安、冯该、韩范、张弘四对疑似同人。已修注释，ID 不换。**
- 四人的注释都改成：库中同名人物的生卒是 UUII 占位值，高度疑似同人，待 2-A 核，不得标为不同人。
- 冯该原注释「同人去重须标为不同人」已删掉。
- 陈安注释写明库中 chen_an 的文化 diren、rite shamanism；韩范注释写明库中那位可能是袁尚的易阳令韩范。
- **移交 2-A**：这四对记入 docs/人物审查/同一人物多ID.csv 的待核项。陈安一对最可能是同一人。不要照 05 §1.3 的建议把冯该一对标成不同人。csv 我没写。

**3. minor：兰陵缪氏不连缪袭。不改。**
05 §1.4 已定新建，审查的依据也标着【记忆·待核】。我只在 `hd_j16_lanling_miu` 的注释里写了「照 05 新建，不连库中缪袭 mou_xi（dyn_111010170001002），是否合并由汇总人定」。请汇总人决定，并在 07 记一笔。

**4. minor：许谦生年、梁成卒日。两条都已处理。**
- 许谦：改回 06 附表的约 330（330.1.1）。346 开局是 346.12.10，那时他已满 16 岁，所以把童年特质那块（333 出生加好奇、349 去掉）整块删了。头部注释也改为「约330」。
- 梁成：383.12.15 保留。注释补了理由：05 写的是 383.11（农历十一月），按 05 §4 的 G6 规则「农历月 +1、日取 15」换算。

**5. minor：张蚝显示成繁体「張蚝」。不改。**
这要改现有本地化 zhang2_dyn 的简中名，会影响张平一系。请汇总人决定。

**6. minor：早开局可见。不改。**
生年早于 263 的新人，在 218、253、263 开局里原生在场，重跑 hbirth 后在 190、218 开局里也会出场，包括崔游、范长生、呼延翼、张瑶、刘殷、刘暾、和郁、山简等（和峤已删）。请汇总人重跑 gen_hbirth 时顺带看一下是否合适，需要的话在 07 记「早开局可见」。

### 二、验证
- **闸门**：按任务命令复跑，输出在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p2-C_gate.txt。结果 error 0、counts 为空，overlay 4 个文件；char_ids 49,543，正好是库 49,422 加新 121。
- **审查人脚本**：在 rv_p2C 下依次跑了 build.py、check.py、dup.py。
  - build.py 重建 idx.pkl：新 121 人、新王朝 24 个。
  - check.py：ID 冲突、字段、新王朝、本地化冲突、表值偏差五节都为空。和郁一行是 dyn_111010095001002、F=he_you，许谦是 330.1.1–396.1.1。
  - 注意：check.py 写死输出到 rv_p2C\check.out，审查人原来的 check.out 已被修正后的结果覆盖。
  - dup.py：要用到 opencc，加 -I 时找不到这个模块，所以不加 -I 跑，结果在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\fix_p2C\dup_new.out。121 行里没有 he_qiao。和郁那行命中的 PYID he_yu，名是「玉」，不是同一人。
  - 这两个脚本只核暂存区自身，不能证明 2-B 那边的移交会被做完。

### 三、未解决项
1. 移交 2-B：he_jiao、he_you 的生卒、父亲、家族修改，和峤的配偶 taiyuan_wang_041。不做的话，和峤仍以占位生卒存在，并且没有妻子。
2. 移交 2-A：四对疑似同人写入待核 csv。
3. 交汇总人：docs 05、02 的和峤条目与 07 记录；缪氏是否合并；zhang2_dyn 简中名；早开局可见检查；重跑 gen_hbirth。

没跑 gen_hbirth、popclean、hd_fo 和纹章生成器，没开游戏，没提交。