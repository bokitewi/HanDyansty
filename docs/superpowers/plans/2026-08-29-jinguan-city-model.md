# 锦官城特殊模型实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Subagents are not authorized for this task.

**Goal:** 按已批准规格制作成都锦官城三层 LOD 组合模型，并把它作为省份 4282 的 `TK_20_21_JinGuanCheng` 特殊建筑模型接入 HanDyansty。

**Architecture:** 使用 Blender 4.2.23 LTS 和已安装的 `io_pdx_mesh` 扩展建立一个可检查的 `.blend` 制作场景，再导出单一 `hd_jinguan_city.mesh`。模型内部按 LOD 和材质拆分 Shape；建筑几何来自获授权资源与原版桥梁，水面和道路为项目新建平面。脚本侧只替换锦官城的 `asset.name`、给 4282 赋予特殊建筑并增加零实例动态资源注册。

**Tech Stack:** Blender 4.2.23 LTS、`io_pdx_mesh`、CK3 PDX `.mesh/.asset`、DDS、PowerShell、Python `unittest`（仅静态审计，不生成游戏内容）、Clausewitz/Jomini P script。

**Spec:** `docs/superpowers/specs/2026-08-29-jinguan-city-model-design.md`

## Global Constraints

- 只考虑新存档；不处理旧存档兼容。
- 只制作简体中文相关内容；不新增英文文本。
- 禁止启动 CK3 或 Map Editor。
- 不创建子代理、备份仓库、额外分支或工作树。
- 不提交 Git；只在主工作区修改批准范围内的文件。
- LOD0 的来源建筑只允许拆分、旋转、平移和整体等比缩放；不得修改拓扑、UV、材质或贴图。
- 新建几何仅限水面、湖泊面和道路面。
- LOD1、LOD2 可以按批准规格简化。
- 不新增持久化 Python 内容生成器；模型的视觉装配在 Blender 场景中完成，Python 仅用于只读审计。
- 保留所有无关脏工作区改动。

## File Map

**Create source/verification artifacts:**

- `content_source/hd_jinguan_city/reference/chengdu_draft.png`：用户草图的冻结副本，709×476。
- `content_source/hd_jinguan_city/reference/chengdu_draft_manifest.json`：下载草稿 JSON 的冻结副本。
- `content_source/hd_jinguan_city/source_manifest.json`：所有输入 `.mesh/.asset/.dds` 的路径、大小和 SHA-256。
- `content_source/hd_jinguan_city/hd_jinguan_city.blend`：Blender 制作源场景。
- `content_source/hd_jinguan_city/layout_manifest.json`：固定种子、实例类别、变换、源部件和数量。
- `content_source/hd_jinguan_city/test_jinguan_city_contract.py`：只读静态契约审计。
- `content_source/hd_jinguan_city/previews/jinguan_lod0_top.png`：LOD0 正交俯视预览。
- `content_source/hd_jinguan_city/previews/jinguan_lod0_oblique.png`：LOD0 斜视预览。
- `content_source/hd_jinguan_city/previews/jinguan_lod1_oblique.png`：LOD1 斜视预览。
- `content_source/hd_jinguan_city/previews/jinguan_lod2_oblique.png`：LOD2 斜视预览。

**Create runtime assets:**

- `gfx/models/buildings/special/hd_jinguan_city/hd_jinguan_city.mesh`：最终三层 LOD PDX 网格。
- `gfx/models/buildings/special/hd_jinguan_city/hd_jinguan_city.asset`：材质、LOD、裁剪和实体绑定。
- `gfx/models/buildings/special/hd_jinguan_city/*.dds`：仅复制被最终 Shape 引用的获授权来源 DDS。

**Modify existing consumers:**

- `common/buildings/tk_special_buildings.txt:880`：仅替换 `TK_20_21_JinGuanCheng.asset.name`。
- `history/provinces/zz_uuii_generated_county_capitals.txt:42558`：给省份 4282 增加锦官城特殊建筑。
- `gfx/map/map_object_data/special.txt:47`：在现有动态特殊建筑注册区增加锦官城零实例注册。

---

### Task 1: 冻结输入并建立失败优先的静态契约

**Files:**

