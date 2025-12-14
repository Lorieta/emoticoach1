import pandas as pd
import matplotlib.pyplot as plt

# Load and Clean Data
df = pd.read_csv('SECCUE.xlsx')

def clean_label(val):
    if pd.isna(val): return "Unknown"
    val = str(val).strip()
    if val == 'Suprise': return 'Surprise'
    if val == 'Angry': return 'Anger'
    return val.capitalize()

df_clean = pd.DataFrame()
df_clean['Psych'] = df['Psychiatrist Answer MELD FORMAT'].apply(clean_label)
df_clean['Dom'] = df['Dominant MELD FORMAT'].apply(clean_label)
df_clean['Kimi'] = df['Kimi 2 MELD Format'].apply(clean_label)

# Define Logic for Chart 1 (Psych Perspective)
def cat_psych(row):
    if row['Kimi'] == row['Psych']: return 'Agrees with Expert'
    if row['Kimi'] == row['Dom']: return 'Agrees with Crowd (Error)'
    return 'Agrees with Neither'

# Define Logic for Chart 2 (Dom Perspective)
def cat_dom(row):
    if row['Kimi'] == row['Dom']: return 'Agrees with Crowd'
    if row['Kimi'] == row['Psych']: return 'Agrees with Expert (Error)'
    return 'Agrees with Neither'

# Calculate Counts
counts_psych = df_clean.apply(cat_psych, axis=1).value_counts()
counts_dom = df_clean.apply(cat_dom, axis=1).value_counts()

# Plotting
fig, axes = plt.subplots(1, 2, figsize=(14, 7))

# Chart 1
axes[0].pie(counts_psych, labels=counts_psych.index, autopct='%1.1f%%', 
            colors=['#99ff99', '#ffcc99', '#ff9999'], startangle=140)
axes[0].set_title('Benchmark: Psychiatrist (Expert)')

# Chart 2
axes[1].pie(counts_dom, labels=counts_dom.index, autopct='%1.1f%%', 
            colors=['#99ff99', '#66b3ff', '#ff9999'], startangle=140)
axes[1].set_title('Benchmark: Dominant (Consensus)')

plt.tight_layout()
plt.savefig('kimi_alignment_separate_pies.png')
plt.show()