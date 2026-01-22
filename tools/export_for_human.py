import json
from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
data_path = ROOT / 'batch_output.json'
refs_dir = ROOT / 'refs'
out_csv = ROOT / 'for_raters.csv'

langs = ['Malayalam', 'Kannada', 'Tamil', 'Telugu']

if not data_path.exists():
    print('batch_output.json not found in', ROOT)
    sys.exit(1)

raw = json.loads(data_path.read_text(encoding='utf8'))
# filter out items marked as not to be translated
data = [d for d in raw if d.get('input', {}).get('meta', {}).get('translate', True) is not False]

rows = []
for idx, item in enumerate(data):
    src = item.get('input', {}).get('text', '').strip()
    for L in langs:
        ref_file = refs_dir / f"{L.lower()}.txt"
        ref_line = ''
        if ref_file.exists():
            ref_lines = [l for l in ref_file.read_text(encoding='utf8').splitlines() if l.strip()!='']
            if idx < len(ref_lines):
                ref_line = ref_lines[idx].strip()
        cand = item.get('translation', {}).get(L, '').strip()
        rows.append({'id': f'{idx+1}', 'language': L, 'source': src, 'reference': ref_line, 'candidate': cand})

with open(out_csv, 'w', newline='', encoding='utf8') as f:
    writer = csv.DictWriter(f, fieldnames=['id','language','source','reference','candidate'])
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print('Wrote', out_csv)
