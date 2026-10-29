# p6-B 最终报告（修正后合并版）

# p6-B「404 开局内容」修正报告（审查后终版）

## 零、审查意见处理结果
审查共 3 条，都是 minor，都只涉及报告。代码不用改，暂存副本这一轮没动。

1. **set_knight_status = forbid 没写进报告**：已修。
   - 暂存代码第 80 行在安置后执行 `set_knight_status = forbid`，头注④写了理由。
   - 本报告第二节第 2 条、第六节、第九节首测项都已补写。
2. **报告引用的闸门是旧的一次**：已修。
   - 已对当前暂存副本重跑闸门，输出在 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p6-B_gate_final.txt
   - 结果：error 0，warn 0，相对基线新增 0 条，resolved_vs_baseline 3。
   - 说明：p6-B_gate_rev 和 p6-B_gate_fix 是上一轮内部修订时跑的，以本次 _final 为准。
3. **d_dunhuang 改 d_dunhuang_hexi 没人认领**：已修。
   - 第七节已从「可选」改为「06 §0 已列的交 A4 待办，请汇总人指派」，并写明要改的冻结文件位置。本路不自己改。

**仍未解决的**：没有本路能处理的项。第七节所列都要汇总人或别路处理。

## 一、暂存任务名与文件
- 暂存任务名 **p6-B**。`stage.py p6-B list` 只有一条：edit `common/scripted_effects/zz_hd_j16_startup_404_effects.txt`。
- 暂存副本：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p6-B\files\common\scripted_effects\zz_hd_j16_startup_404_effects.txt
  - 带 BOM，LF，括号配平。
  - p1-S 写的「历史入侵预设」块一个字节都没动。
  - manifest 的 base_sha256 与 mod 当前文件一致，没有并发冲突。
- `history/titles/zz_hd_404_titles.txt`：核对通过，没改，也没 stage。
- 没有直接写 mod，没跑生成器，没开游戏，没提交 git。
- 闸门（终版）：结果见第零节第 2 条，输出文件 D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p6-B_gate_final.txt
- 辅助脚本（只读，不进 mod）：D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\p6b\ids.py

## 二、改了什么
在 `hd_j16_startup_404_effect` 的预设块之后追加了三段：

1. **只读核实的注释**：秦况计数、shelun_3、各条 done 预设都已到位，本文件不重复设置。
2. **宫廷安置（自拟）**
   - 包在 `hd_history_events_enabled_trigger = yes` 里，调用 `hd_j16_404c_court_place_effect`。
   - 安置对象：冯跋 beiyan_0001、冯素弗 beiyan_0002、冯弘 beiyan_0003、高云 1415976，放进慕容熙 changli_murong_048 的宫廷。
   - 条件：此人在世、无雇主、无地、不是统治者；慕容熙在世且有地。
   - 由辅助效果 `hd_j16_404c_place_effect` 执行，开头先清掉已存的 scope。
   - **安置后对这几人执行 `set_knight_status = forbid`**：
     - 这是永久设置，但玩家仍可手动任命他们当骑士。
     - 目的是防止 AI 宫廷按武力自动选他们当骑士，在节点触发前阵亡。
     - 写法照原版 fp2_struggle_events 3171 行、fp3_extra_flavor_events 267 行。
     - 只对成年廷臣有效；四人生于 367、368、370、375，到 404 年都已成年。
   - 日志：`HD_J16 startup_404 FIRE|SKIP place_<ID>` 和 `HD_J16 startup_404 FIRE court_place`。
3. **p4-D 交接**
   - 入口最末一行、规则 if 之外加了 `hd_j16_startup_404_flavor_effect = yes`，这样关了规则的玩家也能看到「仇池」国号。
   - 这个效果自带 404.3.24 日期闸门。
   - 大厅阶段已经调过一次国号子效果，这里再调一次不会出问题。

## 三、各项逐一处理
- **§3.4 原有的 done 预设（liuyu、juqumengxun、tande）**：已在，没改。
  - liuyu 在本文件的规则 if 里。
  - juqumengxun、tande 在 `hd_nbc_hi_done_effect` 里，无条件设置（R7）。
