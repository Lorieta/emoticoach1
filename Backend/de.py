import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import os

# 1. Load the Dataset
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'SECCUE.xlsx')
df = pd.read_excel(file_path)

# 2. Configuration & Data Cleaning
# ------------------------------
psych_col = 'Psychiatrist Answer MELD FORMAT'
dom_col = 'Dominant MELD FORMAT'
kimi_col = 'Kimi 2 MELD Format'

def clean_label(val):
    if pd.isna(val): return "Unknown"
    val = str(val).strip()
    # Fix typos found in the dataset
    if val == 'Suprise': return 'Surprise'
    if val == 'Angry': return 'Anger'
    return val.capitalize()

# Create a clean DataFrame for analysis
df_clean = pd.DataFrame()
df_clean['Story_ID'] = df['Item']
df_clean['Psych'] = df[psych_col].apply(clean_label)
df_clean['Dom'] = df[dom_col].apply(clean_label)
df_clean['Kimi'] = df[kimi_col].apply(clean_label)

# 3. Calculate Overall Accuracy
# ---------------------------
acc_psych = (df_clean['Kimi'] == df_clean['Psych']).mean()
acc_dom = (df_clean['Kimi'] == df_clean['Dom']).mean()

print(f"--- Overall Accuracy ---")
print(f"Kimi vs. Psychologist (Expert): {acc_psych:.2%}")
print(f"Kimi vs. Dominant (Consensus):  {acc_dom:.2%}\n")

# Plot 1: Overall Accuracy Comparison
plt.figure(figsize=(8, 6))
bars = plt.bar(['vs. Psychologist\n(Expert)', 'vs. Dominant\n(Consensus)'], 
               [acc_psych, acc_dom], 
               color=['#1f77b4', '#2ca02c'], width=0.6)
plt.title('Kimi 2 Overall Accuracy', fontsize=16)
plt.ylabel('Accuracy')
plt.ylim(0, 1.0)
# Add labels
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
             f'{height:.1%}', ha='center', va='bottom', fontsize=12, fontweight='bold')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.savefig('kimi_overall_accuracy.png')
plt.close()

# 4. Calculate Accuracy per Emotion
# -------------------------------
emotions = sorted(list(set(df_clean['Psych'].unique()) | set(df_clean['Dom'].unique())))
if 'Unknown' in emotions: emotions.remove('Unknown')

acc_data = []
for emotion in emotions:
    # Kimi accuracy when Expert says X
    sub_psych = df_clean[df_clean['Psych'] == emotion]
    score_psych = (sub_psych['Kimi'] == sub_psych['Psych']).mean() if len(sub_psych) > 0 else 0
    
    # Kimi accuracy when Crowd says X
    sub_dom = df_clean[df_clean['Dom'] == emotion]
    score_dom = (sub_dom['Kimi'] == sub_dom['Dom']).mean() if len(sub_dom) > 0 else 0
    
    acc_data.append({
        'Emotion': emotion, 
        'vs. Psychologist': score_psych, 
        'vs. Dominant': score_dom
    })

df_acc = pd.DataFrame(acc_data).set_index('Emotion')

# Plot 2: Accuracy by Emotion Grouped Bar Chart
ax = df_acc.plot(kind='bar', figsize=(12, 6), color=['#1f77b4', '#2ca02c'], width=0.8)
plt.title('Kimi 2 Accuracy by Emotion Category', fontsize=16)
plt.ylabel('Accuracy')
plt.ylim(0, 1.1)
plt.legend(title='Ground Truth Source')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig('kimi_emotion_accuracy.png')
plt.close()

print("--- Accuracy per Emotion Table ---")
print(df_acc.round(2))
print("\n")

# 5. Generate Disputed Cases Table (Who does Kimi agree with?)
# --------------------------------------------------------
disputed_mask = df_clean['Psych'] != df_clean['Dom']
disputed_df = df_clean[disputed_mask].copy()

def check_alignment(row):
    if row['Kimi'] == row['Psych']: return 'Agrees with Psych'
    if row['Kimi'] == row['Dom']: return 'Agrees with Dom'
    return 'Agrees with Neither'

disputed_df['Alignment'] = disputed_df.apply(check_alignment, axis=1)

print("--- Disputed Cases Analysis (Psych vs Dom Disagreement) ---")
print(disputed_df[['Story_ID', 'Psych', 'Dom', 'Kimi', 'Alignment']].to_string(index=False))

# Count alignment summary
alignment_counts = disputed_df['Alignment'].value_counts()
print("\nSummary of Kimi's Allegiance:")
print(alignment_counts)