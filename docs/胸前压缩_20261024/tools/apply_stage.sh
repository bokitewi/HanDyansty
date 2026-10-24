#!/usr/bin/env bash
# 备份原文件到 docs/胸前压缩_备份_20261024/<件名>/ 后，用暂存版覆盖 HanJIn_Clothes 原文件。
# 用法：bash apply_stage.sh <stage_final 目录>      还原：把备份目录里的文件按同名拷回 m_clothes/<件名>/
set -e
STAGE="$1"
MC="/e/documents/Paradox Interactive/Crusader Kings III/mod/HanJIn_Clothes/gfx/models/portraits/m_clothes"
BK="/e/documents/Paradox Interactive/Crusader Kings III/mod/HanDyansty/docs/胸前压缩_备份_20261024"
n=0
for gdir in "$STAGE"/g*/*/; do
  g=$(basename "$gdir")
  mkdir -p "$BK/$g"
  for f in "$gdir"*.mesh; do
    b=$(basename "$f")
    [ -f "$MC/$g/$b" ] || { echo "MISSING ORIGINAL $g/$b"; exit 1; }
    [ -f "$BK/$g/$b" ] || cp -p "$MC/$g/$b" "$BK/$g/$b"
    cp "$f" "$MC/$g/$b"
    cmp -s "$f" "$MC/$g/$b" || { echo "COPY MISMATCH $g/$b"; exit 1; }
    n=$((n+1))
  done
done
echo "APPLIED $n files"
