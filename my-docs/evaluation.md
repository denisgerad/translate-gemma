**Evaluation Summary**

Source: `my-docs/reference.txt` (literary / Tharoor-style sentence)
Outputs: `batch_output.json`

Ratings (1–5): Accuracy, Fluency, Register, Cultural naturalness, Metaphor retention

- **Malayalam**: 4 / 3 / 4 / 3 / 4
- **Kannada**: 4 / 3 / 4 / 3 / 4
- **Tamil**: 4 / 4 / 4 / 4 / 4
- **Telugu**: 4 / 3 / 4 / 3 / 3

Notes:
- Scores are human ratings based on comparison with the gold references in `my-docs/reference.txt`.
- Malayalam and Tamil show the strongest fluency and register; Kannada and Telugu are accurate but slightly less idiomatic.
- Recommendations: try stronger prompt templates (explicitly preserve metaphors/register and include an example), or evaluate an alternate model for improved Kannada/Telugu quality.

Commands
- Run batch (use `translategemma:4b` or set `OLLAMA_MODEL`):

```powershell
$env:OLLAMA_MODEL='translategemma:4b'
python translate_gemma.py batch.json
```

Files of interest:
- `my-docs/reference.txt` — human reference translations
- `batch.json` — input batch
- `batch_output.json` — model outputs
