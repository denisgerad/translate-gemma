**Combined Evaluation Summary**

Summary table combining automatic and human ratings (generated from `combined_summary.csv`).

| Language | BLEU | chrF | chrF (1-5) | Accuracy | Fluency | Register | Cultural naturalness | Metaphor retention | Human mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Kannada | N/A | N/A | N/A | 4 | 3 | 4 | 3 | 4 | 3.6 |
| Malayalam | 1.53 | 28.46 | 1 | 4 | 3 | 4 | 3 | 4 | 3.6 |
| Tamil | 1.67 | 36.31 | 2 | 4 | 4 | 4 | 4 | 4 | 4.0 |
| Telugu | 1.58 | 24.23 | 1 | 4 | 3 | 4 | 3 | 3 | 3.4 |

Notes
- BLEU/chrF: automatic metrics computed by `tools/evaluate_auto.py`. Low values are expected for single-sentence evaluation; prefer larger test sets.
- `chrF (1-5)`: coarse mapping of chrF to a 1–5 scale (see `tools/map_auto_scores.py`).
- Human ratings: averaged scores from `my-docs/evaluation.md` written into `human_scores_agg.csv`.

Quick actions
- Re-generate combined CSV: `python tools/merge_scores.py`
- Re-run automatic metrics (after adding more reference lines): `python tools/evaluate_auto.py`
- Export `combined_summary.csv` to Google Sheets or HTML on request.
