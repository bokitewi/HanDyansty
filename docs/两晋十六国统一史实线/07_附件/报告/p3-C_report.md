# p3-C 最终报告（修正后合并版）

## p3-C「世族与朝官」修正报告

本轮只改了暂存区：没有直接写 mod，没有跑生成器，没有开游戏，也没有提交 git。暂存任务名 `p3-C`。

### 一、逐条处理结果

**1. major：22 行新增世族头衔缺政体和继承法——已修**
- 改的是暂存的 `history/titles/zz_hd_304_titles.txt` 第 2394–2415 行，共 22 行 `c_nf_*` 的 304.11.20 授予，包括新建的 `c_nf_hedong_pei` 和 `c_nf_kuaiji_he`。
- 每行在 `liege = X` 之后补上 `government = celestial_government succession_laws = { noble_family_succession_law }`。
  - 政体照 346 `c_nf_zhuojun_liu`、404 `c_nf_jiyang_cai` 的单行写法。
  - 继承法照 integrated 基底，例如 `c_nf_wujun_gu` 346.1.1 那条。
  - 已确认 `noble_family_succession_law` 在原版和 mod 的 `common/laws/01_title_succession_laws.txt` 里都有定义。
- 修改用脚本逐行匹配，断言每行只替换 1 处，共替换 22 行。文件仍是 UTF-8 带 BOM、LF。
- 三个 `c_hd_nf` 键（范阳卢、弘农杨、京兆杜）有 184 基底兜着，按审查意见没动。
- 撤销文件也没动：304.11.21 已撤成 `holder = 0`，346.1.1 基底会再设一次政体和继承法。

**2. minor：吐谷浑储君不一定设得上——不改代码，加实测项**
- `d_tuyuhun` 是 nomad 政体，如果它的继承法没有 `can_designate_heirs`，`set_designated_heir` 可能不生效。
- 吐延是 247346 唯一的儿子，按默认继承也由他继承，所以结果不受影响。
- 实测项见第五节第 6 条第 7 项。

**3. minor：取高邑用 usurped 型转移，赵国郡守可能对颖有篡夺类恶感——暂不改，加实测项**
- 偏差本身等汇总人确认，见第五节第 1 条。
- 实测时看赵国郡守对颖的好感：有篡夺类惩罚的话，改用别的转移类型，或者接受。见第五节第 6 条第 8 项。

**4. 报告瑕疵：「末尾新增 6 个效果」——已更正为 5 个**，见第二节。

**5. §6.3 第 5 步（吐谷浑文化）——已由审查人核过，无问题**
- 两人库文化都是 `tuyuhun`。
- `hd_nbc_assign_culture_effect` 只处理 xianbei 和 xiongnu，不会改吐谷浑文化。原实测项里的这一条已删掉。

### 二、文件清单

