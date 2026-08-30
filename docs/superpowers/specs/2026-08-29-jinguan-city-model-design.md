# 锦官城特殊模型设计规格

日期：2026-08-29

目标模组：HanDyansty

目标存档：仅新存档

目标语言：仅简体中文

运行时验证：禁止启动游戏

## 1. 目标

为省份 4282 的 `TK_20_21_JinGuanCheng` 制作一套独立的成都锦官城地图特殊建筑模型。模型必须按用户提供的 709×476 草图重建城墙、城门、宫殿、民居、军营、寺院、水域、道路和桥梁，并优先复用已确认获准再发布的中国建筑资源及 CK3 原版同类资源。

最终采用单一组合实体方案：游戏只消费一个 `hd_jinguan_city_mesh`，内部按 LOD、用途和材质划分 Shape。不得额外放置一个永久静态成都城实体，以免与特殊建筑系统重复显示。

## 2. 已批准的约束

- 允许从源 `.mesh` 中拆取原始松散部件并重复使用。
- 允许对每个实例进行旋转、平移和整体等比缩放。
- LOD0 不得修改建筑部件的拓扑、UV、材质或贴图，不得跨源部件焊接顶点。
- 允许为 LOD1、LOD2 制作几何简化副本。
- 允许把草图中的绿色和棕色手绘区域整理为平滑水域轮廓与道路中心线，但必须保持总体位置、走向、数量和连接关系。
- 水面、湖泊面和道路面属于本项目允许新建的几何。
- 水域和道路必须使用 CK3 原版水体及城市道路材质。
- 道路穿越水域的位置必须使用原版中国桥梁。
- 民居使用固定随机种子进行混合布置，结果必须可重复。
- `F:\开源建筑\chinese` 的复制、拆分和随模组再发布许可已由用户确认。
- 不处理旧存档兼容，不制作英文文本，不启动游戏，不创建备份仓库或额外工作树。

## 3. 资料优先级

布局判断按以下优先级执行：

1. 用户在本任务中的明确说明与批准；
2. 用户提供的 709×476 成都草图；
3. 本规格中冻结的数量、位置关系和资源映射；
4. 下载的草稿 JSON，仅作为已标注区域的辅助坐标。

草稿 JSON 不包含完整民居、城墙和道路信息，因此不得把它当成可直接生成整座城市的完整清单。缺失部分必须以原始草图为准进行清理和描摹。

## 4. 已研究的原版实现

实现和 `.asset` 绑定以当前安装版本中的下列同类资源为基准：

- `D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\models\buildings\special\tgp\tgp_building_special_changan.asset`
- `D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\models\buildings\special\tgp\tgp_building_special_changan.mesh`
- `D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\map\map_object_data\changan_building.txt`
- `D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\models\buildings\holdings\tgp\tgp_building_chinese_city_01.asset`
- `D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\models\mapitems\lakes\lake.asset`
- `D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\models\mapitems\lakes\lake.mesh`
- 原版 `tgp_chinese_bridge_01` 的 `.asset`、`.mesh` 和材质资源。

原版长安模型的总体占地约为 39.74×40.27 个地图单位，使用 `cull_distance = 300.0`。锦官城使用同一量级的可视范围，但按照草图宽高比构建为约 40×26.85 个地图单位。

## 5. 来源资源映射

### 5.1 宫殿

- 来源：模组现有 `gfx/models/buildings/special/hd_imperial_palace_placeholder/hd_imperial_palace_placeholder.mesh`。
- 数量：两组。
- 草图中上方宫殿外额外画出的宫墙不制作，因为宫殿模型已经自带宫墙。
- 原模型三个 LOD 当前几何相同；本项目为组合模型单独制作有效的 LOD1、LOD2，不能继续重复同一高模。

### 5.2 城墙与城门

- 来源：`F:\开源建筑\chinese\chinese_walls_01` 至 `chinese_walls_04`。
- 从完整城墙组中拆取原始直墙、转角、角楼和门楼，不整体重复使用完整城墙城市。
- 按草图黑色城墙路径重排。
- 按草图的 23 个蓝色标记放置 23 座城门；城门朝向必须与所在线段和道路方向一致。

### 5.3 民居

- 来源：`chinese_city_01`、`chinese_city_02`、`chinese_sprawl` 中的原始建筑部件。
- 只在黄色居住区内布置。
- 固定随机种子为 `4282`。
- 候选建筑必须避让宫殿、军营、寺院、城墙、水域、道路和桥头。
- 碰撞边界按各来源实例的实际 X/Z 包围盒外扩 0.1 个地图单位计算。
- 通过旋转、平移和整体等比缩放制造变化；不得进行非等比拉伸。
- 最终实例布局冻结进组合网格，重复执行同一制作流程时必须得到相同的实例清单。

