# -*- coding: utf-8 -*-
"""
阶段A：根据 mapping_special_buildings.csv + tk_special_buildings.txt + history/provinces + localization
生成权威放置清单 placement_final.csv 与被筛除清单 placement_dropped.csv。

策略（用户确认）：
  - 歧义省份：按地区选优（男爵名/郡县 比对候选省份的 barony/county/duchy 中文名，取最高匹配；平局跳过）
  - 同省多建筑：按 (匹配层级, 置信度, 类型) 取一个
  - 时机：只放汉代及之前（始建年 <= 220）
  - 18 条缺省份：在 mapping 中已标为"建筑有键·地块缺失"，本脚本直接跳过
"""
import csv, re, os, glob, collections

MOD = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty"
CSV = os.path.join(MOD, ".workbuddy", "mapping_special_buildings.csv")
TK = os.path.join(MOD, "common", "buildings", "tk_special_buildings.txt")
PROVDIR = os.path.join(MOD, "history", "provinces")
LOCROOT = os.path.join(MOD, "localization")
OUT_FINAL = os.path.join(MOD, ".workbuddy", "placement_final.csv")
OUT_DROP = os.path.join(MOD, ".workbuddy", "placement_dropped.csv")

# ---------- 1. TK 键映射：Excel建筑编号 -> TK键 ----------
tk_txt = open(TK, encoding="utf-8", errors="ignore").read()
tkmap = {}
for m in re.finditer(r"^TK_(\d+)_(\d+)_(.+?)\s*=\s*\{", tk_txt, re.M):
    tkmap[m.group(3).strip()] = m.group(0).split("=")[0].strip()
print("[1] TK 键解析:", len(tkmap))

# ---------- 2. history/provinces -> prov_id -> {file, county_id, duchy_id, en} ----------
prov_info = {}
for fn in os.listdir(PROVDIR):
    if not fn.endswith(".txt"):
        continue
    fp = os.path.join(PROVDIR, fn)
    cur_d = None
    cur_c = None
    for line in open(fp, encoding="utf-8", errors="ignore"):
        s = line.strip()
        if s.startswith("### "):
            cur_d = s[4:].strip()
        elif s.startswith("## "):
            cur_c = s[3:].strip()
        elif re.match(r"^\d+\s*=\s*\{", s):
            pid = s.split("=")[0].strip()
            prov_info[pid] = {"file": fn, "county_id": cur_c, "duchy_id": cur_d}
print("[2] province 索引:", len(prov_info))

# ---------- 3. localization -> 中文名映射 ----------
barony_name = {}   # pid -> 中文名
county_name = {}   # county_id(str) -> 中文名
duchy_name = {}    # duchy_id(str) -> 中文名
ymls = glob.glob(os.path.join(LOCROOT, "**", "*.yml"), recursive=True)
for yp in ymls:
    for line in open(yp, encoding="utf-8", errors="ignore"):
        m = re.match(r"^\s*([A-Za-z0-9_]+):\s*\d*\s*\"(.*)\"", line.rstrip())
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if re.match(r"^b_\d+_\d+$", key):
            barony_name.setdefault(key.split("_")[1], val)
        elif key.startswith("c_uuii_p_"):
            county_name.setdefault(key, val)
        elif key.startswith("d_"):
            duchy_name.setdefault(key, val)
print("[3] 中文名: barony", len(barony_name), "county", len(county_name), "duchy", len(duchy_name))

# ---------- 4. 处理候选 ----------
rows = list(csv.DictReader(open(CSV, encoding="utf-8-sig")))
LEVEL_RANK = {"男爵": 3, "郡县": 2, "省": 1}
CONF_RANK = {"高": 3, "中": 2, "低": 1}
# 人文地标关键词（命中则视为文化类，优先于资源矿）
CULT_KW = ["寺", "庙", "宫", "陵", "城", "关", "山", "书院", "学宫", "台", "楼", "阁",
           "观", "塔", "窟", "祠", "道观", "古城", "皇城", "神社", "社", "遗址", "泉", "湖", "沟", "海"]

def classify_type(r):
    blob = (r.get("建筑名称", "") + r.get("自定类型", "") + r.get("介绍", ""))
    if any(k in blob for k in ["矿", "铁", "铜", "盐", "金", "银", "玉", "煤"]):
        return 0  # 资源矿
    if any(k in blob for k in CULT_KW):
        return 1  # 人文地标
    return 1  # 默认按人文处理

def start_year(s):
    s = (s or "").strip()
    if not s:
        return None
    m = re.match(r"(\d+)\.", s)
    return int(m.group(1)) if m else None

candidates = []   # (建筑名, key, pid, file, 层级, 置信, 类型, score, 原始行)
dropped = []      # (建筑名, key, 原因, 备注)