- Create: `content_source/hd_jinguan_city/reference/chengdu_draft.png`
- Create: `content_source/hd_jinguan_city/reference/chengdu_draft_manifest.json`
- Create: `content_source/hd_jinguan_city/source_manifest.json`
- Create: `content_source/hd_jinguan_city/test_jinguan_city_contract.py`

**Interfaces:**

- Consumes: 当前 ChatGPT 会话中的 709×476 草图、`C:\Users\15550\Downloads\成都城_草稿装配清单.json`、规格列出的来源模型与原版类比资源。
- Produces: 固定输入哈希和 `python test_jinguan_city_contract.py -v` 验证入口，供后续每个任务复跑。

- [x] **Step 1: 从已授权的相邻 ChatGPT 会话保存草图**

  通过浏览器把原始附件保存为 `content_source/hd_jinguan_city/reference/chengdu_draft.png`；不得用截图替代附件原文件。

- [x] **Step 2: 验证草图身份**

  Run:

  ```powershell
  Add-Type -AssemblyName System.Drawing
  $img = [System.Drawing.Image]::FromFile('content_source\hd_jinguan_city\reference\chengdu_draft.png')
  "{0}x{1}" -f $img.Width,$img.Height
  $img.Dispose()
  Get-FileHash -Algorithm SHA256 'content_source\hd_jinguan_city\reference\chengdu_draft.png'
  ```

  Expected: 第一行严格为 `709x476`，并输出稳定 SHA-256。

- [x] **Step 3: 冻结草稿 JSON 并核对组件计数**

  复制下载文件为 `chengdu_draft_manifest.json`，保持字节不变；读取后确认宫殿 2、军营 2、寺院 4、城门 23。明确记录 JSON 不含完整民居、城墙和道路数据。

- [x] **Step 4: 写入来源清单**

  `source_manifest.json` 必须记录：来源绝对路径、用途、字节数、SHA-256、是否复制进模组，以及对应 `.asset` 的材质契约。至少覆盖：

  - `chinese_city_01.mesh`、`chinese_city_02.mesh`
  - `barracks_chinese.mesh`、`monastery_chinese.mesh`
  - `chinese_walls_01.mesh` 至 `chinese_walls_04.mesh`
  - `hd_imperial_palace_placeholder.mesh`
  - `tgp_chinese_bridge_01.mesh`
  - `lake.mesh`
  - 所有最终引用的来源 DDS 与原版 `.asset`

- [x] **Step 5: 写入初始失败测试**

  `test_jinguan_city_contract.py` 使用 `unittest`，初始至少包含以下断言：

  ```python
  def test_runtime_outputs_exist(self):
      self.assertTrue(self.mesh_path.is_file())
      self.assertTrue(self.asset_path.is_file())

  def test_jinguan_consumer_is_unique(self):
      building = self.building_text()
      province = self.province_text()
      special = self.special_text()
      self.assertEqual(building.count('name = "hd_jinguan_city_mesh"'), 1)
      self.assertEqual(province.count('special_building = TK_20_21_JinGuanCheng'), 1)
      self.assertEqual(special.count('pdxmesh="hd_jinguan_city_mesh"'), 1)
  ```

  测试还必须解析 DDS 头、读取 PDX 网格、统计每级 LOD Shape/顶点/三角面/包围盒，并检查新建道路与水体 UV 面积。

- [x] **Step 6: 运行测试并确认按预期失败**

  Run:

  ```powershell
  & 'C:\Users\15550\AppData\Local\Programs\Python\Python38-32\python.exe' 'content_source\hd_jinguan_city\test_jinguan_city_contract.py' -v
  ```

  Expected: `test_runtime_outputs_exist` 因 `hd_jinguan_city.mesh` 尚不存在而失败；不得出现测试脚本语法错误或来源清单解析错误。

### Task 2: 建立 Blender 制作场景和原始部件库

**Files:**

- Create: `content_source/hd_jinguan_city/hd_jinguan_city.blend`
- Modify: `content_source/hd_jinguan_city/layout_manifest.json`

**Interfaces:**

- Consumes: Task 1 冻结的草图、来源清单和 `io_pdx_mesh` 导入器。
- Produces: 尺度统一、材质不变、按用途分 Collection 的 Blender 部件库。

- [x] **Step 1: 启动指定 Blender 与现有 PDX 扩展**

  Run:

  ```powershell
  & 'D:\SteamLibrary\steamapps\common\Blender\blender.exe' --version
  ```

  Expected: `Blender 4.2.23 LTS`。

