"""Score Step 3 round 2 (Exp. 8): selection rule with a ranking-based safety alarm, and the Green Light.

Rule (D, E, S): use default candidate D until at least E deaths are among fob's fresh (unseen-when-predicted)
records; then use the candidate in S with the best fresh AUC (pooled over complete weeks so far).
E = inf means "always D". The rule is chosen per outbreak by leave-one-outbreak-out (lowest mean gap to gold,
days 0-90, on the other outbreaks).
Green Light on the chosen rule's actual path: green on day d if deaths >= m, stability >= s (OS's risk scores
today vs 8 days earlier, whichever candidates were in use), on two checks in a row, and OS is not on the
age_trend fallback (falling back means OS does not yet trust its understanding). (m, s) is chosen by
leave-one-outbreak-out: fewest false greens, then earliest. A green is false if OS is > 0.02 below gold.
Usage: PYTHONPATH=src python -m outbreak_synth.analyse_os2 exp08_os_replay"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

TOL = 0.02
CHECK = [0, 14, 28, 56, 90]
DEFAULTS = ["kin", "kin_age", "age_trend"]
ES = [0, 10, 20, 50, 100, np.inf]
SETS = {"kin|age": ["kin", "age_trend"], "kin|kin_age|age": ["kin", "kin_age", "age_trend"],
        "all": ["kin", "consensus", "own", "kin_age", "age_trend"]}
MS = [10, 20, 50, 100]
SS = [0.9, 0.95, 0.98, 0.99]


def frame(r):
    d = pd.DataFrame(r["days"])
    if "real_only" not in d:
        d["real_only"] = np.nan
    return d


def path(d, D, E, S):
    out = []
    for _, r in d.iterrows():
        if r.fresh_deaths >= E:
            vals = {c: r[f"fresh_auc_{c}"] for c in S if pd.notna(r[f"fresh_auc_{c}"])}
            out.append(max(vals, key=lambda c: (vals[c], c == D)) if vals else D)
        else:
            out.append(D)
    return out


def apply_rule(d, rule):
    D, E, S = rule
    ch = path(d, D, E, SETS[S])
    auc = [d.loc[i, f"auc_{c}"] for i, c in zip(d.index, ch)]
    stab = [np.nan] + [np.nan] * 0
    stab = []
    for i, c in zip(d.index, ch):
        j = d.index[(d.day == d.loc[i, "day"] - 8)]
        if len(j) and f"stab_{c}__{ch[d.index.get_loc(j[0])]}" in d:
            stab.append(d.loc[i, f"stab_{c}__{ch[d.index.get_loc(j[0])]}"])
        else:
            stab.append(np.nan)
    return d.assign(chosen=ch, auc_os=auc, stability=stab)


def first_day(d, col, gold):
    hit = d[(gold - d[col]) <= TOL]
    return int(hit.day.iloc[0]) if len(hit) else None


def green_day(d, m, s):
    ok = (d.deaths >= m) & (d.stability >= s) & (d.chosen != "age_trend")
    ok2 = ok & ok.shift(1, fill_value=False)
    return int(d.day[ok2].iloc[0]) if ok2.any() else None


def main(name):
    outs = json.loads(Path("results", f"{name}.json").read_text())["outbreaks"]
    frames = {f: frame(r) for f, r in outs.items()}
    gold = {f: r["info"]["gold_auc"] for f, r in outs.items()}
    age = {f: r["info"]["age_only_auc"] for f, r in outs.items()}
    rules = [(D, E, S) for D, E, S in itertools.product(DEFAULTS, ES, SETS) if not (E == np.inf and S != "kin|age")]
    applied = {rule: {f: apply_rule(d, rule) for f, d in frames.items()} for rule in rules}
    gap = pd.DataFrame({str(rule): {f: float((gold[f] - a.auc_os).mean()) for f, a in per.items()} for rule, per in applied.items()})
    key = {str(r): r for r in rules}
    chosen = {f: key[gap.drop(index=f).mean().idxmin()] for f in gap.index}
    pd.set_option("display.width", 250)
    fixed = {f"always {c}": float(np.mean([(gold[f] - frames[f][f"auc_{c}"]).mean() for f in frames]))
             for c in ["kin", "consensus", "own", "kin_age", "age_trend"]}
    print("mean gap to gold, fixed candidates:", {k: round(v, 4) for k, v in fixed.items()})
    print("best rules (mean gap, all outbreaks):"); print(gap.mean().sort_values().head(8).round(4).to_string())
    print("rule chosen (leave-one-outbreak-out):", sorted(set(map(str, chosen.values()))))

    final = {f: applied[chosen[f]][f] for f in frames}
    rows = []
    for f in sorted(final):
        d, g, a = final[f], gold[f], age[f]
        both = d.dropna(subset=["real_only"])
        rows.append({"outbreak": f, "gold": round(g, 3), "age_only": round(a, 3),
                     **{f"d{k}": round(float(d.loc[d.day == k, "auc_os"].iloc[0]), 3) for k in CHECK},
                     "plateau_real": first_day(d, "real_only", g), "plateau_os": first_day(d, "auc_os", g),
                     "days_below_age": int((d.auc_os < a - 1e-9).sum() * 2),
                     "worst_vs_age": round(float((d.auc_os - a).min()), 3),
                     "worst_vs_real": round(float((both.auc_os - both.real_only).min()), 3) if len(both) else None,
                     "uses": ",".join(f"{c}:{n*2}d" for c, n in d.chosen.value_counts().items())})
    t = pd.DataFrame(rows)
    print(t.to_string(index=False))
    by_day = {k: f"{int((t[f'd{k}'] >= t.age_only - 1e-9).sum())}/{len(t)}" for k in CHECK}
    print("OS at least as good as age only, by day:", by_day)
    pr, po = t.plateau_real.fillna(999), t.plateau_os.fillna(999)
    summ = {"fixed_candidates_mean_gap": fixed, "rule_chosen": {f: str(r) for f, r in chosen.items()},
            "mean_gap_final": float(np.mean([(gold[f] - final[f].auc_os).mean() for f in final])),
            "os_at_least_age_only_by_day": by_day, "plateau_earlier_same_later_vs_real":
            [int((po < pr).sum()), int((po == pr).sum()), int((po > pr).sum())],
            "outbreaks_ever_below_age": int((t.days_below_age > 0).sum())}

    # Green Light on the final path.
    def ev(m, s):
        res = {}
        for f, d in final.items():
            gd = green_day(d, m, s)
            auc = float(d.loc[d.day == gd, "auc_os"].iloc[0]) if gd is not None else None
            res[f] = {"green_day": gd, "auc": auc, "false": gd is not None and gold[f] - auc > TOL}
        return res
    grid = {(m, s): ev(m, s) for m, s in itertools.product(MS, SS)}
    def cost(e, skip):
        e = [v for f, v in e.items() if f != skip]
        return (sum(v["false"] for v in e), np.mean([v["green_day"] if v["green_day"] is not None else 120 for v in e]))
    gl = []
    for f in sorted(final):
        ms = min(grid, key=lambda k: cost(grid[k], f))
        v = grid[ms][f]
        gl.append({"outbreak": f, "m": ms[0], "s": ms[1], "green_day": v["green_day"],
                   "auc_at_green": None if v["auc"] is None else round(v["auc"], 3), "gold": round(gold[f], 3),
                   "false_green": v["false"], "plateau_os": first_day(final[f], "auc_os", gold[f])})
    gl = pd.DataFrame(gl)
    print(gl.to_string(index=False))
    summ["green_light"] = {"rules": sorted(set(zip(gl.m, gl.s))), "greens": int(gl.green_day.notna().sum()),
                           "false_greens": int(gl.false_green.sum()), "never_green": int(gl.green_day.isna().sum()),
                           "median_green_day": None if gl.green_day.isna().all() else float(gl.green_day.median())}
    print(summ["green_light"])
    if "covid_2020" in final:
        d = final["covid_2020"]
        print("COVID 2020 gold", round(gold["covid_2020"], 3), "age_only", round(age["covid_2020"], 3),
              "slope prior", round(outs["covid_2020"]["info"]["slope_prior"], 3))
        print(d[d.day <= 44][["day", "n", "deaths", "fresh_deaths", "chosen", "auc_kin", "auc_kin_age", "auc_age_trend",
                              "auc_os", "real_only", "stability"]].round(3).to_string(index=False))
    t.to_csv(Path("results", f"{name}_summary.csv"), index=False)
    gl.to_csv(Path("results", f"{name}_greenlight.csv"), index=False)
    Path("results", f"{name}_analysis.json").write_text(json.dumps(summ, indent=2, default=str))


if __name__ == "__main__":
    main(sys.argv[1])
