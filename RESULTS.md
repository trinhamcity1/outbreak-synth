# RESULTS

Running log of what was run, on which data, and what came out. Newest entry first.

---

## 2026-10-05 — Outbreak library, H1N1 replay, and first test of learning from past outbreaks

### Owner decisions
- OS **learns** the new disease day by day. It generates synthetic data only once it judges that it understands
  the disease well enough. So the daily score is OS's understanding (AUC on later real patients), and
  synthetic data is checked once, when OS says it is ready.
- Start with Brazilian respiratory outbreaks only; mpox, Ebola and others come later.

### Outbreak library (`src/outbreak_synth/library.py` → `data/processed/library.parquet`, summary `results/library_summary.csv`)
- New data: SRAG 2009–2012 and 2013–2018 CSVs, same ministry portal, CC-BY (`scripts/download_srag_historic.sh`, SHA-256 recorded).
- Three form versions are harmonised to one schema: age, sex, race, state; 6 symptoms (fever, cough, sore throat,
  shortness of breath, respiratory distress, low oxygen saturation); 10 comorbidities (cardiac, lung, renal,
  immunosuppression, metabolic/diabetes, liver, neurological, obesity, postpartum, Down syndrome).
  Each is `yes` / `no` / `missing`.
- Mapping decisions (from the official dictionaries): age codes are `unit×1000 + value` on the old form;
  states are IBGE numbers on the old form and letters on the new one; old "chronic metabolic disease" = new "diabetes".
  On the 2009 pandemic form, `CLASSI_FIN 1` = new influenza subtype (H1N1pdm) and `EVOLUCAO 2` = death from influenza.
- Patients: hospitalised, outcome cure (1) vs death (2). 2010–2012 are skipped: the 2012 file mixes two outcome
  codings, and 2010–2011 are small.
- 24 outbreaks, ~2.15M patients. Examples: H1N1 2009 21,123 (9.5% death, median age 24); flu seasons
  1,257–11,824 each (13–19% death); other-virus seasons, mostly infants (median age 1, 3–7% death);
  COVID 2020–22 1.97M (28–33% death, median age 57–70).
- **Form effect:** the 2019+ form leaves 36–59% of yes/no fields blank, against 3–8% on the 2013–2018 form.
  That is a difference in the form, not the disease, so OS must not read it as a disease trait.

### Experiment 3: real data only, replayed day by day, on the shared fields (`run_replay_real.py`, `exp03_replay_real.toml`)
| Outbreak | Test set | Gold AUC | First day with enough data | First day within 0.02 of gold |
|---|---|---:|---|---|
| H1N1 2009 | entries 2009-09-08 to 12-31: 8,128 (620 deaths) | 0.761 | day 27 (123 pts, AUC 0.596) | **day 56** (7,315 pts, 0.753) |
| COVID 2020 | entries 2020-07: 93,635 (31,431 deaths) | 0.774 | day 21 (88 pts, 0.708) | **day 33** (2,824 pts, 0.756) |

- The shared fields lose almost nothing for COVID (gold 0.774 vs 0.776 with the full field set in Exp. 2).
- For H1N1, models from day 60 on beat the "gold" (0.771 vs 0.761) because the gold set includes 2010–2012
  entries from a different phase. The gold standard is a reference, not a strict ceiling.

### Experiment 4: does knowledge from past outbreaks help COVID early? (`run_prior_probe.py`, `exp04_prior_probe.toml`)
Past library = every outbreak that ended before 2020 (H1N1 2009, flu and other-virus 2013–2019; 93,643 patients).

| Day | COVID patients so far | New data only | Past outbreaks only | Past + new |
|---:|---:|---:|---:|---:|
| 0–20 | 1–15 | cannot train | 0.727 | cannot train |
| 21 | 88 | 0.708 | 0.727 | 0.716 |
| 24 | 306 | 0.717 | 0.727 | 0.720 |
| 26 | 553 | 0.738 | 0.727 | 0.742 |
| 28 | 1,084 | 0.740 | 0.727 | 0.742 |
| 33 | 2,824 | 0.756 | 0.727 | 0.757 |

**Plain reading:**
- The past-only model scores 0.727 with zero COVID patients, but **ranking COVID patients by age alone also scores 0.727**.
  So far, the past outbreaks are teaching only "older patients die more often", which is known on day 0 without any model.
- Adding the past model's risk score to the new data helps a little on days 21–28 (+0.002 to +0.009) and does not move the plateau day (33).
- **Death rate:** 11.5% in past outbreaks vs 33.6% in COVID. A generator built mainly from past outbreaks would understate
  COVID deaths about three times over. OS has to learn the new disease's own severity from its early rows.
- This is a negative first result for the simplest version of the idea. It does not rule out OS. It says the gain must come
  from learning more than age from past outbreaks (e.g. which comorbidities matter and how much), from choosing which past
  outbreaks to trust, and from learning the new disease's severity fast.

---

## 2026-10-05 — Experiment 2: days to plateau with real data only

**Why:** The owner's goal is a learner ("OS") that gives scientists useful data earlier in an outbreak.
The baseline it has to beat is how many days real data alone takes to reach its plateau.

