# -*- coding: utf-8 -*-
"""
从指定文件中精确删除若干顶层块（key = { ... }），并一并删除紧邻块上方的注释行。
用法: python remove_dyn_blocks.py <文件路径> <key1> <key2> ...
"""
import re
import sys


def find_top_blocks(lines):
    """逐行扫描，返回 {key: [start_idx, end_idx]}，支持块内嵌套括号。"""
    blocks = {}
    i = 0
    n = len(lines)
    while i < n:
        m = re.match(r"^\s*([A-Za-z0-9_]+)\s*=\s*\{", lines[i])
        if m:
            key = m.group(1)
            depth = 0
            j = i
            while j < n:
                for ch in lines[j]:
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            break
                if depth == 0:
                    break
                j += 1
            blocks[key] = [i, j]
            i = j + 1
        else:
            i += 1
    return blocks


def main():
    path = sys.argv[1]
    keys = sys.argv[2:]
    with open(path, encoding="utf-8-sig") as f:
        lines = f.readlines()
    orig_count = len(lines)

    blocks = find_top_blocks(lines)
    missing = [k for k in keys if k not in blocks]
    if missing:
        print("未找到块:", missing, "-> 中止，不修改文件")
        sys.exit(1)

    # 收集要删除的行号（块 + 紧邻上方的注释行）
    delete_idx = set()
    for k in keys:
        s, e = blocks[k]
        # 块上方紧邻注释行（仅当中间无空行）
        p = s - 1
        while p >= 0:
            stripped = lines[p].strip()
            if stripped == "":
                break
            if stripped.startswith("#"):
                delete_idx.add(p)
                p -= 1
            else:
                break
        for idx in range(s, e + 1):
            delete_idx.add(idx)

    new_lines = [ln for idx, ln in enumerate(lines) if idx not in delete_idx]

    # 压缩连续空行（最多保留 1 个）
    collapsed = []
    prev_blank = False
    for ln in new_lines:
        blank = ln.strip() == ""
        if blank and prev_blank:
            continue
        collapsed.append(ln)
        prev_blank = blank

    # 去掉文件开头的多余空行
    while collapsed and collapsed[0].strip() == "":
        collapsed.pop(0)
    # 保证文件以单个换行结尾
    if collapsed and not collapsed[-1].endswith("\n"):
        collapsed[-1] += "\n"
    while collapsed and collapsed[-1].strip() == "":
        collapsed.pop()

    with open(path, "w", encoding="utf-8", newline="") as f:
        f.writelines(collapsed)

    print("删除 %d 个块: %s" % (len(keys), ", ".join(keys)))
    print("行数: %d -> %d (删除 %d 行)" % (orig_count, len(collapsed), orig_count - len(collapsed)))


if __name__ == "__main__":
    main()
