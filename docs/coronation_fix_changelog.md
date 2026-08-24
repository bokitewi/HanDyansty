# 加冕礼（Coronation）活动中断修复 — 变更记录

**日期**：2026-08-24
**问题**：加冕礼能正常触发启动，但进行到一半（进入"加冕"阶段）时自动中断、无任何提示。

## 根因
模组是汉总转换（TC），`descriptor.mod` 用 `replace_path` 替换了 `landed_titles` / `history/titles` / `map_data` / `common/struggle/struggles` 等，导致原版地图头衔（`c_byzantion`、`b_aachen`、`b_constantinople`、`b_krakow`、`b_london`、`b_paris`、`b_reims`、`b_vaticano`、`e_byzantium`、`b_roma`、`d_sunni` 等）与 `struggle:persian_struggle` 在 TC 中**完全不存在**。

为兼容，模组把引用这些头衔的事件整段清空为 `trigger = { always = no }`（注释 `# Absent vanilla-map title links isolated` / `unsupported in the total conversion`）。问题是**过度隔离**——把加冕礼的两个核心阶段控制器也一起清空了：

- `coronation_events.0200`（前奏阶段开始，负责选主祭 officiator）被清空 → 主祭永远选不出
- `coronation_events.0205`（加冕阶段开始，负责触发整条仪式链）被清空 → 进入加冕阶段后无任何仪式内容，空转后直接跳到宴会，表现为"中途无提示中断"

P 社引擎对不存在的指令/条件**静默 no-op 不报错**，因此不会在 `error.log` 留下任何痕迹，是最隐蔽的 bug 源。

## 修复策略
采用"完整恢复仪式链"：从原版 `game/events/activities/coronation_activity/` 提取被隔离事件，恢复到模组。

**关键安全判定**：在 CK3 中，`trigger` / `condition` / `override_background` 的 `trigger` 里引用不存在头衔（如 `= title:c_byzantion`、`has_title = title:d_sunni`）会静默视为 **false（不崩溃）**，fallback 分支（如 `NOT { capital_county = c_byzantion }` → temple 背景）正常生效。因此绝大多数事件可**逐字恢复（verbatim）**；仅 `0205` 中 7 个直接引用缺失头衔做背景描述的 `triggered_desc` 分支改为 `always = no`，保留所有核心 `immediate` / `option` / `after` 逻辑（含 east_asian 分支，对汉模组尤为重要）。

## 恢复的 events（全部已验证括号平衡、ACTIVE、无死链）
| 文件 | Event | 处理方式 |
|------|-------|----------|
| `coronation_events.txt` | `0200`（前奏/选主祭） | c_byzantion 背景分支隔离，其余逐字恢复 |
| `coronation_events.txt` | `0205_audience` 触发器 | 恢复完整 NOR 逻辑（原本 `always = no`） |
| `coronation_events.txt` | `0205`（加冕开始） | 7 个缺失头衔 `triggered_desc` → `always = no`，其余逐字恢复 |
| `coronation_events_6.txt` | `6100` `6110` `6120` `6122` `6130` `6140` | 逐字恢复 |
| `coronation_events_1.txt` | `1007` | 逐字恢复（c_byzantion 比较，安全） |
| `coronation_events_klank.txt` | `klank.1010` | 逐字恢复（trigger 要求 struggle:persian_struggle，TC 中永不触发，无害） |

> 注：`6121`（原本未隔离，已 ACTIVE）、`0300`/`0301`（主祭选择，已 ACTIVE）无需改动。

## 链式验证结果
脚本扫描全部 `id = coronation_events.X` 引用，确认链路完整且无残留 `always = no` 死链：

```
0205.after → 6120 / 6110 / 6130 / 6123
6130 → 6131 → 0100（誓言）
6100 → 6140 → 6122 → … → 0100
0100.after = coronation_ready_effect  （推进到宴会阶段，活动正常完成）
```

## 本地化
模组未 `replace_path` 任何 localization，且不自带 coronation 本地化 → 继承原版 `coronation_activity_l_*.yml`（含全部 `0205`/`6100`/… 键），无需补本地化。

## 回滚参考
原版逐字事件块已存于 `.workbuddy/coronation_restore/`（11 个文件），可供后续比对/回滚。

## 后续建议
同类"过度隔离"很可能也存在于其他活动链（tournament / pilgrimage / hunt / feast / grand_tour 等）。排查方法：在 `events/activities/` 下 `grep "Absent vanilla-map title links isolated"` 与 `trigger = { always = no }` 壳，并追踪事件链 `after` / `trigger_event` 引用是否断链。