暂存副本在 `D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p3-C\files\`，共 6 个文件。改现有文件和新建文件都是 UTF-8 带 BOM、LF；两个 history/titles 文件是在动笔前一刻才 `stage edit` 的。

**改 3 个现有文件**
- `common/scripted_effects/zz_hd_j16_startup_304_effects.txt`
  - 入口 `hd_j16_startup_304_effect` 在 3-A 八王装配之后追加 4 段调用，3-A 原有的段没动。
  - 文件末尾新增 5 个效果：
    - `hd_j16_304c_ying_lose_ye_effect`（颖失邺）
    - `hd_j16_304c_court_offices_effect`（朝官）
    - `hd_j16_304c_minister_effect`（授官薄壳）
    - `hd_j16_304c_court_place_effect`（宫廷安置）
    - `hd_j16_304c_tuyuhun_heir_effect`（吐谷浑储君）
- `history/titles/zz_hd_304_titles.txt`
  - 改写 3 行现有的 `304.11.20 holder = 0`：
    - 范阳卢 `c_hd_nf_famous_h_house_111010165001013`
    - 弘农杨 `c_hd_nf_famous_h_house_111010016007013`
    - 京兆杜 `c_hd_nf_famous_h_uuii_book_house_f8bdf3d26e54`
  - 同段末尾新增 22 行 `c_nf_*` 授予。本轮给这 22 行补了政体和继承法。
- `history/titles/zz_hd_304_undo.txt`：22 个新增键各补一行 `304.11.21 = { holder = 0 }`。

**新建 3 个**
- `common/landed_titles/zz_hd_j16_noble_titles.txt`
  - `c_nf_hedong_pei`，首府闻喜 `c_uuii_p_2453`。
  - `c_nf_kuaiji_he`，首府山阴 `c_uuii_p_6471`。
  - 结构照抄 `zz_hd_nbc_noble_families.txt`。文件内自定义了 `@hd_j16_nf_never_primary = -1000`。
- `localization/simp_chinese/zz_hd_j16_304c_l_simp_chinese.yml` 和 `localization/english/zz_hd_j16_304c_l_english.yml`：中英各 2 键，一一对应。

### 三、闸门结果

修正后复跑 `gate.py --overlay p3-C --compare baseline.json --only-changed`：
- errors 0，counts 为空，相对基线没有新增。
- overlay 读到 6 个文件。
- 输出在 `D:\Temp\claude\E--documents-Paradox-Interactive-Crusader-Kings-III-mod-HanDyansty\1a9fd535-720a-4cbe-ba72-76d6e91ee4f8\scratchpad\stage\p3-C_gate.txt`。

### 四、自拟与偏差（更新后）

1. **颖保底县（偏离任务字面）。**
   - 颖开局直接持有的县只有魏郡 8 县，与 `d_weijun` 法理 8 县完全一致。照字面全部转走，颖会一县不剩。这与决定 3「颖仍有地」相违，3-A 的 B3 执行体也是按颖有地写的。
   - 做法：先从赵国郡守手里取高邑 `c_uuii_p_4258` 给颖。高邑是 `k_uuii_jizhou` 的法理首府，不是赵郡郡治（郡治是 `c_uuii_p_287`）。
   - 然后用 `set_realm_capital` 把颖的首府迁到高邑，再把 `d_weijun` 及辖县转给天子直辖。
   - 取不到高邑时整段不做，记 `SKIP ying_lose_ye_no_keep_county`。
2. **只有颖失邺包在史实事件规则开关里。** 朝官授予、宫廷安置、吐谷浑储君不受开关控制，算开局数据，有 346 `hd_nbc_ministers_effect` 的先例。
3. 「为将」用 `set_knight_status = force` 落实。
4. 诸葛氏只授 `c_nf_langya_zhuge`。`c_hd_nf_langya_zhuge` 在 304、346、404 都是空的，不授。
5. 世族头衔照 346 先例，没有加「无 TGP 时销毁头衔」的效果。22 行无基底的头衔已照 346、404 无基底先例补了政体和继承法（本轮）。
6. 魏郡下属县如果改投天子，该下属的全部领地会一并转过去。开局时没有这种情况（审查已核实）。
7. 太原王氏不授（00 §6「核不清不授」）。三个「Wang of Taiyuan」键的历史持有人都不属于王承所在的 jinyang_wang 一系。

### 五、需汇总人处理

1. **颖保底县的偏差**（第四节第 1 条），请确认。确认后会有两个连带结果：
   - B3 走「颖有地」分支，给颖 5000 兵并让他对魏郡宣称；
   - B7 不会触发，与决定 3 记下的局限一致。
2. **3-D 颖卡**：taidi、yexia 两个主目标要求持 `d_weijun`，开局第 2 天就不成立，符合 02 §5。
3. **3-D 越卡**：smyue_yingjia 的 b1 用 `hd_asp3_subject_trigger` 判「苟晞在麾下」，这个触发器把廷臣也算进去。苟晞开局就入越宫廷，所以 b1 开局即成立，按 D56 可能永远不发奖。请 3-D 或汇总人定夺。审查已核实属实。
4. **司徒接任**：王戎 305.7.11 卒后由温羡（`taiyuan_wen_005`）接司徒。这要在运行时做，请交 3-B1，或另行指定人做（例如加一个节点）。
5. **D 盘 gen304.py 在仓库外**：重跑它会冲掉本轮对两个头衔文件的改动，包括本轮补的政体和继承法。
6. **实测项**：
   1. AI 天子会不会把魏郡另行分封（会的话，决议 E 的「邺属天子」条件就失效了）；
   2. 天子直辖县超出上限后的表现；
   3. 世族家主带着非天子的 liege 时是否正常（越、颖、颙、刘弘）；
   4. 高邑转给颖、迁首府是否成功，看日志 `ying_keep_gaoyi`；
   5. 没有 TGP 的玩家，世族头衔怎么处理；
   6. 304 开局时 22 个 `c_nf_*` 的政体是否显示为天朝政体，继承法是否为 noble_family（本轮新增）；
   7. 吐谷浑的指定储君是否显示为吐延 247347（本轮新增）；
   8. 赵国郡守对颖有没有篡夺类负面好感，有的话改用别的转移类型或接受（本轮新增）。

### 六、本期面板行清单（交 F-1）

无。本路只做开局装配，没有节点 fire。

### 七、新增事件号、变量名

- 事件号：无。
- 全局变量、人物变量：无。
- 新增 scope：`hd_j16_yl_ying`、`hd_j16_yl_tz`、`hd_j16_yl_cap`、`hd_j16_yl_change`、`hd_j16_yl_c`、`hd_j16_cp_gx`、`hd_j16_cp_wm`；另沿用 `councillor_liege`。
- 新头衔键：`c_nf_hedong_pei`、`c_nf_kuaiji_he`。
- 日志：`HD_J16 startup_304 FIRE ying_keep_gaoyi`、`FIRE ying_lose_ye`、`SKIP ying_lose_ye_no_keep_county`、`SKIP minister_<ID>`。
- 02 编号式旧名 → 语义名：本路不涉及。

### 八、卒年表 PRE 变量的设置处

本路不设任何 PRE。gen_deaths.py 读的是 mod，所以改为 grep 暂存副本核对：暂存副本里的 `set_global_variable` / `set_variable` 只有 3-A 原有的 4 处，分别是 `hd_hi_done_liuyu`、`hd_hi_done_luxun`、`hd_j16_bawang_active`、`hd_j16_zhangfang_general`。卒年表第 8 列的 PRE 也没有一项归 3-C。

### 九、仍未解决

- 第五节第 1、3、4 条等汇总人定夺。
- 第五节第 6 条只能进游戏实测。
- 审查的两个 minor 按建议没改代码，只加了实测项。