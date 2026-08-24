# 宗族/家族"无成员空壳"检查报告

检查日期：2026-08-24
检查范围：HanDyansty 模组全部 `common/dynasties`、`common/dynasty_houses` 定义与 `history/characters` 角色（含历史角色）

## 检查方法

1. 解析 `common/dynasties/*.txt` 得到全部**宗族（dynasty）定义** 10,523 个
2. 解析 `common/dynasty_houses/*.txt` 得到全部**家族（house）定义** 10,739 个
3. 提取 `history/characters/*.txt` 中所有角色的 `dynasty_house = "xxx"` 引用（10,470 处）
4. 差集计算：**定义了但没有任何角色（含历史角色）引用**的宗族/家族
5. 额外校验三类悬空引用（house→dynasty、角色→house、角色→dynasty）

## 总体结论

| 类别 | 家族(house) | 宗族(dynasty) |
|---|---|---|
| 定义总数 | 10,739 | 10,518 |
| 无任何角色引用 | 1,425 | 1,433 |
| └ 百家姓氏池（设计用途） | 1,421 | 1,428 |
| └ 刻意保留条目 | 0 | 2 |
| └ **疑似孤儿/废弃残留** | **4** | **3** |

**存在"无成员、无历史成员、无任何成员但仍存在于游戏数据中"的条目**，但绝大多数是设计使然；真正可疑的目前剩 4 个家族 + 3 个宗族，详见下文（C2 已于 2026-08-24 处理完毕）。

---

## A. 百家姓氏池（设计用途，非问题）

- `house_baijia1~504`（504 个）+ `house_xin1~917`（917 个）家族
- `baijia1~504`（504 个）+ `xin1~924`（924 个）宗族

这些是《百家姓》/《新百家姓》**随机姓氏池**，本地化如 `dynn_baijia1 = "赵"`、`dynn_xin1 = "吉白"`。游戏运行时随机生成的角色会按文化从池中取姓，**当前无静态成员是预期状态**，无需处理。

## B. 刻意保留条目（非问题）

- `100848`（dynn_Tikanariyen）：原版宗族
- `1029001`（dynn_Prydain）：注释明确写明 *"Keeping Prydain to dodge a stubborn error"*（刻意保留规避报错）

## C. 疑似孤儿/废弃残留（建议处理）

### C1. 黄巾体系：张曼成宗族（1 宗族 + 1 家族）

| ID | 来源文件 |
|---|---|
| `dynasty_hd_zhang_mancheng` | common/dynasties/zz_hd_yellow_turban_dynasties.txt |
| `house_hd_zhang_mancheng` | common/dynasty_houses/zz_hd_yellow_turban_houses.txt |

- 本地化已配齐：宗族/家族名均为"张"
- **现象**：黄巾领袖张曼成角色（`zhang_man_cheng`，east_asian_han_dead_before_180.txt:14291）实际挂在 `dynasty_house = "uuii_book_house_bed19398c5c0"`（书史体系自动生成的"张"氏家族）下，而手工定义的这套宗族/家族没有任何角色挂载
- **判定**：`zz_hd_yellow_turban_effects.txt` 脚本仍引用 `character:zhang_man_cheng`，角色存在但关联到了别家——手工宗族成为孤儿
- **建议**：二选一——① 将 `zhang_man_cheng` 的 `dynasty_house` 改为 `house_hd_zhang_mancheng`（恢复手工体系）；② 删除这两个定义（保留书史体系）

### C2. 农民体系：曹氏/夏侯氏废弃备用宗族（5 个宗族）—— ✅ 已删除（2026-08-24）

| ID | 姓氏 | 状态 |
|---|---|---|
| `dyn_111010026001002` | 曹（谯郡曹氏） | ✅ 已从 uuii_peasant_historical_dynasties.txt 删除 |
| `dyn_111010026002002` | 曹（谯郡曹氏） | ✅ 同上 |
| `dyn_111010026003002` | 曹 | ✅ 同上 |
| `dyn_111010026004002` | 曹 | ✅ 同上 |
| `dyn_111010819001002` | 夏侯（谯郡夏侯氏） | ✅ 同上 |

- 原现象：name 均为 `"111010026000001_Cao"` / `"111010819000001_XiaHou"` 格式（备用变体），**无任何 house 挂靠、无任何角色引用**；定义内部 `dynasty = "dyn_111010026000001"` 关联被注释掉，而该主宗 ID 在 dynasty 定义文件中**并不存在**（悬空注释）
- 处理记录：两处引用同时删除——① `common/dynasties/uuii_peasant_historical_dynasties.txt`（宗族定义，26 行）；② `common/coat_of_arms/coat_of_arms/zz_dm_bce_generated_family_coas.txt`（家徽定义，含注释 135 行）。备份：两份文件 `.bak_20260824_105623`
- 处理后验证：全模组无残留引用、括号平衡 OK、空宗族总数 1,438 → 1,433、空家族数不变

### C3. 书史体系（uuii_book_*）：孤宗 + 孤分家（2 宗族 + 3 家族）

| 孤宗 | 姓氏 | 孤分家(house) | 来源文件 |
|---|---|---|---|
| `uuii_book_dyn_9abdb3f599ee` | 刘 | `uuii_book_house_4da8cbcd9186`（分家名误用宗族名） | uuii_book_historical_*.txt |
| `uuii_book_dyn_cdae1c314e2f` | （汉） | `uuii_book_house_d867ee0b4caa` | 同上 |
| — | 夏侯 | `uuii_book_house_51e4d4ade4f3`（挂在 `uuii_book_dyn_cao_xiahou` 下，分家名与宗族名相同"夏侯"，疑复制粘贴） | 同上 |

- **判定**：书史体系绝大部分宗族/家族都有角色挂载，仅这 3 个分家 + 2 个宗族无角色，疑似全量生成时的个别遗漏
- **建议**：人工核对《刘》《夏侯》等氏族是否有对应角色应挂载；无则应删除

---

## D. 悬空引用检查（全部通过 ✓）

| 检查项 | 结果 |
|---|---|
| 家族定义引用的宗族不存在 | 无 |
| 角色引用的家族不存在 | 无 |
| 角色直接引用的宗族不存在 | 无 |

模组内部引用链完整，孤儿条目不会导致加载报错或崩溃。

## 附录

- 完整空壳清单（1,425 家族 + 1,433 宗族，2026-08-24 已更新）：`tools/empty_dynasty_report.txt`
- 检查脚本（可复用）：`tools/check_empty_dynasties.py`
- 块删除工具（可复用）：`tools/remove_dyn_blocks.py`
