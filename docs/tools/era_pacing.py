# -*- coding: utf-8 -*-
"""天朝循环·时代特色：节奏粗估。读取生成后的局势文件与数值表，估算各出口到 5000 的年数。

场景（均为粗估，用于发现明显失衡，不代表实际游戏）：
  安静：只有年度保底/年度统计类正分诱因每年触发一次（负分不计）
  一般：安静 + 本出口正分行为诱因中取中位数值的 3 个，每年各触发 2 次
  动荡：安静 + 本出口全部正分行为诱因每年各触发 1 次
  上限：单个诱因每年最多 10 次（年上限），列出单诱因年最大贡献最高者
用法：python docs/tools/era_pacing.py
"""
import os
import re
import statistics

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SIT = os.path.join(ROOT, 'common', 'situation', 'situations', 'z_kuzhu_modified_dynastic_cycle.txt')
VAL = os.path.join(ROOT, 'common', 'script_values', 'hd_dc_era_values.txt')
P = 'situation_dynastic_cycle_phase_'
YEARLY_HINT = ('_yearly', 'natural_disaster', 'epidemic', 'treasury_debt', 'treasury_raided', 'too_few_lands',
               'examinations_gap', 'maa_limit', 'demilitarized', 'endless_war', 'overmighty', 'land_annexation',
               'wuxun_dominant', 'houses_')


def load_values():
    vals = {}
    with open(VAL, encoding='utf-8-sig') as f:
        for ln in f:
            m = re.match(r'^(\w+)\s*=\s*(-?\d+(?:\.\d+)?)', ln)
            if m:
                vals[m.group(1)] = float(m.group(2))
    return vals


def main():
    vals = load_values()
    text = open(SIT, encoding='utf-8-sig').read()
    thr = vals['hd_dc_era_threshold']
    rows = []
    for pm in re.finditer(r'^\t\t(' + P + r'\w+) = \{', text, re.M):
        src = pm.group(1)
        # 截到下一个阶段
        nxt = re.search(r'^\t\t' + P + r'\w+ = \{', text[pm.end():], re.M)
        blk = text[pm.end(): pm.end() + nxt.start()] if nxt else text[pm.end():]
        for om in re.finditer(r'^\t\t\t\t(' + P + r'\w+) = \{(.*?)^\t\t\t\t\}', blk, re.M | re.S):
            dst, body = om.group(1), om.group(2)
            cats = re.findall(r'^\s*(catalyst_\w+)\s*=\s*(\S+)', body, re.M)
            yearly, behav = [], []
            for k, v in cats:
                n = vals.get(v)
                if n is None:
                    try:
                        n = float(v)
                    except ValueError:
                        continue
                if n <= 0 or n >= thr:
                    continue
                (yearly if any(h in k for h in YEARLY_HINT) else behav).append((k, n))
            # 家族统计四档互斥：只按"中"档计
            yearly = [(k, n) for k, n in yearly if 'houses_' not in k or k.endswith('_m')]
            quiet = sum(n for _, n in yearly)
            med = statistics.median([n for _, n in behav]) if behav else 0
            typical = quiet + 3 * 2 * med
            storm = quiet + sum(n for _, n in behav)
            top = max(behav, key=lambda x: x[1]) if behav else ('-', 0)

            def yrs(x):
                return '%.0f' % (thr / x) if x > 0 else '∞'
            rows.append((src.replace(P, ''), dst.replace(P, ''), quiet, yrs(quiet), typical, yrs(typical),
                         storm, yrs(storm), top[0].replace('catalyst_', ''), top[1] * 10))
    print('| 出口 | 安静/年 | 年数 | 一般/年 | 年数 | 动荡/年 | 年数 | 单诱因年上限最大者（×10） |')
    print('|---|---|---|---|---|---|---|---|')
    for r in rows:
        print('| %s → %s | %.0f | %s | %.0f | %s | %.0f | %s | %s %.0f |' % r)


if __name__ == '__main__':
    main()
