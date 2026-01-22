import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
auto_path = ROOT / 'auto_scores.csv'
out_path = ROOT / 'auto_scores_rated.csv'

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

if not auto_path.exists():
    print('auto_scores.csv not found at', auto_path)
    raise SystemExit(1)

df = pd.read_csv(auto_path)
df['chrF_1to5'] = df['chrF'].apply(chrF_to_1_5)
df.to_csv(out_path, index=False)
print('Wrote', out_path)
