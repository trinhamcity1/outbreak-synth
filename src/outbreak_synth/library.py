"""Outbreak library: every Brazilian SRAG outbreak harmonised to one schema.

One row per hospitalised patient with a known outcome (cure vs death), tagged with the outbreak
it belongs to. Old (2009-2018, CSV) and new (2019+, parquet) SIVEP-Gripe forms are mapped to the
same fields; a field the form did not collect is "missing".
Usage: PYTHONPATH=src python -m outbreak_synth.library  -> data/processed/library.parquet
"""
import glob
from pathlib import Path

import numpy as np
import pandas as pd

OLD = Path("data/raw/srag_historic")
NEW = Path("data/raw/srag")
OUT = Path("data/processed/library.parquet")

SYMPTOMS = ["FEBRE", "TOSSE", "GARGANTA", "DISPNEIA", "DESC_RESP", "SATURACAO"]
# METABOLIC = old-form METABOLICA ("chronic metabolic disease / diabetes") = new-form DIABETES.
COMORB = ["CARDIOPATI", "PNEUMOPATI", "RENAL", "IMUNODEPRE", "METABOLIC", "HEPATICA",
          "NEUROLOGIC", "OBESIDADE", "PUERPERA", "SIND_DOWN"]
YESNO = SYMPTOMS + COMORB
OTHER_CAT = ["CS_SEXO", "CS_RACA", "SG_UF_NOT"]
CATEGORICAL = YESNO + OTHER_CAT
NUMERIC = ["age"]
FEATURES = NUMERIC + CATEGORICAL
TARGET = "death"

# IBGE state codes (old files) -> state abbreviations (new files).
UF = {11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO", 21: "MA", 22: "PI",
      23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE", 29: "BA", 31: "MG", 32: "ES",
      33: "RJ", 35: "SP", 41: "PR", 42: "SC", 43: "RS", 50: "MS", 51: "MT", 52: "GO", 53: "DF"}


def _num(s):
    return pd.to_numeric(s.astype("string").str.strip(), errors="coerce")


def _yesno(s):
    c = _num(s)
    yes = (c == 1).fillna(False).to_numpy(bool)
    no = (c == 2).fillna(False).to_numpy(bool)
    return pd.Series(np.select([yes, no], ["yes", "no"], "missing"), index=s.index)


def _finish(df, outbreak):
    for c in YESNO:
        df[c] = _yesno(df[c]) if c in df else "missing"
    df["CS_SEXO"] = df.CS_SEXO.astype("string").str.strip().replace({"I": pd.NA}).fillna("missing")
    df["CS_RACA"] = _num(df.CS_RACA).astype("Int64").astype("string").replace({"9": pd.NA}).fillna("missing")
    df["SG_UF_NOT"] = df.SG_UF_NOT.fillna("missing")
    df["age"] = df.age.clip(0, 110)
    df["outbreak"] = outbreak
    return df[["outbreak", "id", "DT_DIGITA", "DT_SIN_PRI"] + FEATURES + [TARGET]]


def load_old(year):
    """2009-2018 CSV files. 2009-2011 use the pandemic form (CLASSI_FIN 1 = new influenza subtype,
    EVOLUCAO 2 = death from influenza); 2012-2018 use CLASSI_FIN 1 influenza, 2 other resp. virus."""
    df = pd.read_csv(OLD / f"INFLUD{year:02d}.csv", sep=";", dtype=str, encoding="latin-1")
    df = df[_num(df.HOSPITAL) == 1].copy()
    df["id"] = f"{year:02d}-" + df.index.astype(str)
    for c in ["DT_DIGITA", "DT_SIN_PRI"]:
        df[c] = pd.to_datetime(df[c], format="%d/%m/%Y", errors="coerce")
    raw_age = _num(df.NU_IDADE_N)
    unit = (raw_age // 1000).map({1: 1 / (365.25 * 24), 2: 1 / 365.25, 3: 1 / 12, 4: 1.0})
    df["age"] = (raw_age % 1000) * unit
    df["METABOLIC"] = df["METABOLICA"]
    df["SG_UF_NOT"] = _num(df.SG_UF_NOT).map(UF)
    evo = _num(df.EVOLUCAO)
    df = df[evo.isin([1, 2])].copy()
    df[TARGET] = (evo[df.index] == 2).astype(int)
    return df, _num(df.CLASSI_FIN)


def load_new(path):
    cols = ["NU_NOTIFIC", "DT_DIGITA", "DT_SIN_PRI", "CLASSI_FIN", "HOSPITAL", "EVOLUCAO", "NU_IDADE_N",
            "TP_IDADE", "CS_SEXO", "CS_RACA", "SG_UF_NOT", "DIABETES"] + [c for c in YESNO if c != "METABOLIC"]
    df = pd.read_parquet(path, columns=cols)
    df = df[_num(df.HOSPITAL) == 1].copy()
    df["id"] = df.NU_NOTIFIC.astype(str)
    unit = _num(df.TP_IDADE).map({1: 1 / 365.25, 2: 1 / 12, 3: 1.0})
    df["age"] = _num(df.NU_IDADE_N) * unit
    df["METABOLIC"] = df["DIABETES"]
    df["SG_UF_NOT"] = df.SG_UF_NOT.astype("string").str.strip()
    evo = _num(df.EVOLUCAO)
    df = df[evo.isin([1, 2])].copy()
    df[TARGET] = (evo[df.index] == 2).astype(int)
    return df, _num(df.CLASSI_FIN)


def build():
    parts = []
    # H1N1 pandemic 2009: confirmed new-subtype influenza.
    df, cls = load_old(9)
    parts.append(_finish(df[cls == 1].copy(), "h1n1_2009"))
    # Seasonal outbreaks 2013-2018 (same form as today). 2010-2012 skipped: the 2012 file mixes
    # the pandemic-form and 2012-form outcome codes, and 2010-2011 are small.
    for y in range(13, 19):
        df, cls = load_old(y)
        parts.append(_finish(df[cls == 1].copy(), f"flu_20{y}"))
        parts.append(_finish(df[cls == 2].copy(), f"othervirus_20{y}"))
    for f in sorted(glob.glob(str(NEW / "INFLUD*.parquet"))):
        y = int(Path(f).name[6:8])
        df, cls = load_new(f)
        parts.append(_finish(df[cls == 1].copy(), f"flu_20{y}"))
        parts.append(_finish(df[cls == 2].copy(), f"othervirus_20{y}"))
        if y >= 20:
            parts.append(_finish(df[cls == 5].copy(), f"covid_20{y}"))
    lib = pd.concat(parts, ignore_index=True)
    lib = lib.sort_values(["outbreak", "DT_DIGITA", "DT_SIN_PRI", "id"], kind="stable").reset_index(drop=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lib.to_parquet(OUT, index=False)
    return lib


def summary(lib):
    g = lib.groupby("outbreak")
    s = pd.DataFrame({
        "patients": g.size(), "death_rate": g[TARGET].mean().round(3),
        "first_entry": g.DT_DIGITA.min().dt.date, "median_age": g.age.median().round(0),
        "fields_missing_share": g.apply(lambda x: (x[YESNO] == "missing").to_numpy().mean().round(2)),
    })
    return s


if __name__ == "__main__":
    lib = build()
    s = summary(lib)
    print(s.to_string())
    s.to_csv("results/library_summary.csv")