- Code: `src/outbreak_synth/run_days_to_plateau.py`, config `experiments/exp02_days_to_plateau.toml`,
  output `results/exp02_days_to_plateau.json`. Logistic regression (the best small-N model in Exp. 1).
- Day 0 = 2020-02-26, the first hospitalised COVID-19 record entered. On day d, train on every record entered up to day d.
- Fixed test set: records entered 2020-07-01 to 2020-07-31 (93,635 patients, 31,431 deaths).
- Gold standard: trained on every record we hold today except the test month (1,876,969). **AUC 0.776.**
- Days with fewer than 10 deaths or 10 survivors are skipped (days 0–20: too few records to train at all).

| Day | Date | Records so far | AUC | Gap to gold |
|---:|---|---:|---:|---:|
| 21 | 2020-03-18 | 88 | 0.711 | 0.065 |
| 24 | 2020-03-21 | 306 | 0.721 | 0.055 |
| 28 | 2020-03-25 | 1,084 | 0.740 | 0.036 |
| **33** | **2020-03-30** | **2,824** | **0.757** | **0.019 (first day within 0.02)** |
| 42 | 2020-04-08 | 8,425 | 0.760 | 0.016 |
| 63 | 2020-04-29 | 27,880 | 0.764 | 0.011 |
| 120 | 2020-06-25 | 156,923 | 0.771 | 0.005 |

**Reading:** for this task, real data alone reaches its plateau about **one month** after the first record
(day 33). After that it improves very slowly. For OS to be useful on COVID-19 in Brazil, it must
produce useful data during **days 0–32**, especially days 0–20, when real data cannot train anything.
That window is narrow, and the gold-standard AUC itself is modest (0.776) with these admission-time fields.

---

## 2026-10-05 — Decisions and Experiment 1: real data only (no synthetic data)

### Decisions from the owner
1. Task: in-hospital death among hospitalised COVID-19 patients (`CLASSI_FIN=5`, `HOSPITAL=1`,
   `EVOLUCAO` 2 death vs 1 cure).
2. The earliest N records are chosen by **data-entry date** (`DT_DIGITA`), not symptom onset.
3. Test set: the **records entered right after the small sample** (owner: "earliest data point with
   date entries"). Implemented as every record entered in the 30 days after the last training day.
4. The "epsilon tuner" is the owner's separate `dp tuner` repo (differential privacy). It is out of scope here.

### Setup
- Code: `src/outbreak_synth/data.py`, `models.py`, `run_real_only.py`; config `experiments/exp01_real_only.toml`;
  output `results/exp01_real_only.json`. Data: the four SRAG files listed above (release 23-03-2026).
- Cohort 1,970,604 rows, ordered by entry date → onset date → notification id (deterministic).
- Training pool: first 3,000 records (entered 2020-02-26 to 2020-03-31). Records entered on the
  cutoff day after the 3,000th are left out of both sets.
- **Test set: 26,245 records entered 2020-04-01 to 2020-04-30, 9,227 deaths (35.2%).** The same for every N.
- Features (admission-time only, 25): age; sex, race, urban/rural zone, notifying state; 8 symptoms;
  12 comorbidities; hospital-acquired infection. Each yes/no field becomes `yes` / `no` / `missing`
  (blank or 9). ICU, ventilation, X-ray, antivirals and lab results are excluded because they happen
  after admission and would leak the outcome. Four symptoms added to the form later in 2020 are excluded (>90% blank early).
- Models: logistic regression (one-hot, standardised age); histogram gradient boosting (300 trees, lr 0.05).
- 95% CI: 1,000 bootstrap resamples of the test set. Both models turned out deterministic for a
  fixed training set, so seeds do not change these numbers. Seed variance will come in with the generators.
- Reference ceiling: trained on 537,778 records entered **after** the test window (May–Dec 2020). This is
  future data, so it is only an upper reference, not something available during an outbreak.

### Results: test AUC (95% bootstrap CI)

| Train N | Deaths in train | Logistic regression | Gradient boosting |
|---:|---:|---|---|
| 100 | 39 | 0.728 (0.722–0.734) | 0.720 (0.714–0.727) |
| 300 | 110 | 0.738 (0.732–0.744) | 0.709 (0.703–0.716) |
| 1,000 | 333 | 0.783 (0.777–0.788) | 0.756 (0.750–0.762) |
| 3,000 | 902 | 0.797 (0.792–0.802) | 0.774 (0.768–0.780) |
| Reference (537,778) | 177,830 | 0.807 (0.802–0.812) | 0.815 (0.811–0.821) |

### What this means
- **The room for synthetic data to help is small.** With 3,000 real records, logistic regression is
  already 0.010 below its ceiling and 0.018 below the best ceiling (0.815). It is within the brief's
  "0.02 of full data" target at N = 3,000 without any synthetic data.
- The real room is at **N = 100–300** (0.07–0.09 below the ceiling), and at N = 1,000 for gradient boosting (0.06).
  That is where the generator comparison is worth running.
- Logistic regression beats gradient boosting at every small N, which matches the JMIR sample-size study cited in the brief.
- I have not fitted the power-law learning curve yet. Four points are too few for it to mean much on its own; I'll fit it once the generator runs add points.

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