- **§3.4 补设 luxun、murongde、tufawugu**：第 1 期已写在本文件的规则 if 里，不缺，没补。
- **p5-A1 / p5-C 秦况计数**：核实成立。
  - E4-W50 的 `hd_j16_node_qinkuang_effect` 在 start_year >= 404 首跳时，同时设 `hd_j16_qin_collapse` 和 `hd_j16_qin_collapse_m = 120`，并摘掉导演旗标、调排程。
  - 规则关闭时心跳不跑，两个变量都不会设，符合「要么同时设、要么都不设」。
  - 所以开局里不重复设。
- **shelun_3**：不预设。在 404 局里，`hd_j16_hi_next_stage_closed_trigger` 把它视为已开。
- **p4-D 仇池国号**：已加，见第二节第 3 条。
- **§4.3 盘面**：与 06 一致，不改头衔。
  - 慕容德：k_uuii_qingzhou、d_qiguo、广县 2978。
  - 勃勃（xiongnu_liu_050）、傉檀（tufa_012）、乾归（qifu_008）：上级都是 e_bingliang。
  - 李暠：持两个敦煌郡。
  - 慕容熙：k_pingzhou、扶黎 3479。
  - 拓跋遵：k_uuii_bingzhou。
  - 刘裕：京口 2086。
  - 唯一差异：社仑 yujiulv_20004 在 404 没有领地，要靠 shelun 入侵起兵。这与 §3.4 一致，请 6-N2 知悉。
- **勃勃起兵**：归 6-N2。
- **并州王冠**：p5-C 已做。
- **H 线**：归 6-S。
- **刘义真、刘义符**：已在 early_spawn.tsv（1800917、1800916），F-3 重跑后生效。
- **其余 404 原生人物**：`hd_j16_resolve_effect` 直接按 `character:ID` 取人，开局不用处理。
- **404 头衔改动**：没有别路转交的改动，所以没有 stage。

## 四、自拟与偏差
1. **宫廷安置只收 E5-M60 一组**（照 5-D 先例，再收窄）。
   - 入选标准有四条：
     - 节点要求此人身在某国；
     - 节点自己不做 set_employer；
     - 404 原生、无地、人物历史里没有雇主；
     - 节点窗口晚于 404.3.24。
   - 安置后设 knight forbid（理由见第二节第 2 条）。
   - 不授郡，不任官。
2. **404 不做百济换人**。
   - 404 年在位的是阿莘王 korean_buyeo_42（生卒待核）。
   - `zz_hd_404_titles.txt` 第 200 行及 486 行起仍是虚构的 hd_nbc404_chief_baiji，可交 F 参考。
3. **南凉 tufa_012 在 404 显示「凉」（dynn_title_liang_west），没改**。404 开局时没有 A6-F10 所说的重名。
   - 如果要统一，可在本入口风味行之后加一行：`hd_nbc_realm_name_effect = { WHO = tufa_012 NAME = dynn_title_nanliang FIXED = no }`。列为可选。
4. 李暠的主头衔不再作为本路的可选项，已移到第七节第 5 条作为待办。

## 五、本期面板行清单（交 F-1，只列不写）
- 本路 0 行。
- 404_01–07 改为 le404、去掉日期闸门，以及新组 hd_hev_grp_j16_e5 的 15 行，归 F-1 和 6-S、6-N1、6-N2 的节点 FIRE 分支。

## 六、新增名字清单
- 新事件号 0；新 yml、触发器、修正 0；新全局变量 0（只有 debug_log）。
- 06 编号式旧名改语义名：0 条。
- 新效果 2 个：`hd_j16_404c_court_place_effect`、`hd_j16_404c_place_effect`（全 mod 不重名）。
- 新 saved scope 2 个：`hd_j16_404c_court`、`hd_j16_404c_who`。
- 新人物状态：冯跋、冯素弗、冯弘、高云入慕容熙宫廷，并设 knight_status = forbid（永久）。
- 卒年表 PRE：归本路设置的 0 条。本路没有节点；开局按 TEMPLATE §5-15 不设 PRE。

### 我读别路的变量
| 名 | 来源 | 用途 |
|---|---|---|
| （无全局变量） | — | 只读触发器 `hd_history_events_enabled_trigger`，调用 4-D 的 `hd_j16_startup_404_flavor_effect` |

### 我设给别路的变量 / 状态
| 名 | 类型 | 给谁 | 说明 |
|---|---|---|---|
| 冯跋、冯素弗、冯弘、高云入慕容熙宫廷，并设 knight forbid | 开局状态，不是变量 | 6-N1 E5-M60（M65） | M60 用 `hd_j16_n1_in_realm_trigger`（top_liege ?= 慕容熙）判断，开局安置正好让它在 404 局成立。M60 如果还要 add_courtier 或 set_employer，须先判断目标是否已在该宫廷 |

