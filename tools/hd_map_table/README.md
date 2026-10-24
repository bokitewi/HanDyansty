# 地图桌「汉晋漆案」构建脚本

工具：Blender 4.2（Steam 版），加 io_pdx_mesh 0.91（4.2 extensions 目录）。另需带 Pillow 的 Python（用 `python -P` 运行）。

1. `import_audit.py`：用「Import Autodesk MAX」扩展读 3d66 #18349387 的 .max，保存为 blend，并输出部件审计 json。
   用法：`blender -b --factory-startup --python import_audit.py -- <扩展目录> <.max> <out.blend> <audit.json>`
2. `build_scene.py`：烘焙世界矩阵、删杂物、贴图对应，按 `cfg_layout.json` 摆放器物和汉刀，再缩放到 CK3 单位。
   用法：`blender -b <source_import.blend> --python build_scene.py -- cfg_layout.json <scene.blend>`
3. `mockup_render.py`：布局示意渲染，地图用 colormap 占位。
4. `tex_build.py`：生成全部 DDS（自写 mip 链），并找出黑色 UV 区。
   用法：`python -P tex_build.py <素材目录> <输出目录> <原版 tgp 目录> <汉刀目录> <tex_report.json>`
5. `prod_export.py`：
   - 拆分并合并 Shape；
   - 把黑面 UV 收进黑色区；
   - 修零面积 UV；
   - 博山炉减面（参数为目标面数，现用 12000）；
   - 导出 3 个 .mesh。
6. `roundtrip.py`：回读 .mesh，核验 Shape、面数、UV、包围盒，并渲染背面剔除视图。
7. `write_text.py`：从回读结果生成 .asset、地图物件、图层、风格、环境和本地化文件。
8. `import_installed.py`：从安装目录导入 .mesh，再配合 `mockup_render.py` 出最终预览。

改布局：编辑 `cfg_layout.json` 后，从第 2 步重跑。改动只影响暂存目录，拷进 HanJIn_Clothes 前先确认游戏没在运行。

汉刀的两种定位方式：
- 给了 `sword.top_cm`（刀北端坐标，单位厘米，以桌面中心为原点，东为 +X、北为 +Y）时：从北端沿 `tilt_deg` 往南摆，长度取 `length_cm`。
- 没给时：按 `cross_frac` / `overhang_cm` 推算。

现用的是第一种：`top_cm` (-27.5, 22.5)、倾角 11.2°，数值从游戏截图上的红圈量出。
