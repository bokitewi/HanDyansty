# 长城 C3/G1 方案 A 设计规格

状态：用户已批准设计；游戏数据实施尚未开始。

日期：2026-08-23

## 1. 目标

修复 HanDyansty 地图上长城与关口整体同向错位、墙段首尾不相连、部分墙体进入水域的问题，同时遵守用户已锁定的 `scale = 2.0` 视觉尺寸。

本设计不再用现有大尺寸墙体 mesh 拼接一条跨越整个北方的连续长城，而是采用三个彼此独立的象征性短段。每个短段只放置一个 `great_wall_china_03` 实例，并配置一个从安装版原版 wall03/关口关系推导出的关口实例。

## 2. 已锁定的生产决定

- 所有保留的墙体与关口 transform 三轴缩放必须逐字写为 `2.000000 2.000000 2.000000`。
- 采用 C3：三个分离的象征性短段，不要求三个区域之间连续。
- 采用 G1：不强制保留现有五个关口，只保留几何上可行的关口。
- 采用已批准的方案 A：三个独立 wall03 段，每段一个正确套用原版 socket 关系的关口。
- 只使用现有 mesh 和 asset，不新增、不复制、不转换模型资源。
- 本轮未获授权启动游戏；设计和后续实施只能声明离线/静态检查结果。

## 3. 成功标准

实施后必须同时满足：

1. 地图对象实例结构为 `wall01 = 0`、`wall02 = 0`、`wall03 = 3`、`gate = 3`，且 transform 数量分别为 `0/0/3/3`。
2. 六个保留实例的 position、quaternion 和 scale 与本规格逐字段一致，不重新归一化四元数，不翻转四元数符号。
3. 三个墙体实例分别由单个 wall03 mesh 构成；不存在需要靠两个独立 transform 首尾拼接的段内接缝。
4. 三个关口分别复用安装版原版 wall03 的同一个已验证 socket 关系，复算残差不超过 `0.10` 世界单位，并重现约 `0.0962` 的现有结果。
5. 使用完整 mesh 三角面投影而不是对象中心点检查后，六个实例对海域、主要河流、湖泊、不可通行山地和不可通行海域的命中数都为 `0`。
6. 最终游戏数据增量只涉及两份获批文件中的 count 和 transform；无关脏工作保持不变。
7. 不把离线几何结果表述为游戏内视觉验收通过。

## 4. 作用域

### 4.1 允许修改的游戏数据文件

- `gfx/map/map_object_data/great_wall_china.txt`
- `gfx/map/map_object_data/great_wall_china_gate.txt`

### 4.2 明确不修改

- `.mesh`、`.asset`、纹理和材质；
- `gfx/map/map_object_data/uuii_compat_layers.txt` 或其他 layer 定义；
- Great Building 的 startup、23 节点或建筑逻辑；
- building/holding locator；
- `descriptor.mod`；
- `map_data`、地形、heightmap、province 或水域数据；
- 任何无关文件和既有脏工作。

设计文档本身不是游戏数据改动。后续实施不得以本设计为理由扩大上述游戏数据范围。

## 5. 原版参照与现有链路

安装版 CK3 的同类地图对象定义表明，长城和关口使用：

- 显式 transform；
- `render_pass=Map`；
- `clamp_to_water_level=no`；
- `generated_content=no`；
- 对应 pdxmesh 绑定。

原版链路中没有发现会自动把关口吸附到墙体、自动连接相邻墙段或自动避开水域的 socket/连续性逻辑，因此位置、旋转和实例数量必须由 map object 数据显式给出。

安装版原版还存在 `count=0` 且不带 transform 的 map object 定义模式。因此，保留 wall01/wall02 对象块和 pdxmesh 绑定、只把实例数设为零，是符合现有数据模式的最小改动。

模组现有 `hd_great_wall_layer` 继续使用，不修改其淡出设置。Great Building 的 23 节点逻辑与本次纯视觉 map object 布局分离，不纳入改动。