## 七、需要汇总人处理的事项
1. **6-S 的 J50 随从入帐会重复**。
   - 冻结文件 `zz_hd_nbc_startup_effects.txt` 的 `hd_nbc404_court_effect`，在 404 大厅之后已把刘毅、何无忌、刘道规、孟昶、诸葛长民、刘道怜、檀凭之 7 人 add_courtier 给了刘裕。
   - J50 再加一次会撞上「已在该宫廷」。
   - 二选一处理：J50 先判 employer 再加；或者删掉冻结文件里那一段。
   - 魏咏之 hd_j16_wei_yongzhi 不在旧名单里，由 J50 负责。
2. **本路有意没安置的人**。下列当事人开局时可能无雇主，节点在 set_employer 之前要先判断：
   - **6-N1**：
     - M55：慕容超 changli_murong_058、公孙五楼 gong_sun_wu_lou、慕容镇、韩范
     - T60：拓跋嗣 tuoba_013、拓跋绍 tuoba_qinghe
     - Y50：姚泓 shaodang_yao_020、姚懿 _021、姚弼 _022
   - **6-N2**：
     - X58：叱干阿利 chigan_003、王买德
     - X74：乞伏公府 qifu_006
     - X82：秃发虎台 1415833
     - X90：李歆 longxi_li_007、李恂 longxi_li_010
   - **6-S**：
     - J45：刘穆之
     - J60：卢循、徐道覆
     - J70：檀道济 gaoping_tan_dao_ji、刘敬宣 congtingli_liu_044、段宏 liaoxi_duan_065
     - J73：孙处、沈田子 1802134、杜慧度
     - J75：谢混
     - J76：朱龄石、臧熹、谯道福
     - J78：鲁轨、司马文思
     - J80：姚赞、姚恢、沈林子 1802135、朱超石、王仲德
     - J82：王修、傅弘之、毛德祖
     - J51：冯迁；丁旿
     - J52、J86：司马德文
3. **tuobagui_2/3 闸门**：404 局 M10、T10 前标时，按通则也应设闸门（归 6-N1）。但 404 局已由 W50 的 M=120 了结，不影响结果，只记一笔。
4. **两项可选**：百济换人（第四节第 2 条）、南凉国号（第四节第 3 条）是否交 F，请决定。
5. **A4-G1 敦煌主头衔：06 §0「交其他节」已列的待办，没有人认领，请指派 A4 或 F**。
   - 现状：
     - 404 头衔历史第 192–193 行，d_dunhuang（本地化名「冥泽」）和 d_dunhuang_hexi（真敦煌）都由李暠 longxi_li_005 持有，liege = 0，写法合法。
     - 冻结文件 `zz_hd_nbc_startup_effects.txt` 中 `hd_nbc_realm_display_effect` 的 404 分支，仍以 d_dunhuang 为李暠的主头衔，在上面设「西凉」国号。
   - 要做的事：
     - 把主头衔换成 d_dunhuang_hexi；
     - 改上述 404 分支，给新主头衔设西凉国号；
     - 复原 d_dunhuang 的「冥泽」名字；
     - 再查其他开局（346、370）是否有同样的问题。
   - 本路没有越权改冻结文件。

## 八、回归复核（08 §10）
- **R7**：三个预设都没动。本次改动在预设块之后，不碰京口 J50 首跳开打，也不碰谯纵入侵。
- **R1–R6**：本路只改了 startup_404 一个文件，不涉及结局读取、伐蜀和淝水兜底、东征、D24 豁免、永嘉、慕容王朝写法。

## 九、首测项（交汇总人）
- 404 局的 game.log 应出现 `HD_J16 startup_404 FIRE court_place` 和 `HD_J16 flavor_404 FIRE startup`。
- 看 `place_1415976` 是 FIRE 还是 SKIP。
  - 如果引擎开局把高云放进了高句丽宫廷，这里会 SKIP。
  - 那样的话，M60 换主时高云是高句丽廷臣。不阻断流程，但要实测。
- **新增**：几年后看冯跋、冯素弗、冯弘、高云是否从未被 AI 任命为骑士（knight forbid 是否生效），以及玩家能否手动任命他们。
- 规则关闭开局：不应出现 court_place 日志；仇池国号仍应显示。