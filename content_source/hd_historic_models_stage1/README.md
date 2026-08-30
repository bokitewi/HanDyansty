# Han historic models Stage 1 source manifest

本目录只记录第三方源资产的选择与依赖审计，不生成 CK3 `.mesh/.asset`，不修改
`gfx`、`common` 或本地化文件，也不启动游戏。

## 固定选择

`selection_contract.json` 明确记录 13 个 accessory：7 个 headgear、3 个 clothes、
3 个 legwear；组件实例总数为 38，按 body part 为 head 14、upper 18、lower 6。
选择表保留了用户指定的 VMD 槽位、嵌套 VMD 链和大小写敏感的 model 引用。

## 源与链路

源包是：

`D:\SteamLibrary\steamapps\workshop\content\779340\1835352612\@_bjmy_China_Historic_Weapons.pack`

SHA256：

`CBFCE13751CF7496047A91E718C50C847233F21886F6E7D2290BD4A2F1EB0506`

`source_manifest.json` 对每个唯一源文件记录了源包哈希、实际内部路径、源文件
SHA256、文件种类、关联 accessory/component/body part，以及完整的
`VMD -> WSModel -> RMV2 -> LOD0 material part -> texture` 引用。纹理条目还记录
DDS 原生宽、高、格式和 mip 数。

只选择 LOD0；WSModel 的其他 `lod_index` 和 RMV2 的其他 LOD 均记录为排除项。所有
选定 VMD 链中的 probability slot 均明确记录为排除，选定 probability slot 为空。
`unresolved_dependency_count` 必须为 0。

源包中有一个历史格式边界：部分单 LOD v7 RMV2 使用 v6 大小的 LOD header，解析器
会以 LOD 数组索引 0 作为 LOD0，并在 manifest 中标记
`lod_array_index_0_legacy_header`。`touming.xml.material` 的两个嵌套 source 标签
只在内存中做确定性 XML 修复；原始文件与哈希不变。

## 复现

在仓库根目录运行：

```text
py -3.11 content_source\hd_historic_models_stage1\test_stage1_contract.py
py -3.11 content_source\hd_historic_models_stage1\build_stage1.py
```

工具只读取允许的 `mod\tools\work\hd_historic_models_stage1_20260829` 提取目录，
并写回本目录的两个 JSON 输出；不会写入 CK3 运行时目录。
