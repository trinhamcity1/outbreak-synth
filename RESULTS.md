# RESULTS

Running log of what was run, on which data, and what came out. Newest entry first.

---

## 2026-10-05 — Step 1: data inspection (no models trained)

**Script:** `PYTHONPATH=src python -m outbreak_synth.inspect_srag` → `results/inspect_srag.json`
**Environment:** 4 CPU cores, 15 GB RAM, **no GPU**. Python 3.11, pandas 3.0.6, pyarrow 25.0.1.

### Data used
I used the **primary source** instead of the two derived files in the brief. The "derived file"
(3.4M records, `classi_fin`) and the "COVID-19 inpatient mortality" file are both cut from this
same surveillance system, so going to the source removes a layer of unknown preprocessing and
settles the license question.

| File (release 23-03-2026) | Rows | SHA-256 (first 12) |
|---|---:|---|
| INFLUD19 (symptoms 2018-12-30 to 2019-12-28) | 48,941 | 748519f593d4 |
| INFLUD20 (2019-12-29 to 2021-01-02) | 1,206,920 | 371723b91c0e |
| INFLUD21 (2021-01-03 to 2022-01-01) | 1,745,672 | ecad01062f23 |
| INFLUD22 (2022-01-02 to 2022-12-31) | 560,577 | 93aab4d4ef3a |

- Source: Ministério da Saúde open-data portal, dataset `srag-2019-a-2026`, **CC-BY**
  (license stated on the dataset page). The portal moved from opendatasus.saude.gov.br to
  dadosabertos.saude.gov.br; files are on the ministry's S3 bucket.
- 194 columns per file. No duplicate notification IDs across 3,562,110 rows.
- The SRAG form is for **hospitalised** severe respiratory illness, so `HOSPITAL = 1` for ~96%.
- Label codes checked against the official data dictionary:
  `CLASSI_FIN` 1 influenza, 2 other respiratory virus, 3 other agent, 4 unspecified, 5 COVID-19;
  `EVOLUCAO` 1 cure, 2 death, 3 death from other causes, 9 ignored.
- Data quirk: code fields are numeric in the 2019–20 files and strings in 2021–22. My first
  pass silently dropped 2021–22 from the counts. Fixed: all code fields are now converted to numbers on load.

### Candidate task A: in-hospital death among hospitalised COVID-19 (preferred in the brief)
Cohort: `CLASSI_FIN = 5`, `HOSPITAL = 1`, `EVOLUCAO ∈ {1, 2}` (excludes deaths from other causes and unknown outcomes).

- 1,970,604 records, death rate **32.3%** (2020–2022).
- Earliest-N samples, ordered by symptom-onset date:

| N | Deaths | Survivors | Last onset date in sample |
|---:|---:|---:|---|
| 100 | 35 | 65 | 2020-02-29 |
| 300 | 117 | 183 | 2020-03-06 |
| 1,000 | 329 | 671 | 2020-03-13 |
| 3,000 | 888 | 2,112 | 2020-03-19 |

Events are not scarce: even N = 100 has 35 deaths. Monthly volume goes from 102 (Feb 2020) to
11,855 (Mar) and 54,227 (Apr), so N = 3,000 covers roughly the first five weeks.

### Candidate task B: influenza vs COVID-19 classification
Hospitalised, known-outcome influenza: only **29,634** records (6,460 from 2019, before COVID).
This is a diagnosis task, not a prognosis task, and it does not fit the "new disease, few records" framing as well.

### Missingness (all 3.56M rows; blank or 9 = "ignored")
Demographics are almost complete (age 0.5%, sex 0%). Symptoms 14–20%. **Comorbidities are 54–64%
missing** (cardiac 54%, diabetes 57%, obesity 64%, renal 64%), because in many records the
comorbidity block is left blank instead of being marked "no". How to encode this
(blank = no, or a separate "missing" category) changes what the generators learn, so it needs
one fixed rule for every generator.

### Concerns to flag
1. **Reporting lag.** For records with onset before 2020-03-20, the median delay from onset to data
   entry is 12 days; the 90th percentile is 66 days and the 99th is 391 days. "Earliest N by onset date"
   from today's final file is not what an analyst actually had in March 2020. It is more complete
   and its outcomes are already resolved. Ordering by data-entry date (`DT_DIGITA`) instead would be more realistic.
2. **Distribution shift in the held-out set.** The death rate moves over time (36% Feb, 40% Apr,
   30% Sep 2020), and vaccines and variants arrive in 2021–22. A time-based test set that spans
   2020–2022 mixes these effects into the AUC. A narrower test window (e.g. Apr–Jun 2020) is cleaner.
3. **Past-disease side.** The 2019 file holds only ~6.5k hospitalised influenza records with known
   outcomes. The portal also has SRAG 2009–2012 (including the H1N1 pandemic) and 2013–2018. These
   are a natural, same-schema, same-source "past outbreaks" library. I have not downloaded or checked them yet.

### Not done yet (waiting on decisions)
Steps 2–6 (generators, predictors, learning curves). The brief makes the prediction task a decision point.
