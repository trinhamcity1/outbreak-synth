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
```

## Data sources
- SIVEP-Gripe SRAG (severe acute respiratory illness) notifications, Ministério da Saúde, Brazil.
  Dataset `srag-2019-a-2026` on https://dadosabertos.saude.gov.br, license CC-BY.
  Release `23-03-2026` for the 2019-2022 files. Data dictionary: `dicionario-de-dados-2019-a-2025.pdf`.
  Datasets `srag-2009-2012` and `srag-2013-2018` (CC-BY) for the historic outbreaks.

## What we are building (OS)
A learner that has studied past outbreaks, is fed a new disease's records day by day, says when it
understands the disease well enough, and only then generates synthetic patient data for it.
