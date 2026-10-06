# RESULTS

Running log of what was run, on which data, and what came out. Newest entry first.

---

## 2026-10-06 — Step 2: Severity Model + Handover Rule vs real data only

**Code:** `src/outbreak_synth/recipe.py`, `run_recipe_replay.py`, `analyse_recipe.py`; config
`experiments/exp06_recipe_replay.toml`. Outputs: `results/exp06_recipe_replay.json`, `_summary.csv`, `_analysis.json`.
Runtime 21 minutes on 4 CPUs.

### Method
- **Severity Model:** logistic regression for in-hospital death, fitted with a prior.
  - Each risk factor's prior mean = the Kinship-Vote-weighted average of the kin's coefficients. Votes come from
    Step 1, using only weeks completed before the day in question.
  - Never borrowed: the intercept (fob's overall death rate), state (geography), and fields a kin's form did not collect.
  - Fields: all 26 shared fields (age band, sex, race, state, 6 symptoms, 10 conditions; yes vs not-yes).
- **Handover Rule:** borrowing strength = λ0 × (1 − Stranger share). The prior is fixed while the data term grows,
  so fob's own data takes over as patients arrive.
  - λ0 ∈ {1, 10, 100, 1000}, chosen per outbreak by leave-one-outbreak-out (minimum mean gap to gold over days
    0–90 on the other outbreaks). λ0 = 10 was chosen for 22 of 23 outbreaks.
- **Real only:** the same model with no borrowing (ridge). It needs at least 10 deaths and 10 survivors, as in Exp. 2/3.
- **Replay:** every outbreak with earlier kin (23), days 0–90 in steps of 2 days.
  - Test set = records entered on days 91–182; for COVID 2020, July 2020, the same as Exp. 2/3.
  - Gold = the same model class trained on every record of the outbreak outside the test window.
- **Age only:** a zero-learning baseline that ranks test patients by age.

### Results (test AUC; plateau = first day within 0.02 of gold)
| Outbreak | Gold | Age only | OS day 0 | OS day 14 | OS day 28 | Real day 28 | Plateau, real | Plateau, OS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **COVID 2020** | 0.767 | **0.727** | 0.685 | 0.681 | 0.744 | 0.743 | 34 | **30** |
| COVID 2021 | 0.716 | 0.683 | 0.646 | 0.706 | 0.709 | 0.709 | 10 | 8 |
| COVID 2022 | 0.751 | 0.657 | 0.729 | 0.739 | 0.744 | 0.744 | 8 | 4 |
| flu 2013 (only H1N1 as kin) | 0.802 | 0.664 | 0.640 | 0.565 | 0.575 | – | never | never |
| flu 2014–2020 (7 seasons) | 0.77–0.81 | 0.65–0.75 | 0.78–0.81 | 0.78–0.81 | 0.75–0.81 | mostly none | 84–88 or never | **0–6** |
| flu 2021 (during COVID) | 0.715 | 0.713 | 0.674 | 0.686 | 0.673 | – | never | 58 |
| flu 2022 | 0.775 | 0.710 | 0.771 | 0.764 | 0.774 | 0.778 | 10 | 0 |
| other virus 2013 (only H1N1 as kin) | 0.785 | 0.749 | 0.689 | 0.690 | 0.670 | – | never | never |
| other virus 2014–2022 (9 seasons) | 0.82–0.86 | 0.69–0.83 | 0.76–0.85 | 0.78–0.85 | 0.78–0.84 | mostly none | 68–76 or never | 0–58 (6 of 9 on day 0) |

- **Plateau:** OS reaches it earlier in 21 of 23 outbreaks, at the same time in 2 (neither arm got there), and later in none.
  Median plateau day: real only 51 among those that reached it (most never did within 90 days); OS 0.
- **Compared with real only on the same day,** OS is at most 0.02 worse (other virus 2021) and is up to 0.15 better.
- **Compared with age only on day 0,** OS is better in 18 of 23 outbreaks.
- In 3 seasons OS beats the gold standard, because the gold model is trained on that season's own small dataset.
- The real-only arm needs at least 10 deaths. Many seasons have fewer than that early on, so "never" often means
  "never had enough data", not "trained but poor".

### Plain reading
**Familiar outbreaks: a strong win.** For seasonal flu and other-virus seasons, OS is already at the plateau on
day 0 by borrowing from past seasons. Real data alone usually could not even train a model within 90 days.

**Novel outbreaks: the method fails where it matters most.**
- **COVID 2020** technically meets the step's target: plateau on day 30 against 34 for real data alone.
  But that is only 4 days, and on days 0–20 OS (0.655–0.685) is **worse than ranking by age** (0.727).
  - Cause: in weeks 0–2 the Kinship Vote trusted flu (the Stranger had only 4%), and flu's risk pattern beyond
    age misleads for COVID. Borrowing only helps once COVID's own data takes over (from about day 26).
- **The same failure** appears in every outbreak with a high novelty gap in Step 1: flu 2013 and other virus 2013
  (H1N1 was the only kin), and flu 2021 (flu during COVID). OS is worse than age only in all of them.
  - flu 2013 and other virus 2013 get **worse over time** (0.64 → 0.58), which needs investigating.
- **COVID 2021** starts below age only on day 0 (0.646 vs 0.683) and recovers by day 14.

**What this means for the design:** borrowing is only as good as the Kinship Vote's early call, and the Stranger
Flag is too slow to protect novel outbreaks. Candidate fixes for Step 3, not yet tested:
1. A **safe fallback**: until the vote is confident, borrow only what is shared by almost every respiratory
   outbreak (age), not every risk factor.
2. Let the **Fresh-Days Check** catch a misleading prior on fob's own newest days and weaken borrowing then.
3. Add **age only** as a permanent baseline alongside real only.

---

## 2026-10-06 — Step 1: Kinship Vote + Stranger Flag, Time Machine Replay over the Outbreak Atlas

**Code:** `src/outbreak_synth/kinship.py`, `run_kinship_replay.py`, `analyse_kinship.py`; config
`experiments/exp05_kinship_replay.toml`. Outputs: `results/exp05_kinship_replay.json` (hindsight answers),
`_weeks.csv` (weekly scores), `_votes.csv` (weekly votes), `_analysis.json` (summary).
Runtime about 4 minutes on 4 CPUs.

### How the vote works
- **Candidates:** every outbreak that started before fob, using only the records entered before fob's day 0
  (at least 200 patients and 20 deaths), plus the **Stranger**, which learns only from fob's own earlier records.
- **Scoring:** every week, each candidate predicts fob's new patients before seeing them, on two parts:
  - **profile:** how likely these patients are under the candidate's patient mix (age band, sex, core fields);
  - **severity:** who dies, after shifting the candidate's overall death rate to fob's own (Handover Rule).
- **Votes** = softmax(τ × cumulative score). τ = 0.03 was chosen by leave-one-outbreak-out (the same value
  for every held-out outbreak).
- **Fields:** only the 9 yes/no fields collected by **every** form (fever, cough, sore throat, shortness of breath;
  heart, lung, kidney, immune, metabolic/diabetes) plus age band and sex, coded yes vs not-yes.
  - Check behind this: on the 2019+ form, blank conditions mostly come with a blank "any risk factor"
    (401,243 of 529,382 blank heart-disease rows in 2020), so blank means "no".
  - Fields missing from the 2009 form are left out entirely, so the form cannot make outbreaks look unrelated.
- **Groups for scoring:** flu (including H1N1), other respiratory virus, COVID. The vote never sees these labels;
  they are only used to score it.

### Hindsight answers (fit on each outbreak's full data)
- Flu seasons are closest to earlier flu seasons, other-virus seasons to other-virus seasons, and COVID 2021 to COVID 2020.
- **Novelty gap** = how much better fob's own model fits than its best kin (nats per patient):
  - familiar seasons: 0.01–0.07;
  - pandemic-era seasons: other virus 2020–21 0.26–0.28, flu 2021 0.48;
  - outbreaks whose only possible kin was H1N1: flu 2013 0.99, other virus 2013 1.76;
  - **COVID 2020: 1.10**.
- COVID 2022 (Omicron) is closest in hindsight to **flu 2021**, not COVID 2021 (novelty gap 0.30).

### Right group? (23 replayed outbreaks; 21 have an earlier member of their own group)
| Week | Top group correct | Average vote for the true group | Exact best single kin |
|---:|---:|---:|---:|
| 1 | 81% | 0.66 | 52% |
| 2 | 81% | 0.70 | 52% |
| 4 | 90% | 0.80 | 57% |
| 8 | 100% | 0.92 | 70% |
| 13 | 100% | 0.98 | 78% |
| 25 | 95% | 0.96 | 83% |

- The patient-profile part does most of the work: profile alone gets the group right 90% of the time at week 4,
  severity alone 67%.
- The exact best single season is much harder (52–83%), because seasons within a group are near-ties.
  Choosing within a group is left to the Fresh-Days Check, as planned.

### Honest confidence? (group level, all weeks)
| Vote for top group | Cases | Average said | Actually right |
|---|---:|---:|---:|
| 0.40–0.60 | 38 | 0.55 | 0.66 |
| 0.60–0.80 | 71 | 0.70 | 0.93 |
| 0.80–0.95 | 42 | 0.88 | 0.93 |
| 0.95–1.00 | 394 | 0.998 | 0.992 |

When OS is sure, it is right. When it hedges, it is right **more often** than it says (under-confident),
which is the safe direction.

### Stranger Flag
| Outbreak | Novelty gap | Week the Stranger first wins | Patients by then |
|---|---:|---:|---:|
| other virus 2013 (only H1N1 to compare with) | 1.76 | 0 | 2 |
| flu 2013 (only H1N1 to compare with) | 0.99 | 6 | 27 |
| flu 2021 (flu during COVID) | 0.48 | 18 | 254 |
| **COVID 2020** | **1.10** | **3** | **749** |
| other virus 2021 | 0.28 | 8 | 1,738 |
| flu 2015–2018, familiar seasons | 0.04–0.05 | 13–24, or never | 1,974–3,725, or never |
| COVID 2022 | 0.30 | 2 | 17,562 |
| COVID 2021 | 0.06 | 9 | 183,742 |
| 10 other familiar seasons | 0.01–0.07 | never in 26 weeks | – |

- Rank correlation between the novelty gap and "fewer patients before the Stranger wins": **0.67**.
- **COVID 2020 timeline:**

| Week | Patients | Stranger | Vote |
|---:|---:|---:|---|
| 0 | 2 | 4% | 57% flu |
| 2 | 39 | 4% | 87% flu (closest: flu 2019) |
| 3 | 749 | 52% | – |
| 4 | 3,538 | 100% | – |

### Plain reading
- **What works:** the vote finds the right group in 90% of outbreaks by week 4 and in all of them by week 8.
  Its high-confidence calls are right 99% of the time, and it flags COVID 2020 as new by week 3.
- **Limits:**
  - With fewer than about 40 patients, OS called COVID 2020 "flu-like". The Stranger needs a few hundred patients to win.
  - In familiar seasons the Stranger also wins eventually, after about 2,000 patients, because fob's own data
    becomes enough. So the flag is "the Stranger wins **early**". The cut-off is not tuned yet.
- **Caveats:** 23 outbreaks but 3 groups, with COVID the only truly new disease after 2009, so these numbers
  are encouraging, not proof. The groups used for scoring are lab-defined; the vote itself does not use them.
- **Next:** the Two-Part Recipe and Handover Rule (step 2), using these votes to decide what to borrow.

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