- [x] **Step 2: 建立 Collection 结构**

  在同一个 `.blend` 中建立：`REFERENCE`、`SOURCE_PARTS`、`LOD0`、`LOD1`、`LOD2`、`MATERIALS`。草图以 40×26.85 单位的正交参考图放入 `REFERENCE`，中心为 X/Z 原点，上方为正 Z。

- [x] **Step 3: 导入来源网格**

  使用已安装的 `io_pdx_mesh` 扩展逐一导入规格中的来源 `.mesh`。导入时启用 mesh、禁用 skeleton/locator、启用相同材质合并。导入后逐个记录 Shape 名、材质索引、包围盒和三角面数。

- [x] **Step 4: 隔离原始建筑部件**

  把建筑结构与来源自带 decal 平面分开；只把结构部件放入 `SOURCE_PARTS`。允许按连通岛拆分墙段、门楼、角楼和民居，但不得编辑岛内顶点、面、UV 或材质槽。

- [x] **Step 5: 保存并回开场景**

  保存 `hd_jinguan_city.blend`，关闭后用 Blender 重新打开，确认所有 Collection、材质槽、参考图尺度和来源部件均存在。

### Task 3: 装配 LOD0 建筑与固定民居布局

**Files:**

- Modify: `content_source/hd_jinguan_city/hd_jinguan_city.blend`
- Create: `content_source/hd_jinguan_city/layout_manifest.json`
- Create: `content_source/hd_jinguan_city/previews/jinguan_lod0_top.png`
- Create: `content_source/hd_jinguan_city/previews/jinguan_lod0_oblique.png`

**Interfaces:**

- Consumes: Task 2 的原始部件库和 40×26.85 坐标映射。
- Produces: 完整 `LOD0` Collection，以及记录每个实例来源、位置、旋转、等比缩放和类别的布局清单。

- [ ] **Step 1: 放置两组宫殿与特殊建筑**

  按草图深紫、红、紫区域放置两组宫殿、两座军营和四座寺院。删除草图上方宫殿外围误画宫墙的对应制作曲线，不给宫殿额外加墙。

- [ ] **Step 2: 沿黑色路径装配城墙**

  使用拆出的直墙、转角和角楼覆盖黑色路径。墙段只允许等比缩放；需要改变长度时改用重复段，不做非等比拉伸。

- [ ] **Step 3: 放置 23 座城门**

  每个蓝色标记对应一座门楼。逐门核对方向与道路连通；`layout_manifest.json` 中 `category = "gate"` 的记录数必须严格为 23。

- [ ] **Step 4: 建立固定民居分布**

  在黄色区域建立 Geometry Nodes 分布，种子固定为 `4282`，实例源集合仅包含 `chinese_city_01`、`chinese_city_02` 与批准的 `chinese_sprawl` 民居部件。先从黄色面中扣除宫殿、军营、寺院、道路、水域、城墙和桥头避让区，再分布点、随机旋转与整体等比尺寸。

- [ ] **Step 5: 冻结实例**

  将 Geometry Nodes 结果 Realize Instances，并把最终实例变换写入 `layout_manifest.json`。再次计算碰撞，任何 X/Z 包围盒在外扩 0.1 单位后相交的民居必须移除或重新放置。

- [ ] **Step 6: 输出两张 LOD0 预览**

  以正交俯视和斜 45 度视角输出工作台渲染。俯视预览必须能与草图对齐检查两宫殿、两军营、四寺院、23 门、墙路水域结构。

### Task 4: 制作水面、道路和中国桥梁

**Files:**

- Modify: `content_source/hd_jinguan_city/hd_jinguan_city.blend`
- Modify: `content_source/hd_jinguan_city/layout_manifest.json`

**Interfaces:**

- Consumes: LOD0 建筑避让区和草图绿色/棕色区域。
- Produces: 独立 `water_LOD0`、`road_LOD0` 与桥梁 Shape，且道路—桥梁—水域关系连续。

- [ ] **Step 1: 描摹并平滑水域**

  把全部绿色区域描摹为闭合面，保持独立湖泊数量和河道连通关系。曲线平滑只移除手绘抖动，不改变总体走向。

