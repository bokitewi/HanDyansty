# 头衔有效性检查报告

> 检查目标：找出「本应该有地、但实际无地」的无效头衔。
> 依据：`descriptor.mod` 使用了 `replace_path="common/landed_titles"` 与 `replace_path="history/titles"`，
> 即本模组完全替换原版头衔定义与历史（无 fallback）。因此「在 landed_titles 中定义了，却在 history/titles 里
> 没有 holder」的头衔，就是真正的无地头衔。

## 一、总体数据

| 项目 | 数量 |
|------|------|
| landed_titles 定义的头衔总数 | 9216 |
| ├─ 帝国 (e_) | 18 |
| ├─ 王国 (k_) | 44 |
| ├─ 公国 (d_) | 295 |
| ├─ 伯爵领 (c_) | 2038 |
| └─ 男爵领 (b_) | 6820 |
| landless = yes 的无地头衔（故意设计） | 189 |

---

## 二、⚠️ 明确的问题头衔（建议修复）

### A1. 完全「死地」county —— 13 个（无 holder、无 government、无 liege）

这些 county 在 `history/titles` 中只有 `change_development_level`，没有任何持有者、政体或领主。
它们在游戏开始时会成为地图上的**无人区**（灰色空地），无法被统治、无法提供税收/征召。

| county | 所在公国（父头衔） |
|--------|-------------------|
| c_bailan | d_golong |
| c_baitu | d_xiping |
| c_fusi | d_fusi |
| c_gande | d_golong |
| c_haix | k_tuyuhun |
| c_huang | d_golong |
| c_jiaqiu | d_bianhan |
| c_nanmut | d_golong |
| c_tianjun | (无父头衔) |
| c_tiekui | k_tuyuhun |
| c_tuosu | k_tuyuhun |
| c_tuyuhun | k_tuyuhun |
| c_wanxiucheng | d_xiping |

### A2. 有归属公国、但无人统治的 county —— 19 个（有 liege，无 holder 无 government）

这些 county 已经声明了 `liege = d_xxx`（归属于某公国），却漏写了 `holder` 与 `government`，
属于**最典型的「本应有地却无地」**：公国圈住了它，但没人真正持有它。

| county | liege（归属公国） |
|--------|-------------------|
| c_fangcheng1 | d_wudou |
| c_gnan | d_longxi |
| c_guandong | d_long1 |
| c_jiangchuan1 | d_yinping1 |
| c_juchenbg1 | d_yinping1 |
| c_maling | d_anding |
| c_qianer | d_beidi |
| c_qingfeng | d_wudou |
| c_qishan1 | d_wudou |
| c_shendu | d_taoxi1 |
| c_uuii_p_1303 | d_xihe_sili |
| c_uuii_p_1324 | d_yunzhong |
| c_uuii_p_1325 | d_yunzhong |
| c_uuii_p_1331 | d_yunzhong |
| c_uuii_p_1338 | d_yunzhong |
| c_uuii_p_2660 | d_yunzhong |
| c_uuii_p_2670 | d_dingxiang |
| c_uuii_p_2674 | d_dingxiang |
| c_wujie | d_yinping1 |

### A3. 有政体有归属、但漏写 holder 的公国 —— 4 个

| 公国 | 情况 |
|------|------|
| d_taibei | 历史条目是空的 `184.1.1 = { }`，完全无内容（最明显） |
| d_fuyu | `celestial_government` + `liege = k_uuii_youzhou`，但无 holder |
| d_gaojuli | `celestial_government`，无 holder |
| d_xiwuhuan | `celestial_government` + `liege = k_uuii_youzhou`，但无 holder |

---

## 三、⚠️ 需要你确认的「疑似问题」（可能是设计）

### B. holder = 0 的 county —— 871 个

历史中明确写了 `holder = 0`（无主），但都有 government：

| government | 数量 |
|-----------|------|
| celestial_government | 743 |
| tribal_government | 124 |
| kuzhu_warlord_government | 3 |
| nomad_government | 1 |

> 这些 county 占全部 county（2038）的 **43%**。它们有政体、有 liege，但 `holder = 0`。
> 若模组没有「行政任命 / 太守代管」机制在开局自动填补 holder，它们会在地图上显示为无主空地。
> 我检索了 `on_action/` 与 `scripted_effects/` 的 startup 流程，**未发现**针对这些 holder=0 county 的自动填补逻辑
> （`hd_han_setup_184_court_effect` 只处理朝廷九卿/三公职务，不涉及 county holder）。
> **建议确认：这是否是「朝廷直辖 / 东汉末年太守空缺」的有意设计？**

### C. 只有 government、无 holder 的 county —— 241 个

| government | 数量 | 性质判断 |
|-----------|------|---------|
| nomad_government | 107 | 游牧空地，多半是设计 |
| tribal_government | 55 | 部落空地，多半是设计 |
| hd_yeren_government | 36 | 「野人」地（日本/北海道），多半是设计 |
| **feudal_government** | **41** | **封建空地，值得排查** |
| **celestial_government** | **2** | **天朝空地，值得排查** |

---

## 四、非问题（故意设计，无需处理）

- **189 个 `landless = yes` 的无地头衔**：CK3「无地头衔」机制（Tours & Tournaments 及后续 DLC），
  用于表现「著名贵族家族」（`c_hd_nf_famous_p_*` / `c_hd_nf_famous_h_*`）与黄巾/义军营地（`d_hd_yt_*`、`d_hd_*_bandits`）。
- **约 120 个无历史的 d_/k_/e_ 头衔**：可创建（formable）头衔，如百济、高句丽、鲜卑、蒙古高原诸部等，
  玩家可通过决议创建，无需开局 holder。

---

## 五、结论与建议

1. **优先修复 A1 + A2 + A3 共 36 个头衔**：这些是明确的「本应有地却无地」，几乎可以肯定是漏写。
   建议参照同文件的正常 county（如 `c_shicheng`、`c_xiangwu1`）补上 `holder = hd_fictional_governor_<公国>_184`、
   `government = celestial_government`（或相应政体）。
2. **核实 B 类 871 个 holder=0**：若为设计请忽略；若非设计，需补 holder 或确认行政任命机制会填补。
3. **排查 C 类中 41 个 feudal + 2 个 celestial 空地**：封建/天朝政体的 county 不应是空地，可能是漏写 holder。

> 原始明细见 `tools/landless_titles_report.txt`；检查脚本为 `tools/check_landless_titles.py`。