### 5.4 军营与寺院

- 军营来源：`chinese_sprawl` 的 `barracks_chinese_mesh`，数量两座。
- 寺院来源：`chinese_sprawl` 的 `monastery_chinese_mesh`，数量四座。
- 严格保持草图中的红色和紫色标注位置关系。
- 不复制 `chinese_sprawl_main_assets.asset` 中错误重复命名的 outpost 实体定义。

### 5.5 水域

- 草图中的所有绿色区域均生成独立的河流或湖泊平面。
- 水域轮廓可以平滑，但不得改变水域之间的连通关系，也不得移除独立湖泊。
- 水体材质严格采用原版湖泊契约：
  - `shader = "lake"`
  - `shader_file = "gfx/FX/pdxwater.shader"`
  - `subpass = Water`
  - `texture_diffuse = "nodiffuse.dds"`
  - `texture_normal = "nonormal.dds"`
  - `texture_specular = "nospec.dds"`
- 水体实际颜色、法线和流动效果由游戏原版全局水体资源提供，不制作自定义水贴图。

### 5.6 道路

- 沿草图全部棕色线条建立带宽道路面，平滑手绘抖动并保留原有路线和连接关系。
- 使用原版中国城市同类地面 decal 契约：
  - `western_city_01_decal_diffuse.dds`
  - `western_city_01_decal_normal.dds`
  - `western_city_01_decal_properties.dds`
  - `shader = "decal_local"`
  - `shader_file = "gfx/FX/pdxmesh_decal.shader"`
  - `subpass = "LocalDecals"`
- 道路在桥头连续衔接，但不得把道路平面铺到桥面上方造成闪烁。

### 5.7 桥梁

- 道路与水域相交处使用原版 `tgp_chinese_bridge_01`。
- LOD0 保留原版桥梁几何，只允许旋转、平移和整体等比缩放。
- 桥下水面连续，桥头与道路边缘连续。

## 6. 坐标、比例与层次

- 草图横向 709 像素映射为 40 个地图单位；纵向按同一比例映射为约 26.85 个地图单位。
- 草图中心映射到组合模型 X/Z 平面的原点；草图上方映射为正 Z。
- 组合模型原点设在整座城市几何中心，而不是某个单独建筑的中心。
- 建筑底部统一到地面基准，保留来源模型自身的竖直比例。
- 道路、水面和建筑地面层使用同类原版资源的相对高度规则，并采用最小必要偏移避免 Z-fighting。
- 特殊建筑 locator 保持比例 `{ 1, 1, 1 }`。最终地图尺度由组合模型自身决定，不使用 locator 进行二次非等比调整。

## 7. Shape 与材质组织

- 最终只有一个 `hd_jinguan_city.mesh`，其中包含 LOD0、LOD1、LOD2。
- 按 LOD 和实际材质分 Shape；相同材质的多个实例可以汇入同一个 Shape 以减少 draw call。
- 汇入只合并索引与顶点数据容器，不跨原始部件焊接顶点，也不重新展开 UV。
- 水体和道路必须各自保持独立 Shape，以便绑定 Water 与 LocalDecals 子通道。
- Shape 名称、Shape 内材质索引和 `.asset` 的 `meshsettings` 只能依据最终 PDX 回读结果填写，不得依据预期手写。
- 所有源 DDS 保持原格式、Mip、alpha 和 packed 通道；禁止重新压缩。

## 8. LOD 与可视范围

### LOD0

- 完整保留两组宫殿、城墙、23 座城门、两座军营、四座寺院、全部桥梁及确定性生成的民居。
- 来源建筑几何不简化，不改变拓扑、UV、材质和贴图。
- 新建几何仅限水域与道路。

### LOD1

- 保留宫殿、城墙、城门、军营、寺院、桥梁、道路和水域的识别轮廓。
- 减少民居数量，简化屋顶装饰，删除确定不可见的内部面。
- 三角面目标为 LOD0 的 45% 至 60%。

### LOD2

- 保留宫城、外墙、主要城门、桥梁轮廓与城区天际线。
- 用低面数建筑体块表现密集民居，并减少道路和水域曲线分段。
- 三角面目标为 LOD0 的 15% 至 25%。

### 切换与裁剪

- `lod_percentages` 采用当前 TGP 中国/亚洲大型地图建筑常用配置：LOD1 为 `20.0`，LOD2 为 `10.0`。
- `cull_distance = 300.0`，与原版长安特殊模型一致。

