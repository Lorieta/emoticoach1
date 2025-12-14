import pandas as pd
import matplotlib.pyplot as plt

# 1. Load the Data
file_path = 'SECCUE.xlsx - Sheet1.csv'
df = pd.read_csv(file_path)

# 2. Define Columns & Clean Data
psych_col = 'Psychiatrist Answer MELD FORMAT'
dom_col = 'Dominant MELD FORMAT'
kimi_col = 'Kimi 2 MELD Format'

def clean_label(val):
    if pd.isna(val): return "Unknown"
    val = str(val).strip()
    # Fix dataset typos
    if val == 'Suprise': return 'Surprise'
    if val == 'Angry': return 'Anger'
    return val.capitalize()

# Create a simplified DataFrame
df_clean = pd.DataFrame()
df_clean['Psych'] = df[psych_col].apply(clean_label)
df_clean['Dom'] = df[dom_col].apply(clean_label)
df_clean['Kimi'] = df[kimi_col].apply(clean_label)

# 3. Categorize Alignment
def categorize(row):
    k = row['Kimi']
    p = row['Psych']
    d = row['Dom']
    
    if k == p and k == d:
        return 'Overlap (All Agree)'
    elif k == p and k != d:
        return 'Only Psych'
    elif k == d and k != p:
        return 'Only Dominant'
    else:
        return 'Only AI (No Agreement)'

df_clean['Category'] = df_clean.apply(categorize, axis=1)
counts = df_clean['Category'].value_counts()

# 4. Plot the Pie Chart
plt.figure(figsize=(9, 9))

# Define colors: Blue (All), Green (Crowd), Orange (Expert), Red (None)
colors = ['#66b3ff', '#99ff99', '#ffcc99', '#ff9999']
explode = [0.05] * len(counts) # Slightly separate all slices

wedges, texts, autotexts = plt.pie(
    counts, 
    labels=counts.index, 
    autopct='%1.1f%%', 
    startangle=140, 
    colors=colors, 
    explode=explode,
    textprops=dict(color="black", fontsize=12),
    pctdistance=0.85
)

# Add Title
plt.title('Kimi 2 Prediction', fontsize=16)

# Save and Show
plt.tight_layout()
plt.savefig('kimi_alignment_pie_chart.png')
plt.show()

# Print the raw numbers for your text
print("--- Raw Counts ---")
print(counts)