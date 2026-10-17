# 解体后一次性空间清理：最终实装（2026-10-15）

状态：完成；31个最终静态效果场景通过。未启动游戏。本次只修改E盘HanDyansty；未改工坊、播放集、存档、全局设置、英文/UI/美术或推送。此前拥护-20、尊王-20、对抗+20权重及原始政治触发器文件哈希未变。

## 文件和交付

修改 common/scripted_effects/zz_hd_han_breakup_effects.txt、common/on_action/zz_hd_han_breakup_on_actions.txt、events/zz_hd_han_breakup_events.txt；新增 common/scripted_effects/zz_hd_han_breakup_spatial_effects.txt、common/scripted_triggers/zz_hd_han_breakup_spatial_triggers.txt、tests/han_breakup_spatial.cjs。

同目录 before_manifest.json 与三份原件为写前备份；installed_manifest.json 包含六个最终文件SHA256。spatial_change.diff 是完整差异；new_spatial_code.txt 是所有变更文件的完整最终代码；spatial_static_results.json 是31个场景的结果。修订前副本也保留，没有永久删除。

## 明确时序

D0：在任何独立前，为全部原汉霸权县级以上实有地封臣保存其所有非landless、县级以上的领地头衔票据，放在h_china的 hd_hb_spatial_titles。包含郡/王国头衔，防无自持县的郡主漏判；不包含汉君直辖头衔。随后原D0逻辑照常。

D3：原郡复判及所有AI结果应用结束后，才设置 hd_hb_d3_applied，再调用 hd_hb_maybe_spatial_effect。不是把空间清理当作第二次权重判定。

玩家：每次展示原选择前记录玩家角色收据 hd_hb_pending_players 和当时直属领主 hd_hb_choice_pending_liege。两种选项/触发失败均先清理pending，再唤醒门控。有效玩家未答复时暂缓空间阶段；由h_china最多排一个一天后的等待收据。等待只读这份有界玩家角色列表，不重复空间判定、不扫全世界、不新增全局日/月pulse。死亡、失地、变AI或换直属领主使旧选择失效时清理收据。角色收据避免玩家转封全部初始县后被漏等。

所有有效待选结束后：设置 hd_hb_spatial_started 防重入；解析初始领地头衔现任持有者并按角色去重；对全部对象先快照并判定，再全部释放，最后清理票据/临时变量和玩家收据，设置 hd_hb_spatial_done。后续回调不重复独立或朝贡。原D30刘备/公孙瓒链和董卓死后另一路均未修改。

## 连接口径和整体处理

以空间清理开始前的原直属领主首都县为目标。对封臣整个 sub-realm 的每一个实有地 county，调用本机原版接口 is_connected_to={target=保存的原直属首都县}；只要任何所属县（含下级县）连通，就保留其全部领地，不看首府单点，不因一块飞地拆全体。

只用原生默认领地连通逻辑，不用直辖邻接近似，不额外添加2000海程或一县外国陆隙宽容。海峡/海路的底层默认图行为未启动游戏实测；静态图场景不是真实地图验证。

全部连通结果固定在释放前的同一快照。即使先释放一个桥接封臣，也不在同轮对其他人重算，不制造级联或循环。君主直辖孤县不生成领主、不剥离头衔；只处理现有封臣整体。空间强制独立不调用忠顺/忠信豁免或概率。

## 原领主与朝贡对象

每个候选在任何独立前保存 hd_hb_spatial_direct、hd_hb_spatial_top、hd_hb_spatial_capital、hd_hb_spatial_suzerain。原直属领主独立就用它，否则按用户新授权用原最高领主。top_liege不跟随suzerain链：已有朝贡者可以自己拥有朝贡者，仍遵循本次原最高领主关系。

实际变更前复核仍是原直属关系、对象存活有地未独立且非既有朝贡者、保存宗主存活且有primary_title，并满足本机can_have_tributaries_trigger（法律旗标、独立、非herder）及无宗主循环。无法满足时保持原封臣关系并记录跳过，不先独立再猜宗主。

独立后再复核宗主，防原生on_action副作用改变资格。保存宗主为 tier_hegemony 且 celestial_government 时使用 tributary_celestial；否则使用现有通用 tributary_subjugated。采用各组既有默认义务，不强改政体，不调用会额外创建停战的交互helper，不强塞天朝契约给普通君主。

原生朝贡失败时，按模组现有 type=swear_fealty + change_liege 事务尝试恢复保存的原直属领主。恢复条件包括原直属仍活着、是统治者、等级更高且不形成循环。若宗主在独立副作用中死亡且原直属也无法恢复，只记录明确失败，不创建指向死亡/空角色的关系，不擅自另找第三方。此极端失败路径不是事务原子性保证。

## 本机API依据

- 模组 common/scripted_triggers/mpo_scripted_triggers.txt:917–921：can_have_tributaries_trigger 的实际脚本限制。这里是遵循已验证合法入口；不声称证明C++ start_tributary对所有非法输入的行为。
- 模组 common/subject_contracts/groups/subject_contract_groups.txt:159–173：tributary_celestial 的 is_valid_tributary_contract 要求霸权级+celestial_government；100–115行为通用 tributary_subjugated，无该专门限制。
- 模组 zz_hd_304_startup_effects.txt:98–101：start_tributary={contract_group=tributary_celestial suzerain=...}的现有工作用例。
- 原版 common/scripted_triggers/00_game_rule_triggers.txt:27–39、00_war_and_peace_triggers.txt:1058–1064：county-title is_connected_to、目标首都county的现成用例。
- 原版 common/scripted_effects/00_game_rule_effects.txt:1163–1168：every_connected_county及invert/max_naval_distance/allow_one_county_land_gap参数；本任务未额外加入宽容参数。同文件1233–1275整体释放前检查全辖境，避免部分连通误拆。
- 模组 common/scripted_effects/zz_hd_confederation_effects.txt:594–600：type=swear_fealty、change_liege、resolve 的恢复原领主事务形式。

## 静态验证与限制

运行 node tests/han_breakup_spatial.cjs（在模组目录）可复跑31场景：直属/嵌套、部分连通/全断、下级县连接保护、直辖孤县、父子两种顺序、重复头衔、普通/天朝契约、无法律/死亡/herder/无首都宗主、朝贡失败直接/嵌套回滚、D3前不执行、玩家延迟/转封/换领主/死亡、继承、重复回调、不级联、忠信仍按空间强制，以及独立中宗主死亡/失去法律资格、无自持县郡主。

测试解析实际脚本并执行其受支持条件/效果模型；原生连通图和头衔事务为模型桩，不是CK3引擎执行。不能宣称游戏加载、真实海峡/海路或on_action副作用实测通过。

初始对象通过D0领地头衔现任持有者追踪，不全世界搜索；旧存档若已经在旧版本完成D0/D3、没有新票据和d3_applied标记，不自动追溯补跑空间阶段。本任务没有读取或改写存档，也未新增全局迁移扫描。无未解决的正常流程阻塞。