## 9. 游戏资源文件

新增目录：

`gfx/models/buildings/special/hd_jinguan_city/`

运行时资源仅包括：

- `hd_jinguan_city.mesh`
- `hd_jinguan_city.asset`
- 从获授权来源复制且确有引用的 DDS 文件

不复制 CK3 原版水体、道路和桥梁贴图；`.asset` 直接引用原版资源路径。

## 10. 脚本与地图消费链

### 10.1 特殊建筑定义

修改 `common/buildings/tk_special_buildings.txt` 中现有的 `TK_20_21_JinGuanCheng`：

- 仅把 `asset.name` 从 `tgp_building_special_heian_kyo_mesh` 改为 `hd_jinguan_city_mesh`。
- 不改变建筑类型、图标、造价、时间、角色修正、省份修正、伯爵领修正、旅行兴趣点、大学标记或 AI 权重。

### 10.2 省份历史

修改 `history/provinces/zz_uuii_generated_county_capitals.txt` 的省份 4282：

- 增加 `special_building = TK_20_21_JinGuanCheng`。
- 保留现有 `culture = yizhou`、`religion = taipingdao`、`holding = castle_holding`。
- 只考虑新存档结果。

### 10.3 动态模型资源注册

修改 `gfx/map/map_object_data/special.txt`：

- 按模组现有寿春城、邺城的模式增加 `hd_jinguan_city_mesh` 的 `count=0` 动态资源注册。
- 不增加永久静态 transform。

### 10.4 定位点

使用现有 `gfx/map/map_object_data/special_building_locators.txt` 中 4282 号记录：

- 位置：约 `{ 5273, 0, 2827 }`
- 旋转：保留现有值
- 比例：`{ 1, 1, 1 }`

不修改 locator 文件。通过模型自身原点、朝向和尺度匹配该定位点。

## 11. 静态验收

### 11.1 PDX 回读

- 导出后必须用当前 PDX 工具重新导入最终 `.mesh`。
- 记录每个 LOD 的顶点数、三角面数、连通部件数、Shape 数、材质组和包围盒。
- 记录最大 Shape 的回读顶点与三角面数。
- Shape 名称、索引和 `.asset` 绑定必须一一对应。

### 11.2 几何与 UV

- 新建水域和道路不得出现退化三角形或零面积 UV。
- 不得存在意外负缩放或重复应用世界变换。
- LOD0 不得丢失宫殿、城墙、城门、军营、寺院或桥梁。
- LOD1、LOD2 必须达到批准的三角面比例范围，并保持城市轮廓。

### 11.3 贴图与着色器

- 复制的源 DDS 与来源文件 SHA-256 必须一致。
- 检查 DDS 压缩格式、Mip 数、alpha 范围和 packed 通道。
- 检查全部 diffuse、normal、properties、shader、shader_file 和 subpass 引用存在。
- 水域必须绑定 `lake`，道路必须绑定 `decal_local`。

### 11.4 脚本与消费链

- `TK_20_21_JinGuanCheng` 只引用 `hd_jinguan_city_mesh`。
- 省份 4282 只有一个锦官城特殊建筑赋值。
- `special.txt` 只有一条对应动态资源注册。
- 检查 Clausewitz 括号、重复键、编码、资源名称大小写和缺失引用。
- 运行 `git diff --check`，并逐项确认差异只对应本规格。

## 12. 明确不做的内容

- 不改变锦官城建筑的数值效果或图标。
- 不修改相邻省份、伯爵领或其他特殊建筑。
- 不制作英文或其他语言本地化。
- 不处理旧存档兼容。
- 不启动 CK3 或 Map Editor。
- 不声称已经验证游戏内比例、地形贴合、水体实际渲染、阴影或 LOD 切换观感。
- 不建立备份仓库、分支工作树或额外模组副本。
- 不把草图或制作辅助 JSON 作为运行时资源打包。

## 13. 完成判据

只有在以下条件全部满足时，才能把静态制作报告为完成：

1. 最终 `.mesh` 和 `.asset` 存在且通过 PDX 回读；
2. 资源构成、数量和布局符合草图及本规格；
3. LOD0 保留原始建筑部件，LOD1、LOD2 达到批准的简化目标；
4. 水体、道路和桥梁使用批准的原版契约；
5. 4282 省份、锦官城建筑定义和动态资源注册形成唯一消费链；
6. DDS、材质、Shape、脚本引用与静态检查均通过；
7. 最终报告明确列出未进行的游戏内验证。