- [ ] **Step 2: 三角化水面并建立非零 UV**

  水面使用平面投影 UV；每个三角形 UV 面积必须大于 `1e-8`。水体对象使用单独 PDX 材质槽，命名为 `water_LOD0`。

- [ ] **Step 3: 制作道路带宽面**

  沿所有棕色中心线生成连续道路面，清理自交与重叠三角形。道路对象使用独立 PDX 材质槽，命名为 `road_LOD0`。

- [ ] **Step 4: 放置原版中国桥梁**

  在每个道路—水域交点放置 `tgp_chinese_bridge_01` 原始 LOD0 几何，按道路切线旋转并整体等比缩放。道路面终止于桥头，水面在桥下连续。

- [ ] **Step 5: 运行几何检查**

  在 Blender 中统计水面、道路退化面和零面积 UV；预期均为 0。确认桥梁不悬空、不埋入道路面，且没有非等比缩放。

### Task 5: 制作有效 LOD1 与 LOD2

**Files:**

- Modify: `content_source/hd_jinguan_city/hd_jinguan_city.blend`
- Create: `content_source/hd_jinguan_city/previews/jinguan_lod1_oblique.png`
- Create: `content_source/hd_jinguan_city/previews/jinguan_lod2_oblique.png`

**Interfaces:**

- Consumes: 完整 LOD0 Collection。
- Produces: 满足三角面比例和轮廓要求的 LOD1、LOD2 Collection。

- [ ] **Step 1: 构建 LOD1**

  复制 LOD0 到 LOD1；保留宫殿、城墙、23 门、两军营、四寺院、桥梁、道路和水域识别轮廓。减少民居实例，简化屋顶装饰并移除确定不可见内部面。三角面目标为 LOD0 的 45%–60%。

- [ ] **Step 2: 构建 LOD2**

  从 LOD1 构建 LOD2；保留宫城、外墙、主要城门、桥梁轮廓和城市天际线。民居改为低面数体块，道路和水域减少曲线分段。三角面目标为 LOD0 的 15%–25%。

- [ ] **Step 3: 核对结构保留**

  LOD1 必须仍有 23 个门楼实例；LOD2 必须保留所有主要门洞所在轮廓。任何结构删减不得回写 LOD0。

- [ ] **Step 4: 输出 LOD 预览**

  使用与 LOD0 斜视图完全相同的相机、焦距和分辨率输出 LOD1、LOD2，逐张检查轮廓跳变。

### Task 6: 导出 PDX 网格、复制必要 DDS 并编写 `.asset`

**Files:**

- Create: `gfx/models/buildings/special/hd_jinguan_city/hd_jinguan_city.mesh`
- Create: `gfx/models/buildings/special/hd_jinguan_city/hd_jinguan_city.asset`
- Create: `gfx/models/buildings/special/hd_jinguan_city/*.dds`

**Interfaces:**

- Consumes: Task 5 的三层 LOD 场景与 Task 1 来源哈希。
- Produces: `hd_jinguan_city_mesh` 和 `hd_jinguan_city_entity` 运行时资源。

- [ ] **Step 1: 整理导出对象与名称**

  每个导出对象只含一个 PDX 材质组；对象名按实际用途和 LOD 后缀命名。应用位置、旋转和等比缩放一次，确认没有负缩放和双重世界变换。

- [ ] **Step 2: 导出 `.mesh`**

  在 Blender 中使用 `IOPDX_OT_export_mesh`：mesh 开启、skeleton/locator 关闭、selected 关闭、split vertices 关闭、vertex sort 为升序，并同时导出 plain text 供审计。

  目标路径：

  ```text
  gfx/models/buildings/special/hd_jinguan_city/hd_jinguan_city.mesh
  ```

- [ ] **Step 3: 重新导入新导出的 `.mesh`**

  在一个空 Blender 场景中使用相同版本 `io_pdx_mesh` 重新导入最终 `.mesh`，不得以导出前场景统计代替回读结果。

- [ ] **Step 4: 复制实际引用的来源 DDS**

  只复制最终建筑 Shape 所需的来源 DDS。复制后逐个比较源和目标 SHA-256；任何哈希差异都必须停止。原版水体、道路和桥梁贴图不复制，改用完整游戏资源路径引用。

