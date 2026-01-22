import csv
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
out_file = ROOT / 'human_scores.csv'
agg_file = ROOT / 'human_scores_agg.csv'

# Human ratings provided earlier (1-5 scale)
rows = [
    {'language':'Malayalam','Accuracy':4,'Fluency':3,'Register':4,'Cultural_naturalness':3,'Metaphor_retention':4},
    {'language':'Kannada','Accuracy':4,'Fluency':3,'Register':4,'Cultural_naturalness':3,'Metaphor_retention':4},
    {'language':'Tamil','Accuracy':4,'Fluency':4,'Register':4,'Cultural_naturalness':4,'Metaphor_retention':4},
    {'language':'Telugu','Accuracy':4,'Fluency':3,'Register':4,'Cultural_naturalness':3,'Metaphor_retention':3},
]

with open(out_file, 'w', newline='', encoding='utf8') as f:
    writer = csv.DictWriter(f, fieldnames=['language','Accuracy','Fluency','Register','Cultural_naturalness','Metaphor_retention'])
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

df = pd.DataFrame(rows)
df.set_index('language', inplace=True)
df.to_csv(agg_file)
print('Wrote', out_file, 'and', agg_file)
