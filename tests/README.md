# 廷议任命后端检查

在 Beta 根目录运行 `node tests/tingyi_appointments.cjs`。

## 当前范围与源码依据

普通朝臣不新增“无封臣／有实封爵”候选限制，也不要求保留全部地方头衔和封臣。根据 2026-11-07 父审查最新裁决，上一轮自行增加的保全绕行、granted 预授及回滚链已删除。

- 普通廷臣沿本体 `00_petition_liege_effects.txt` 的 `petition_liege_0101_council_seat_effect`：先正常 `add_courtier`，再原生授席。
- 有地或无地统治者沿本体 `10_dlc_tgp_scripted_effects.txt` 的 `fill_the_ministry_effect` 入口：设置实际皇帝为 `councillor_liege`，调用完整 `got_minister_position_effect`。当前 Beta 的完整覆盖位于 `common/scripted_effects/WJ_ministry_override_effects.txt`；普通职位的 appointment、旧官署退休、封臣转隶及既有实封／fixedregent 例外均交给该公共出口处理。
- 丞相仍只经正式完整授相脚本；普通转任不调用或拆改其特殊保留规则。侍中／大司马兼任不套内阁转任限制。
- 原生授衔回调可能已完成入阁，后端不重复 assign。公共出口只比较职位 key 时，地方同类职务还须转入皇帝的真实内阁。正常转任使用 `remove_existing_councillor=yes` 和 `fire_on_actions=yes`，不先手动辞职，不对调成两席。

## 离线检查的证据边界

检查直接加载并执行**整个当前 `got_minister_position_effect` 定义**，不裁剪授衔片段。另执行真实职位 `valid_character`、部长资格、普通九职及 WJ 三职 `on_title_gain` 子动作和 appointment 后端 AST。覆盖有封臣普通地方官、间接封臣、无地幕僚、同类地方职位转朝职、实际旧席释放、原生拒绝、转庭或授衔失败、席位与头衔不全、快照失效及失败变量清理。

引擎原语（包括头衔提升／地方职位退休、转庭、席位转移、回调时序）仍由可注入失败的夹具提供；摄政／契约特权／任期提示等下游独立子系统只检查调用，不在这里模拟完整机制。`assign` 的旧初始化 helper 仅设置测试初态；运行路径不会用它自动制造“换领主＋授 title＋入阁”的成功。不会读取旧 fixture 输出作为验收证据。输出明确标注 `LIVE ENGINE: NOT RUN`。

## 父级接口与实机待验

接口名未改：`WJ_ty_appointment_candidate`、`WJ_ty_appointment_valid`、`WJ_ty_appointment_snapshot`、`WJ_ty_appointment_clear`、`WJ_ty_appointment_commit`。

成功仅认实际目的席位＋官署 title＋皇帝雇主，且原席不再由候选占用。commit 输出 scope value `wj_ty_appointment_success=yes/no`；失败设置操作者变量 `wj_ty_appointment_failed=1`，snapshot／clear／成功 commit 清除。父级仅在 success=yes 时回信、冷却及关闭；原生失败的部分状态不由本后端伪造回滚。

实机分别测试一名有下属封臣的同朝地方官和一名他庭无地幕僚：确认候选可选、实际原席与新席、官署归属及失败提示。普通地方头衔／封臣按原公共出口处理，不以“全部保留”为通过标准。再推进一天检查既有 `hd_cp_handoff` 的旧官署交接；丞相另核完整授相及其原有保留行为。可结合实际 `HD_CPDIAG` 日志和 scopes 核对，不能把离线通过或旧日志当本批实机验收。
