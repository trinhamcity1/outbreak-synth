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
PYTHONPATH=src python -m outbreak_synth.inspect_srag
```

## Data sources
- SIVEP-Gripe SRAG (severe acute respiratory illness) notifications, Ministério da Saúde, Brazil.
  Dataset `srag-2019-a-2026` on https://dadosabertos.saude.gov.br, license CC-BY.
  Release `23-03-2026` for the 2019-2022 files. Data dictionary: `dicionario-de-dados-2019-a-2025.pdf`.
