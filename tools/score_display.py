import json
from pathlib import Path
import sacrebleu
import csv
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.qa_checks import qa_checks
batch_path = ROOT / 'batch_output.json'
refs_dir = ROOT / 'refs'
out_csv = ROOT / 'scoring_display.csv'

langs = ['Malayalam', 'Kannada', 'Tamil', 'Telugu', 'Hindi']

if not batch_path.exists():
    print('batch_output.json not found')
    raise SystemExit(1)

raw = json.loads(batch_path.read_text(encoding='utf8'))
data = [d for d in raw if d.get('input', {}).get('meta', {}).get('translate', True) is not False]

rows = []
for L in langs:
    ref_file = refs_dir / f"{L.lower()}.txt"
    if not ref_file.exists():
        print(f'No reference for {L}; skipping')
        continue
    ref_lines = [l.rstrip('\n') for l in ref_file.read_text(encoding='utf8').splitlines() if l.strip()!='']
    cand_lines = [item.get('translation', {}).get(L, '').strip() for item in data]
    # pairwise length check
    if len(ref_lines) != len(cand_lines):
        print(f'Length mismatch for {L}: refs {len(ref_lines)} vs cands {len(cand_lines)}; truncating to min')
    n = min(len(ref_lines), len(cand_lines))
    ref_lines = ref_lines[:n]
    cand_lines = cand_lines[:n]

    # automatic metrics
    bleu = sacrebleu.corpus_bleu(cand_lines, [ref_lines]).score
    chrf = sacrebleu.corpus_chrf(cand_lines, [ref_lines]).score

    # map chrF to 1-5 meaning accuracy (reuse mapping from map_auto_scores)
    def chrF_to_1_5(ch):
        try:
            ch = float(ch)
        except Exception:
            return 1
        if ch >= 60:
            return 5
        if ch >= 50:
            return 4
        if ch >= 40:
            return 3
        if ch >= 30:
            return 2
        return 1

    meaning = chrF_to_1_5(chrf)

    # completeness: length ratio average
    ratios = []
    for r,c in zip(ref_lines, cand_lines):
        lr = (len(c) / max(1, len(r))) if r else 0
        ratios.append(lr)
    avg_ratio = sum(ratios)/len(ratios) if ratios else 0
    if avg_ratio >= 0.95:
        completeness = 5
    elif avg_ratio >= 0.90:
        completeness = 4
    elif avg_ratio >= 0.80:
        completeness = 3
    elif avg_ratio >= 0.60:
        completeness = 2
    else:
        completeness = 1

    # QA checks aggregated per language
    qa_issues = []
    for src, cand in zip([d.get('input',{}).get('text','') for d in data][:n], cand_lines):
        qa_issues.extend(qa_checks(src, cand, L))
    qa_issues = list(set(qa_issues))

    # fluency heuristic: if PROMPT_LEAKAGE or ENGLISH_WORDS_PRESENT -> low
    if 'PROMPT_LEAKAGE' in qa_issues or 'ENGLISH_WORDS_PRESENT' in qa_issues:
        fluency = 2
    else:
        # use chrF as proxy for fluency too
        fluency = meaning if meaning >=3 else 3

    # register & tone: approximate by chrF mapping
    register = meaning

    # metaphor handling: approximate by meaning
    metaphor = meaning

    # grammar: penalize if many English words or odd punctuation
    if 'ENGLISH_WORDS_PRESENT' in qa_issues:
        grammar = max(1, meaning-1)
    else:
        grammar = min(5, meaning+0)

    human_proxy_mean = round((meaning+completeness+fluency+register+metaphor+grammar)/6,2)

    rows.append({
        'language': L,
        'BLEU': round(bleu,2),
        'chrF': round(chrf,2),
        'meaning_1_5': meaning,
        'completeness_1_5': completeness,
        'fluency_1_5': fluency,
        'register_1_5': register,
        'metaphor_1_5': metaphor,
        'grammar_1_5': grammar,
        'human_proxy_mean': human_proxy_mean,
        'qa_issues': ';'.join(qa_issues)
    })

# write CSV
with open(out_csv, 'w', newline='', encoding='utf8') as f:
    fieldnames = ['language','BLEU','chrF','meaning_1_5','completeness_1_5','fluency_1_5','register_1_5','metaphor_1_5','grammar_1_5','human_proxy_mean','qa_issues']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print('Wrote', out_csv)
print('\nSummary:')
for r in rows:
    print(f"{r['language']}: meaning={r['meaning_1_5']} completeness={r['completeness_1_5']} fluency={r['fluency_1_5']} register={r['register_1_5']} metaphor={r['metaphor_1_5']} grammar={r['grammar_1_5']} mean={r['human_proxy_mean']} QA={r['qa_issues']}")