## 6. 根因判断

现有文件把 scale 已放大到 2，但仍沿用不适配该体量的多段路径和关口位置：

- scale 2 下，wall01 的水平包围约为 `382 x 554`，wall02 约为 `554 x 601`，wall03 约为 `357 x 173`；
- 大型独立 mesh 不是可任意裁切、拉伸或自动弯折的样条；
- 多个大 mesh 仅靠手工 transform 排成跨区域长链时，端点、旋转和地形误差会累积；
- 关口也不会自动迁移到新的墙体位置；
- 只做整条路线的统一平移无法同时修复接缝、关口 socket 和局部水域/陡坡冲突。

因此，本设计在保持 scale 2 和现有资源的前提下，选择最短、最窄的 wall03，并取消所有墙体间的外部拼接接缝。

## 7. 获批布局

三个区域名仅用于展示和辨认候选位置，不表示精确历史遗址坐标：

1. West / Hexi：西部象征短段；
2. Central / Hetao：中部象征短段；
3. East / Yanshan-Liaoxi：东部象征短段。

三地之间故意不连续。每个区域内部只有一个 wall03 mesh，因此“段内连续”来自 mesh 本身，而不是两个 map object 的首尾拼接。

## 8. 精确 transform 规格

每行字段顺序为：

`position_x position_y position_z quaternion_x quaternion_y quaternion_z quaternion_w scale_x scale_y scale_z`

### 8.1 wall03

| 区域 | transform |
|---|---|
| West / Hexi | `4975.000000 0.000000 4750.000000 0.000000 1.000000 0.000000 0.000000 2.000000 2.000000 2.000000` |
| Central / Hetao | `6775.000000 0.000000 4975.000000 0.000000 0.573576 0.000000 0.819152 2.000000 2.000000 2.000000` |
| East / Yanshan-Liaoxi | `7975.000000 0.000000 5025.000000 0.000000 -0.866025 0.000000 0.500000 2.000000 2.000000 2.000000` |

### 8.2 gate

| 区域 | transform |
|---|---|
| West / Hexi | `5038.485352 0.000000 4783.650878 0.000000 -0.409364 0.000000 0.912371 2.000000 2.000000 2.000000` |
| Central / Hetao | `6721.665249 0.000000 5023.147439 0.000000 -0.982172 0.000000 0.187983 2.000000 2.000000 2.000000` |
| East / Yanshan-Liaoxi | `8035.885191 0.000000 4986.845511 0.000000 0.101666 0.000000 0.994819 2.000000 2.000000 2.000000` |

这些字面值是实施权威值。虽然四元数 `q` 与 `-q` 在旋转语义上等价，实施时仍不得翻转符号；也不得用归一化后的近似数覆盖本表。

## 9. 关口 socket 推导

采用安装版原版 wall03 的第一个已验证 compatible socket：

- 原版 wall03 对象原点：`(6728.656738, 2994.335205)`；
- 对应原版 gate 对象原点：`(6696.914062, 2977.509766)`；
- 原版 gate quaternion：`0.000000 -0.912371 0.000000 -0.409364`。

推导保留的是 gate 相对 wall03 的局部位置与相对旋转，而不是把原版 gate 绝对坐标直接复制到新位置。一般形式为：

```text
local_offset = inverse(scale_wall_vanilla)
             * inverse(rotation_wall_vanilla)
             * (position_gate_vanilla - position_wall_vanilla)

position_gate_candidate = position_wall_candidate
                        + rotation_wall_candidate
                        * scale_wall_candidate
                        * local_offset

rotation_gate_candidate = rotation_wall_candidate
                        * inverse(rotation_wall_vanilla)
                        * rotation_gate_vanilla
```

