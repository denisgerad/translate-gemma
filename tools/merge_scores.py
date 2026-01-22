import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
auto_path = ROOT / 'auto_scores_rated.csv'
human_path = ROOT / 'human_scores_agg.csv'
out_path = ROOT / 'combined_summary.csv'

auto_df = pd.read_csv(auto_path) if auto_path.exists() else pd.DataFrame()
human_df = pd.read_csv(human_path) if human_path.exists() else pd.DataFrame()

if auto_df.empty and human_df.empty:
    print('No input score files found.')
    raise SystemExit(1)

# Normalize language column names
if 'lang' in auto_df.columns:
    auto_df = auto_df.rename(columns={'lang':'language'})

# ensure human df has 'language' column
if 'language' not in human_df.columns and 'language' in human_df.index.names:
    human_df = human_df.reset_index()

# Merge on language
combined = pd.merge(auto_df, human_df, on='language', how='outer')

# Compute human mean if human metrics exist
human_metrics = ['Accuracy','Fluency','Register','Cultural_naturalness','Metaphor_retention']
if all(col in combined.columns for col in human_metrics):
    combined['human_mean'] = combined[human_metrics].mean(axis=1).round(2)

combined.to_csv(out_path, index=False)
print('Wrote', out_path)
