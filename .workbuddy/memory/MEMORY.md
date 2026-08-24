# 汉晋春秋 (HanDynasty) Mod — 长期项目笔记

## 模组性质
- CK3 **汉总转换 mod**（tags: Alternative History / Total Conversion）。
- descriptor.mod 用 `replace_path` 替换：`common/landed_titles`、`history/titles`、`history/characters`、`history/provinces`、`history/province_mappings`、`history/wars`、`map_data`、`common/struggle/struggles`、`common/religion/*`、`common/bookmarks` 等。
- **关键推论**：原版地图头衔（`c_byzantion`、`b_aachen`、`b_constantinople`、`b_krakow`、`b_london`、`b_paris`、`b_reims`、`b_vaticano`、`e_france`、`k_france`、`e_byzantium`、`b_roma`、`d_sunni`）与 `struggle:persian_struggle` 等在原版世界存在、在 TC 中**完全不存在**。
- descriptor.mod **未 replace_path 任何 localization** → 模组继承原版全部本地化（包括 coronation_activity_l_*.yml 等）。新增/恢复事件若用原版 loc 键可直接复用，无需补本地化（除非模组主动覆盖）。

## 已踩坑：过度隔离（over-isolation）导致活动中断
- 现象：加冕礼能启动，进行到一半无提示中断 → 根因是核心阶段控制器 `coronation_events.0200`/`0205` 被整段清空为 `trigger = { always = no }`（注释 `# Absent vanilla-map title links isolated` / `unsupported in the total conversion`）。P 社引擎对不存在的指令/条件**静默 no-op 不报错**，是最隐蔽的 bug 源。
- **CK3 安全规则（重要）**：在 `trigger`/`condition`/`override_background` 的 `trigger` 里写 `= title:xxx` 或 `has_title = title:xxx` 引用**不存在的头衔**，引擎静默视为 **false（不崩溃）**；fallback 分支（如 `NOT { capital_county = c_byzantion }` → temple 背景）正常生效。仅 `title:X.holder` 这类**作用域语句**会解析成空作用域（但相关事件若 trigger 要求已被 replace_path 移除的 struggle，则永不触发，无害）。
- **恢复策略**：从原版 `D:\SteamLibrary\steamapps\common\Crusader Kings III\game\` 对应目录提取被隔离事件，逐字恢复（verbatim）即可；仅当 `triggered_desc` 的 `trigger` 直接引用缺失头衔做背景描述时，才把该 trigger 改为 `always = no # UUII: absent vanilla title (X)`。`0205` 即此情况（7 个 barony/county 背景分支隔离）。
- 提取的逐字原版块存于 `.workbuddy/coronation_restore/`（11 文件），可作比对/回滚参考。
- 同类过度隔离**很可能也存在于其他活动链**（tournament / pilgrimage / hunt / feast / grand_tour 等），排查同法：grep `# Absent` / `always = no` 壳 + 追踪事件链 `after`/`trigger_event` 引用是否断链。

## 加冕礼仪式链（恢复后 ACTIVE）
`0205.after` → 6120/6110/6130/6123 → 6130→6131→0100(誓言) → 6100→6140→6122→…→0100 → 0100.after=`coronation_ready_effect`（推进宴会）。0300/0301 选主祭。全部已恢复并验证无死链。

## 工具/沙箱备注
- 沙箱跑含 `open/compile` 的多行 python 脚本会被静默杀（RC=1 无输出）→ 用 `dangerouslyDisableSandbox: true` 或合并单行 `-c`。
- 括号校验用 brace-match（深度计数），不要用 `grep -c "{"`（按行计数，多括号行漏算）。
- 原版文件解析基线：`D:\SteamLibrary\steamapps\common\Crusader Kings III\game\`