- [ ] **Step 5: 依据回读 Shape 编写 `.asset`**

  `.asset` 固定包含：

  ```text
  pdxmesh name = hd_jinguan_city_mesh
  file = hd_jinguan_city.mesh
  cull_distance = 300.0
  LOD1 percent = 20.0
  LOD2 percent = 10.0
  entity name = hd_jinguan_city_entity
  ```

  每个 `meshsettings.name/index` 必须抄自回读结果。水面绑定 `lake`/`pdxwater.shader`/`Water`，道路绑定 `decal_local`/`pdxmesh_decal.shader`/`LocalDecals`，建筑与桥梁绑定各自原始材质契约。

- [ ] **Step 6: 运行静态契约测试**

  Run:

  ```powershell
  & 'C:\Users\15550\AppData\Local\Programs\Python\Python38-32\python.exe' 'content_source\hd_jinguan_city\test_jinguan_city_contract.py' -v
  ```

  Expected: 模型、DDS、LOD、Shape 与 UV 测试通过；消费链测试仍因脚本尚未接入而失败。

### Task 7: 接入锦官城建筑与省份 4282

**Files:**

- Modify: `common/buildings/tk_special_buildings.txt:887-890`
- Modify: `history/provinces/zz_uuii_generated_county_capitals.txt:42558-42562`
- Modify: `gfx/map/map_object_data/special.txt:47`

**Interfaces:**

- Consumes: Task 6 的公共 mesh 名 `hd_jinguan_city_mesh`。
- Produces: 唯一的建筑定义—省份历史—动态地图资源消费链。

- [ ] **Step 1: 替换锦官城模型名**

  在 `TK_20_21_JinGuanCheng.asset` 中只把：

  ```text
  name = "tgp_building_special_heian_kyo_mesh"
  ```

  改为：

  ```text
  name = "hd_jinguan_city_mesh"
  ```

- [ ] **Step 2: 给省份 4282 增加特殊建筑**

  在现有 4282 块中增加且只增加：

  ```text
  special_building = TK_20_21_JinGuanCheng
  ```

  不改文化、信仰和 holding。

- [ ] **Step 3: 增加动态地图资源注册**

  在寿春城、邺城注册附近增加：

  ```text
  object={
      name="hd_special_jinguan_city"
      render_pass=MapUnderWater
      clamp_to_water_level=no
      generated_content=no
      layer="temp_layer"
      pdxmesh="hd_jinguan_city_mesh"
      count=0
  }
  ```

  不增加 `transform`，不修改 4282 的 locator。

- [ ] **Step 4: 运行消费链测试**

  Run:

  ```powershell
  & 'C:\Users\15550\AppData\Local\Programs\Python\Python38-32\python.exe' 'content_source\hd_jinguan_city\test_jinguan_city_contract.py' -v
  ```

  Expected: 全部测试通过。

### Task 8: 最终静态审计与交付

**Files:**

- Verify: 本计划 File Map 中的全部文件

**Interfaces:**

- Consumes: 完整模型、资源和消费链。
- Produces: 可核验的静态完成报告，不包含游戏内成功声明。

- [ ] **Step 1: 复跑完整契约测试**

  Run:

  ```powershell
  & 'C:\Users\15550\AppData\Local\Programs\Python\Python38-32\python.exe' 'content_source\hd_jinguan_city\test_jinguan_city_contract.py' -v
  ```

  Expected: `OK`，无 skipped 或 expected failure。

- [ ] **Step 2: 检查文本与差异**

  Run:

  ```powershell
  git diff --check
  git status --short
  rg -n "hd_jinguan_city|TK_20_21_JinGuanCheng" common history gfx content_source -g '*.txt' -g '*.asset' -g '*.json'
  ```

  Expected: `git diff --check` 无输出；所有新增引用能追溯到最终 mesh；无第二个 4282 锦官城赋值。

- [ ] **Step 3: 输出最终证据表**

  报告必须列出：来源与许可、源文件和复制文件 SHA-256、最终 X/Y/Z 边界、原点和 locator、每级 LOD 顶点/三角面/组件/Shape、最大 Shape、材质/着色器/DDS 格式和 Mip、零面积 UV/退化面/负缩放/缺失引用结果，以及预览路径。

- [ ] **Step 4: 明确未验证边界**

  最终报告必须明确：未启动 CK3 或 Map Editor，因此游戏内比例、地形贴合、水体实际渲染、阴影、LOD 切换观感和新存档实际显示均未验证。
