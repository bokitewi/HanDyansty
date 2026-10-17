# 朋党权重实装与连通性清理核验（2026-10-15）

## 已实装

仅修改 E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty 下两个现有文件：

- common/script_values/zz_hd_han_breakup_values.txt：新增拥护 -20、尊王 -20、对抗 +20 三个独立 if，可与全部既有权重累加。
- common/scripted_triggers/zz_hd_han_breakup_triggers.txt：追加 hd_hb_party_group_state_trigger 与 hd_hb_party_state_trigger，未更改既有 force/block/player 触发器。

备份原件、SHA-256 前后清单、完整 party_change.diff 和 party_static_results.json 都在本目录。没有修改英文、UI、美术、其他朝廷系统、董卓路径、存档、播放集、工坊或共享工具；没有启动游戏或提交/推送。没有调用网页思考。

## 状态映射依据

1. common/scripted_effects/hd_party_effects.txt:112–116 给成员写入 hd_party_my_court、hd_party_my_group、hd_party_my_stance；缓存有效期400天。
2. 同文件123–139的 hd_party_save_member_court_effect：汉朝封臣的朝廷是 h_china.holder，其他封臣的朝廷是 top_liege；朝廷不是任意直属小领主，也不是任意有拥护 modifier 的人。
3. 同文件774：朝廷持有 hd_party_$G$_stance = flag:$STANCE$；866行持有 hd_party_$G$_attitude = flag:$ATTITUDE$。877/881行证实 support/oppose。
4. 同文件778、911–915及 common/scripted_triggers/hd_party_triggers.txt:197–200 证实 zunwang 为尊王立场。
5. 五组为 huanguan、waiqi、wuxun、shizu、hanmen。新 helper 先验证成员 my_court 存在且等于当前 top_liege、该朝廷存活并已初始化，再按成员 my_group 精确读取当前朝廷本组的原始态度/立场。不会读取别组、旧朝廷、任意拥护修正或单独过期的 my_stance 修正。
6. D0所有决定仍先于关系变化；D3按实际新领主/新朝廷重新读取。如果成员还缓存旧朝廷，则不误给旧朝廷加成，也不在本次任务里强行重建其朋党归属。

## 静态验证

432组成员状态：五组及未知组 × support/oppose/neutral/缺失 × zunwang/其他/缺失 × 当前/错误/缺失朝廷 × 存活/死亡朝廷。解析实际新增触发器和宏参数后计算三项加减，另测五档既有分数的0–100截断。

结果通过；拥护+尊王=-40，对抗+尊王=0，错误朝廷/未知组/缺失状态不错误加分。AST逐项比较确认全部既有分数条件、概率函数和原force/block/玩家触发器未变。既有新增加的律法、正统预期、等级和恐惧等权重也完整保留。

## 连通判定可用依据

原版 game/common/scripted_triggers/00_game_rule_triggers.txt:27–39：exclave_independence_trigger 在 county title 上使用 is_connected_to={ target = root.capital_province.county }，不是只查直辖相邻县。

原版 game/common/scripted_effects/00_game_rule_effects.txt:1163–1168 从首都 every_connected_county 建立飞地集合；可用参数 invert=yes、max_naval_distance=2000、allow_one_county_land_gap=yes。原版还有不同游戏规则分支，不能把2000海程或一县外国陆隙豁免擅自当成本任务规则。建议使用原版严格连通默认口径（陆地/游戏认定的连接，不额外添加海程或一县陆隙宽容）；海峡和默认图连通的真实引擎表现未启动游戏验证，不能宣称全部海域均连通。

同文件1233–1275在整体释放国王/公爵前检查其 any_sub_realm_title，避免因一个飞地释放仍有连通主体的统治者。新清理应同样按“封臣 entire sub-realm 中任何实有地 county 连到原直属领主首都就保留整体”判断，绝不能只看封臣首府，也不能因任意一块飞地拆其整个主体。

当前链：D0 hd_qxzl_begin_effect → 先算全部/分批释放；D3 hd_hb_recheck_duchies_effect → hd_hb_apply_round_effect → HD_HB D3_COMPLETED。空间清理应另设一个仅一次的阶段和完成标记，在D3整轮应用之后快照仍存在的关系与结果，再实施变更，不把它当作原D3概率重判。原初汉对象的分裂后领国需要有界追踪，不能仅扫描当时 h_china 剩余封臣漏掉已独立郡/王国中的封臣。不得在释放过程中重新扫/循环至稳定。

## 朝贡可用效果与限制

原版 common/scripted_effects/00_interaction_effects.txt:2322–2325 说明 start_tributary_interaction_effect 可无战争直接调用，参数 TRIBUTARY、SUZERAIN；模组覆盖文件中也保留此 helper。它会按政体/头衔选择具体 contract_group，并创建停战。直接 start_tributary={ contract_group=... suzerain=... } 有模组实例 zz_hd_304_startup_effects.txt:98，不能把带25年双向停战的完整交互 helper 当成没有副作用。

common/subject_contracts/groups/subject_contract_groups.txt:159–173（模组）规定 tributary_celestial 宗主必须 tier_hegemony 且 celestial_government，因此普通独立郡/王国不能一律使用此组。普通组 tributary_subjugated 在100–115行；不应为天朝宗主强塞普通组改变既有契约语义。

关键限制：
- 模组 common/scripted_triggers/mpo_scripted_triggers.txt:917–920 的 can_have_tributaries_trigger 要求 can_have_tributaries 法律旗标、is_independent_ruler=yes、非herder。
- 原版 common/character_interactions/00_tributary_interactions.txt:15–22 同样要求宗主独立；注释明确不能与非独立统治者创建新朝贡关系。
- 原版与模组 common/scripted_effects/00_tributary_setup_effects.txt:4–5 明确写道，现有封臣必须先释放并重建为朝贡者，才能拥有自己的朝贡者。
- 天朝四档官僚制律法本身均带 can_have_tributaries（模组00_realm_laws.txt:1942/1994/2090/2182）；但“有法律旗标”不能替代独立条件。

因此，用户要求的“原直属领主仍是封臣时，孤立下级独立并朝贡原直属领主”存在明确脚本合法性边界。不能绕过检查赌 start_tributary 内部是否接受，不能改向最高领主，不能为满足朝贡条件自动释放其原领主。

## 边界方案及当前待决

- 封臣首府不连但其任一所属县（含下级县）连通：整体保留。
- 一人多块分离领地：有任一块连通则整体保留；全体不连才是整体独立候选，全部县一起随其现有头衔结构处理。
- 君主直辖飞地：豁免，不换持有者、不生成新领主。
- 单次清理：所有连通结果先快照，再释放，避免先断桥造成级联或无限清理。
- 每个候选先保存原直属领主，独立成功后只向这个保存的有效角色建立朝贡，不能再用已变化的 liege。
- 嵌套封臣且原直属领主非独立：尚需用户决定例外处理。可选择仅对原直属领主具备合法宗主资格者执行清理，其余保持现状并记录；或另行明确改变该边界的规则。不能默认扩大到独立上级或更换朝贡对象。

连通性阶段目前未写入有效脚本；原因是上述必须进一步决定的嵌套宗主限制，不是授权未到、网页协作、文件写权限或工具拒绝。权重部分已完成，可独立生效。