上式用于记录来源和离线复验，不授权重新生成第 8 节已批准的数据。使用第 8 节字面 transform 复算时，三组 gate 原点到目标 wall03 socket 几何的残差约为 `0.0962` 世界单位；验收上限为 `0.10`。若结果明显不同，应先检查字段抄写、坐标轴、矩阵乘法顺序和 socket 选择，不能直接移动已批准对象。

wall03 另有第二个原版兼容 socket，但方案 A 已锁定每段只保留一个关口，并选用上述第一个 socket；第二个 socket 不是待决项。

## 10. 文件级改动矩阵

| 文件 | 对象 | 当前目标 | 允许的改动 |
|---|---|---:|---|
| `great_wall_china.txt` | `great_wall_china_01` | count `0`，transform `0` | count 从 4 改为 0，删除原有 transform |
| `great_wall_china.txt` | `great_wall_china_02` | count `0`，transform `0` | count 从 1 改为 0，删除原有 transform |
| `great_wall_china.txt` | `great_wall_china_03` | count `3`，transform `3` | 保持 count 3，用第 8.1 节三个 transform 替换原布局 |
| `great_wall_china_gate.txt` | `great_wall_china_gate` | count `3`，transform `3` | count 从 5 改为 3，用第 8.2 节三个 transform 替换原布局 |

四个对象必须保留原有：

- object 名；
- `render_pass=Map`；
- `clamp_to_water_level=no`；
- `generated_content=no`；
- `layer=hd_great_wall_layer`；
- 各自 pdxmesh 绑定。

wall01 和 wall02 即使 `count=0`，对象块与 pdxmesh 引用也不得删除。

## 11. 已完成的离线选址证据

### 11.1 mesh 尺寸与段内连续性

现有 mesh 已通过安装版 `io_pdx_mesh` 解析。wall03 在 scale 2 下约为 `357 x 173`，是 wall01、wall02、wall03 中最短且最窄的候选，因此最适合在严格保持 scale 2 时避让水域和陡峭禁区。

每个区域只有一个 mesh，不存在两个独立墙体 transform 的外部接缝。这个结论只说明数据结构中不再要求墙墙拼接，不等于游戏内所有观察角度都无视觉问题。

### 11.2 禁区栅格

地图尺寸为 `11136 x 6848`，世界坐标到 province 像素按 `(x, 6848 - z)` 映射。禁区 mask 来自模组当前 `map_data/default.map` 链，覆盖：

- sea zones；
- major rivers；
- lakes；
- impassable mountains；
- impassable seas。

检查使用完整 mesh 三角面投影，而非只检查 transform 原点，并使用：

- 墙体 footprint 缓冲：`2` 世界单位；
- 关口 footprint 缓冲：`1` 世界单位。

三个墙体和三个关口在上述各禁区 mask 上的命中数均为 `0`。

### 11.3 heightmap 回归指标

候选 footprint 覆盖范围内的 8-bit heightmap 灰度跨度为：

| 区域 | 墙体 | 关口 |
|---|---:|---:|
| West / Hexi | 6 | 2 |
| Central / Hetao | 21 | 8 |
| East / Yanshan-Liaoxi | 5 | 3 |

这些值不是物理高度、坡度或游戏内贴地成功证明，只用于检测坐标意外变化和确定运行时观察优先级。Central 段跨度最高，未来若获授权运行游戏，应优先检查其悬空、埋墙和穿坡情况。

## 12. 实施后的最小离线验收

### 12.1 结构与语法

- 验证 Clausewitz/Jomini 花括号平衡和 map object 基本结构；
- 验证四个对象块仍存在且 object 名唯一；
- 验证 count 与 transform 数量严格为 `0/0/3/3`；
- 验证 wall01/wall02 不残留 transform，wall03/gate 不残留旧布局或额外实例。

### 12.2 transform 精确值

