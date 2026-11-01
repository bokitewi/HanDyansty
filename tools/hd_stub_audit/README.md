# 原版空壳审计脚本（2026-11-01）

在本目录运行（输出写到 out/，out/ 不必提交）：

1. python -I audit.py      # 建索引 out/idx.pkl（原版 1.20 与 mod 的顶层定义）
2. python -I compare.py    # token 级比对 -> out/results.json、out/deleted.json（同名文件覆盖丢失的原版定义）
3. python -I stubs.py      # 结构化桩检测 -> out/stubs.json（trigger/is_shown=always no、效果清空、hidden 等）
4. python -I onaction.py   # on_action 事件列表缺失条目 -> out/onaction_missing.json
5. python -I refs.py       # 丢失定义在现存代码中的引用 -> out/deleted_refs.json
6. python -I defines.py / rules.py / gui.py   # defines、游戏规则、GUI 隐藏元素

原版路径写在 audit.py 的 VAN。报告见 docs/原版空壳审计_2026-11-01.md。
7. python -I verify.py [文件...]   # 改动后验收：括号、缺失头衔/区域、未定义效果/触发器/事件（不带参数=git 改动文件）
8. python -I locchk.py             # 改动新增行引用的中文本地化键是否存在（name= 变量会误报）
