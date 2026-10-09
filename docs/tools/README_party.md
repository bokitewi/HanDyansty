# 朋党系统生成脚本

在 mod 根目录运行（顺序无关，可重复运行）：

| 脚本 | 生成 |
|---|---|
| `python docs/tools/gen_party.py` | `common/scripted_triggers/hd_party_triggers.txt`、`common/script_values/hd_party_values.txt` |
| `python docs/tools/gen_party_effects.py` | `common/scripted_effects/hd_party_effects.txt`、`common/modifiers/hd_party_modifiers.txt`（含青睐复制件，读取局势文件的组效果）、`common/opinion_modifiers/hd_party_opinions.txt` |
| `python docs/tools/gen_party_events.py` | `events/hd_party_events.txt` |
| `python docs/tools/gen_party_gui.py` | 在 `gui/window_tgp_dynastic_cycle.gui` 中重写"政治派别面板"块 |
| `python docs/tools/gen_party_gui_domestic.py` | 同一 GUI 中：顶部本国头像、组按钮本国数字、本国势力框、隐藏全局成员名单（须在上一个脚本之后运行） |
| `python docs/tools/gen_party_loc.py` | `localization/simp_chinese/hd_party_l_simp_chinese.yml` 与 replace 覆盖中的三个键 |

**改了局势文件里的组效果后，必须重跑 `gen_party_effects.py`**，否则"青睐朋党"复制给君主的效果会与组效果不一致。

手写文件（不由脚本生成）：`hd_party_identity_triggers.txt`、`hd_party_action_effects.txt`、`hd_party_debate_effects.txt`、`hd_party_decisions.txt`、`hd_party_guis.txt`、`hd_party_on_actions.txt`、`hd_party_debate.txt`（活动）、`hd_party_debate_intents.txt`、`hd_party_debate_events.txt`、`hd_party_debate_widget.gui`、`zz_hd_party_value_overrides.txt`。

## 外戚扫描（2026-10-08）
- **外戚的定义**：朝廷君主的配偶、母亲、侧室、子女配偶所属宗族（dynasty）的全部成员。
- **扫描效果**：`hd_party_waiqi_sweep_effect`，在手工维护的 `common/scripted_effects/hd_party_waiqi_sweep_effects.txt` 中。生成的 `hd_party_refresh_waiqi_list_effect` 会在末尾调用它，模板在 `gen_party_effects.py`。
- **入组**：后族宗族成员只要满足以下全部条件，就加为参与者（不论有无官职），并强制改为外戚（覆盖原有的组别锁定）：
  - 成年；
  - 最高领主是本朝廷君主；
  - 不是天子、不是独立统治者、不是宦官；
  - 不是他党现任领袖。
- **失势**：宗族已不在后族列表的外戚，清除组别锁定，由引擎重新归组。外戚党现任领袖不动。
- **保留条件**：`gen_party.py` 的 `hd_party_manual_participant_valid_trigger` 已加入 `hd_party_is_waiqi_trigger`，因此无官职的外戚不会在年度结算时被移出。
