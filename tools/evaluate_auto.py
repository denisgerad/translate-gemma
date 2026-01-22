import json
from pathlib import Path
import csv
import sys

try:
    import sacrebleu
except Exception:
    print('sacrebleu not installed. Install with: pip install sacrebleu')
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
data_path = ROOT / 'batch_output.json'
refs_dir = ROOT / 'refs'
out_csv = ROOT / 'auto_scores.csv'

langs = ['Malayalam', 'Kannada', 'Tamil', 'Telugu']

if not data_path.exists():
    print('batch_output.json not found in', ROOT)
    sys.exit(1)

raw = json.loads(data_path.read_text(encoding='utf8'))
# filter out items marked as not to be translated (meta.translate == False)
data = [d for d in raw if d.get('input', {}).get('meta', {}).get('translate', True) is not False]

results = []
for L in langs:
    ref_file = refs_dir / f"{L.lower()}.txt"
    if not ref_file.exists():
        print(f'No reference file for {L} at {ref_file}; skipping automatic metrics for this language.')
        continue
    ref_lines = [l.rstrip('\n') for l in ref_file.read_text(encoding='utf8').splitlines() if l.strip()!='']
    cand_lines = []
    for item in data:
        cand = item.get('translation', {}).get(L, '').strip()
        cand_lines.append(cand)

    if len(ref_lines) != len(cand_lines):
        print(f'Reference length ({len(ref_lines)}) and candidate length ({len(cand_lines)}) differ for {L}; skipping.')
        continue

    bleu = sacrebleu.corpus_bleu(cand_lines, [ref_lines])
    chrf = sacrebleu.corpus_chrf(cand_lines, [ref_lines])
    results.append({'lang': L, 'BLEU': round(bleu.score, 2), 'chrF': round(chrf.score, 2)})
    print(f'{L}: BLEU={bleu.score:.2f}, chrF={chrf.score:.2f}')

if results:
    with open(out_csv, 'w', newline='', encoding='utf8') as f:
        writer = csv.DictWriter(f, fieldnames=['lang','BLEU','chrF'])
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    print('Wrote', out_csv)
else:
    print('No automatic scores computed.')