- 对六个 transform 逐字段比对第 8 节；
- 验证全部 scale 字面值为 `2.000000 2.000000 2.000000`；
- 验证 position 和 quaternion 的数字、顺序、符号完全一致；
- 允许检查四元数范数接近 1，但不得将检查结果回写文件。

当前字面四元数的范数约为：

| transform | 范数 |
|---|---:|
| West wall | 1.000000000 |
| Central wall | 0.999999713 |
| East wall | 0.999999650 |
| West gate | 0.999999863 |
| Central gate | 0.999999723 |
| East gate | 1.000000409 |

上述约 `10^-7` 量级的偏差来自十进制截断，不构成失败。

### 12.3 关口几何复验

- 用落盘后的六个精确 transform 复用第 9 节同一推导和第一个 socket；
- 三组 gate/socket 残差都必须不超过 `0.10` 世界单位；
- 结果应重现约 `0.0962`，明显漂移优先判定为数据抄写、坐标系或验证算法错误。

### 12.4 禁区与 heightmap 回归

- 重新运行完整 mesh 三角面投影；
- 保持 wall buffer `2`、gate buffer `1`；
- 六个实例对五类禁区的命中数继续为 `0`；
- heightmap 灰度跨度应重现第 11.3 节结果，允许将其作为坐标回归证据，但不得作为视觉通过证据。

### 12.5 不变量、diff 与脏工作

- 检查第 10 节列出的属性和 pdxmesh 绑定未变；
- 实施前保存两份目标文件的精确副本和哈希到仓库外的新建专用临时目录，不覆盖既有 `crash_isolation_backups/bak_20260823_great_wall/`；
- 实施前后分别记录工作树状态；
- 只审计目标增量，不要求原本就脏的工作树变干净；
- 不使用广域 `reset`、`checkout`、`restore` 或格式化；
- 最终作用域 diff 中，游戏数据只允许出现第 10 节的 count/transform 改动；
- 确认原有无关修改仍存在且未被覆盖。

## 13. 必须留待游戏运行的验收

本轮没有游戏启动授权，以下项目不能声称已通过：

- 近、中、远距离缩放下的视觉尺寸、辨识度和整体构图；
- 三个 wall03 是否出现悬空、埋入、穿坡或相机角度相关穿模；
- Central 段较高 heightmap 灰度跨度是否产生不可接受的视觉效果；
- 三个关口是否在最终渲染中自然嵌入墙体，门洞、墙垛和朝向是否正确；
- holding、城堡、建筑模型或其他 locator 与墙体/关口是否发生明显穿插；
- 地名、领地、军队、建筑和其他地图标签是否遮挡；
- `hd_great_wall_layer` 的 zoom/fade 实际表现；
- 三个象征性短段是否达到用户最终审美预期。

普通 holding/building locator 的视觉重叠无法在不扩大文件范围的前提下完全排除。它是明确保留的运行时人工验收项，不是本轮离线验收的漏项，也不授权修改 locator 文件。

## 14. 风险与失败处理

- 若 count/transform、精确字面值、socket 残差或禁区栅格失败，停止并修正两份目标文件，不启动游戏掩盖静态失败。
- 若离线检查通过，只能报告“批准的 A 方案已按精确 transform 落盘并通过既定静态检查”。
- 若未来运行时发现 Central 段严重悬空/埋入或建筑穿插，应先把问题记录为视觉验收失败，再由用户决定是否授权新的坐标方案或扩大作用域；不得在本规格内擅自移动对象或修改地形/locator。
- 若需要回滚，只恢复实施开始前保存的两份目标文件精确副本，不触碰无关文件和既有备份。

## 15. 结论边界

本设计解决的是“在 scale 2、现有 mesh、两文件范围内，构造可静态验证的三段象征性长城和三处关口布局”。它不承诺跨区域连续长城，也不把静态 footprint、socket 和 heightmap 证据等同于游戏内最终视觉效果。

在获得用户对本书面规格的确认前，不进入实施计划和游戏数据修改阶段。
