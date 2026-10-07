# outbreak-synth

Disease-aware synthetic data for early outbreaks. The question: can a model that has studied
past outbreaks look at a new disease's first few hundred records, match them to similar past
diseases, and pick the synthetic-data generator (and settings) that most improves downstream AUC?

Status and numbers live in [RESULTS.md](RESULTS.md).

## Layout
- `data/` raw and derived data (git-ignored, never committed)
- `scripts/` data download scripts (pinned releases, SHA-256 recorded)
- `src/outbreak_synth/` library code
- `experiments/` one config per experiment
- `results/` small machine-readable outputs

## Reproduce
```bash
pip install -r requirements.txt
./scripts/download_srag.sh                 # ~260 MB, Brazilian SIVEP-Gripe SRAG 2019-2022
./scripts/download_srag_historic.sh        # ~90 MB, SRAG 2009-2018
PYTHONPATH=src python -m outbreak_synth.library   # harmonised outbreak library
PYTHONPATH=src python -m outbreak_synth.inspect_srag
PYTHONPATH=src python -m outbreak_synth.run_real_only experiments/exp01_real_only.toml
PYTHONPATH=src python -m outbreak_synth.run_days_to_plateau experiments/exp02_days_to_plateau.toml
PYTHONPATH=src python -m outbreak_synth.run_replay_real experiments/exp03_replay_real.toml
PYTHONPATH=src python -m outbreak_synth.run_prior_probe experiments/exp04_prior_probe.toml
PYTHONPATH=src python -m outbreak_synth.run_kinship_replay experiments/exp05_kinship_replay.toml
PYTHONPATH=src python -m outbreak_synth.analyse_kinship exp05_kinship_replay
PYTHONPATH=src python -m outbreak_synth.run_recipe_replay experiments/exp06_recipe_replay.toml   # ~20 min
PYTHONPATH=src python -m outbreak_synth.analyse_recipe exp06_recipe_replay
PYTHONPATH=src python -m outbreak_synth.run_kinship_replay experiments/exp05b_kinship_replay.toml
PYTHONPATH=src python -m outbreak_synth.analyse_kinship exp05b_kinship_replay
PYTHONPATH=src python -m outbreak_synth.run_os_replay experiments/exp07_os_replay.toml   # ~25 min
PYTHONPATH=src python -m outbreak_synth.analyse_os exp07_os_replay
PYTHONPATH=src python -m outbreak_synth.run_os_replay2 experiments/exp08_os_replay.toml   # ~40 min
PYTHONPATH=src python -m outbreak_synth.analyse_os2 exp08_os_replay
PYTHONPATH=src python -c "from outbreak_synth.analyse_os2 import offline_variants; offline_variants('exp08_os_replay')"
python3 -m venv .venv-ctgan && .venv-ctgan/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.1 \
  && .venv-ctgan/bin/pip install -r requirements-ctgan.txt          # isolated env for the CTGAN baseline
PYTHONPATH=src python -m outbreak_synth.run_synth_release experiments/exp09_synth_release.toml   # ~45 min
PYTHONPATH=src python -m outbreak_synth.run_synth_release experiments/exp10_synth_chain.toml   # dependency-chain generator
PYTHONPATH=src python -m outbreak_synth.glass_box covid_2020 14 44   # Glass Box reports -> reports/
# Out-of-country test (Mexico COVID-19 2020/2021)
./scripts/download_mexico.sh && (cd data/raw/mexico && mkdir -p extracted && cd extracted && unzip -o ../COVID19MEXICO2020.zip && unzip -o ../COVID19MEXICO2021.zip && unzip -o ../diccionario_datos_abiertos.zip)
PYTHONPATH=src python -m outbreak_synth.library --intl                     # -> data/processed/library_intl.parquet
export OUTBREAK_LIB=data/processed/library_intl.parquet
PYTHONPATH=src python -m outbreak_synth.run_kinship_replay experiments/exp11_kinship_mexico.toml
PYTHONPATH=src python -m outbreak_synth.run_os_replay2 experiments/exp11_os_mexico.toml
PYTHONPATH=src python -m outbreak_synth.run_synth_release experiments/exp12_synth_mexico.toml
# Vote-only test on small line lists (Ebola 2014, H7N9 2013, MERS 2015)
./scripts/download_small.sh && PYTHONPATH=src python -m outbreak_synth.library --small
export OUTBREAK_LIB=data/processed/library_small.parquet
PYTHONPATH=src python -m outbreak_synth.run_kinship_replay experiments/exp13_vote_small.toml
PYTHONPATH=src python -m outbreak_synth.run_kinship_replay experiments/exp13b_vote_small_present.toml
PYTHONPATH=src python -m outbreak_synth.analyse_vote_small exp13_vote_small exp13b_vote_small_present
```

## Data sources
- SIVEP-Gripe SRAG (severe acute respiratory illness) notifications, Ministério da Saúde, Brazil.
  Dataset `srag-2019-a-2026` on https://dadosabertos.saude.gov.br, license CC-BY.
  Release `23-03-2026` for the 2019-2022 files. Data dictionary: `dicionario-de-dados-2019-a-2025.pdf`.
  Datasets `srag-2009-2012` and `srag-2013-2018` (CC-BY) for the historic outbreaks.
- Mexico COVID-19 open data (SISVER), Secretaría de Salud / Dirección General de Epidemiología, year-closure files
  2020 and 2021, under the DGE Términos de Libre Uso de Datos Abiertos.

## What we are building (OS)
Outbreak Synth is a general method: it studies the past, follows something new day by day, says when
it understands it well enough, and only then generates synthetic data. Two case studies:
1. Early outbreak data (in progress): Brazilian SRAG outbreaks 2009-2022.
2. Vaccine side-effect signals (planned): replay known signals week by week.

Plain-language plan: [docs/outbreak-synth-plan.pdf](docs/outbreak-synth-plan.pdf) (built by `scripts/make_plan_pdf.py`).