for r in rows:
    cat = r["类别"]
    if cat in ("跳过", "建筑有键·地块缺失"):
        # 18 条缺省份按用户要求跳过（已在 mapping 中标好）
        if cat == "建筑有键·地块缺失":
            dropped.append((r["建筑名称"], r["解析建筑键"], "缺省份", r["mod省份id"]))
        continue
    ek = r["Excel建筑编号"].strip()
    key = tkmap.get(ek)
    if not key:
        dropped.append((r["建筑名称"], ek, "无TK键", ""))
        continue
    # 时机过滤
    y = start_year(r["始建时间"])
    if y is not None and y > 220:
        dropped.append((r["建筑名称"], key, "时机延后", "始建年=%s" % y))
        continue
    # 省份解析
    pids = [p.strip() for p in r["mod省份id"].split(",") if p.strip()]
    if not pids:
        dropped.append((r["建筑名称"], key, "缺省份", ""))
        continue
    # 地区选优（仅多省份时需要）
    bname = r["男爵名"].strip()
    cname = r["郡县"].strip()
    tokens = set()
    if bname:
        tokens.add(bname)
    if cname:
        # 郡县可能含多级，按常见分隔拆
        for t in re.split(r"[|/、\s]", cname):
            if t:
                tokens.add(t)
    scored = []
    for pid in pids:
        info = prov_info.get(pid)
        if not info:
            scored.append((pid, -1, "省份不在history"))
            continue
        bcn = barony_name.get(pid)
        ccn = county_name.get(info["county_id"]) if info["county_id"] else None
        dcn = duchy_name.get(info["duchy_id"]) if info["duchy_id"] else None
        sc = 0
        if bcn and bcn in tokens:
            sc += 1
        if ccn and ccn in tokens:
            sc += 1
        if dcn and dcn in tokens:
            sc += 1
        scored.append((pid, sc, "b=%s c=%s d=%s" % (bcn, ccn, dcn)))
    if len(pids) == 1:
        pid = pids[0]
        if pid not in prov_info:
            dropped.append((r["建筑名称"], key, "省份不在history", pid))
            continue
        score = scored[0][1]
    else:
        # 取最高分；平局（含全0）跳过
        maxsc = max(s[1] for s in scored)
        best = [s for s in scored if s[1] == maxsc]
        if maxsc <= 0 or len(best) > 1:
            dropped.append((r["建筑名称"], key, "歧义平局",
                             "; ".join("%s(sc=%d,%s)" % (s[0], s[1], s[2]) for s in scored)))
            continue
        pid = best[0][0]
        score = maxsc
    # 记录候选
    lvl = LEVEL_RANK.get(r["匹配层级"].replace("/歧义×", "").split("/")[0].strip(), 0)
    # 置信度取主级（去掉 /歧义×n）
    conf_raw = r["置信度"].split("/")[0].strip()
    conf = CONF_RANK.get(conf_raw, 0)
    typ = classify_type(r)
    candidates.append({
        "建筑名": r["建筑名称"], "key": key, "pid": pid,
        "file": prov_info[pid]["file"],
        "层级": r["匹配层级"], "置信": r["置信度"],
        "类型": "人文" if typ else "资源",
        "_lvl": lvl, "_conf": conf, "_typ": typ, "_score": score,
    })

print("[4] 通过键+省份+时机 的候选:", len(candidates))

# ---------- 5. 碰撞处理：按省份取一个 ----------
by_prov = collections.defaultdict(list)
for c in candidates:
    by_prov[c["pid"]].append(c)
final = []
for pid, lst in by_prov.items():
    if len(lst) == 1:
        final.append(lst[0])
        continue
    lst.sort(key=lambda c: (c["_lvl"], c["_conf"], c["_typ"]), reverse=True)
    final.append(lst[0])
    for loser in lst[1:]:
        dropped.append((loser["建筑名"], loser["key"], "碰撞落选",
                        "同省%s 胜出:%s" % (pid, lst[0]["建筑名"])))
print("[5] 碰撞后最终放置:", len(final), " 累计筛除:", len(dropped))

# ---------- 6. 输出 ----------
cols = ["建筑名", "key", "pid", "file", "层级", "置信", "类型", "_score"]
final_sorted = sorted(final, key=lambda c: (c["file"], int(c["pid"])))
with open(OUT_FINAL, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["建筑名", "TK键", "province_id", "文件", "匹配层级", "置信度", "类型", "地区评分"])
    for c in final_sorted:
        w.writerow([c["建筑名"], c["key"], c["pid"], c["file"], c["层级"], c["置信"], c["类型"], c["_score"]])

with open(OUT_DROP, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["建筑名", "TK键", "筛除原因", "备注"])
    for d in dropped:
        w.writerow(d)

# ---------- 7. 汇总 ----------
fc = collections.Counter(d[2] for d in dropped)
print("\n=== 汇总 ===")
print("最终放置:", len(final_sorted))
print("筛除明细:", dict(fc))
print("按文件:", dict(collections.Counter(c["file"] for c in final_sorted)))
