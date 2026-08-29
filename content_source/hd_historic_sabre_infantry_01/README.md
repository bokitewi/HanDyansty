# 历史化持刀步兵肖像装备制作记录

- Workshop 项目：`1835352612`
- 根 VMD：`variantmeshes/variantmeshdefinitions/unit_metal_sabre_infantry_historic.VariantMeshDefinition`
- 源包：`@_bjmy_China_Historic_Weapons.pack`
- 源包 SHA-256：`CBFCE13751CF7496047A91E718C50C847233F21886F6E7D2290BD4A2F1EB0506`
- 分支选择规则：每个无概率槽位取 VMD 中第一个声明分支；排除概率 `0.2`/`0.4` 的军官附件和所有同级替代外观。
- 明确排除：身体、头部、头发、手持刀、盾牌、民兵与派系替代分支。
- 上装甲裙归入上装；下装只保留裤装与胫甲鞋靴；刀鞘和腰挂归入上装。

## 工具链

- Blender `4.2.23 LTS`
- `io_scene_rmv2 1.8.0`
- `io_pdx_mesh 0.91`
- RPFM `5.0.6` 官方 Windows 便携包
- RPFM ZIP SHA-256：`39C289237C4511462845A5ECBE70BA66628ADB709AB7CE13B96C7786D090832D`
- DirectXTex `2026.5.8.1`

RPFM、RMV2 和 PDX Mesh 均已用真实源文件完成离线导入/导出冒烟测试。完整提取文件哈希和 17 个活动组件的 pack、内部路径、材质与贴图依赖清单生成在共享制作目录 `tools/work/hd_historic_sabre_infantry_20260829/manifests`；清单未解析项为 0。

`build_portrait_equipment.py` 生成基础网格和约定成年男性体型，`audit_roundtrip.py` 对最终 PDX 文件重新导入并检查 Shape、材质索引、三角面、UV、骨骼、权重和体型拓扑。两者均须由 Blender 后台模式执行。
