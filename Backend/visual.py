import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import cohen_kappa_score
import os

# 1. Setup and Load Data
# ----------------------
file_path = os.path.join(os.path.dirname(__file__), 'SECCUE.xlsx')
df = pd.read_excel(file_path)

# Define columns
psych_col = 'Psychiatrist Answer MELD FORMAT'
dom_col = 'Dominant MELD FORMAT'
model_cols = {
    'Kimi 2': 'Kimi 2 MELD Format',
    'OpenAI GPT-OSS': 'openai/gpt-oss-120b (reasoning).2',
    'Llama 4 Scout': 'groq/compound(reasoning).2'
}

# 2. Data Cleaning
# ----------------
def clean_label(val):
    if pd.isna(val): return "Unknown"
    val = str(val).strip()
    # Standardize typos and casing
    if val == 'Suprise': return 'Surprise'
    if val == 'Angry': return 'Anger'
    return val.capitalize()

# Create a clean DataFrame for analysis
df_clean = pd.DataFrame()
df_clean['Item'] = df['Item']
df_clean['Psych'] = df[psych_col].apply(clean_label)
df_clean['Dom'] = df[dom_col].apply(clean_label)

for m, c in model_cols.items():
    df_clean[m] = df[c].apply(clean_label)

# 3. Calculate Human Agreement Stats
# ----------------------------------
agreement_rate = (df_clean['Psych'] == df_clean['Dom']).mean()
kappa = cohen_kappa_score(df_clean['Psych'], df_clean['Dom'])

print(f"--- Human Baseline Stats ---")
print(f"Psychiatrist-Dominant Agreement: {agreement_rate:.2%}")
print(f"Cohen's Kappa: {kappa:.3f}\n")

# 4. Compare AI Accuracy (Psych vs. Dominant)
# -------------------------------------------
results = []
for model in model_cols.keys():
    acc_psych = (df_clean[model] == df_clean['Psych']).mean()
    acc_dom = (df_clean[model] == df_clean['Dom']).mean()
    results.append({
        'Model': model, 
        'vs_Psychiatrist': acc_psych, 
        'vs_Dominant': acc_dom
    })

df_results = pd.DataFrame(results).set_index('Model')
print("--- AI Model Accuracy ---")
print(df_results)
print("\n")

# Plot 1: Accuracy Comparison Chart
ax = df_results.plot(kind='bar', figsize=(10, 6), color=['skyblue', 'salmon'], width=0.7)
plt.title('AI Model Performance: Expert vs. Consensus', fontsize=14)
plt.ylabel('Accuracy')
plt.ylim(0, 1.05)
plt.xticks(rotation=0)
plt.legend(title="Ground Truth Source")
plt.grid(axis='y', linestyle='--', alpha=0.5)

# Add numerical labels on bars
for container in ax.containers:
    ax.bar_label(container, fmt='%.2f')

plt.tight_layout()
plt.savefig('comparison_psych_vs_dom.png')
print("Generated Plot: comparison_psych_vs_dom.png")
plt.close()

# 5. Analyze "Disputed Cases"
# ---------------------------
# Isolate stories where Expert and Consensus disagree
disputed_mask = df_clean['Psych'] != df_clean['Dom']
disputed_df = df_clean[disputed_mask].copy()

print(f"--- Disputed Cases Analysis ---")
print(f"Number of stories where Expert and Crowd disagree: {len(disputed_df)}")

# Calculate alignment for these specific stories
alignment_stats = {model: {'Agrees with Psych': 0, 'Agrees with Dom': 0, 'Agrees with Neither': 0} 
                   for model in model_cols}

for idx, row in disputed_df.iterrows():
    for model in model_cols:
        pred = row[model]
        if pred == row['Psych']:
            alignment_stats[model]['Agrees with Psych'] += 1
        elif pred == row['Dom']:
            alignment_stats[model]['Agrees with Dom'] += 1
        else:
            alignment_stats[model]['Agrees with Neither'] += 1

df_align = pd.DataFrame(alignment_stats).T
print("\nAlignment Stats (in disputed cases):")
print(df_align)

# Plot 2: Alignment Stacked Bar Chart
# Green = Sides with Expert, Red = Sides with Crowd
colors = ['#2ca02c', '#d62728', '#7f7f7f'] 
df_align.plot(kind='bar', stacked=True, figsize=(10, 6), color=colors)
plt.title('Who does AI agree with when Expert and Crowd disagree?', fontsize=14)
plt.ylabel('Number of Stories')
plt.xticks(rotation=0)
plt.legend(title="Alignment")
plt.tight_layout()
plt.savefig('alignment_disputed_cases.png')
print("Generated Plot: alignment_disputed_cases.png")
plt.close()

# 6. Visual Scorecard (Heatmap)
# -----------------------------
# Create matrices where 1 = Correct, 0 = Incorrect

# vs Psychiatrist
scorecard_data_psych = {}
for model in model_cols.keys():
    scorecard_data_psych[model] = (df_clean[model] == df_clean['Psych']).astype(int)
df_scorecard_psych = pd.DataFrame(scorecard_data_psych)
df_scorecard_psych.index = df_clean['Item']

# vs Dominant
scorecard_data_dom = {}
for model in model_cols.keys():
    scorecard_data_dom[model] = (df_clean[model] == df_clean['Dom']).astype(int)
df_scorecard_dom = pd.DataFrame(scorecard_data_dom)
df_scorecard_dom.index = df_clean['Item']

# Plot Heatmaps Side-by-Side
fig, axes = plt.subplots(1, 2, figsize=(12, 10), sharey=True)

sns.heatmap(df_scorecard_psych, ax=axes[0], annot=False, cmap='RdYlGn', cbar=False, 
            linewidths=0.5, linecolor='white', square=False)
axes[0].set_title('vs. Psychiatrist', fontsize=14)
axes[0].set_ylabel('Story ID', fontsize=12)

sns.heatmap(df_scorecard_dom, ax=axes[1], annot=False, cmap='RdYlGn', cbar=False, 
            linewidths=0.5, linecolor='white', square=False)
axes[1].set_title('vs. Dominant (Crowd Consensus)', fontsize=14)
axes[1].set_ylabel('')

plt.suptitle('Visual Scorecard: Correct (Green) vs Incorrect (Red)', fontsize=16)
plt.tight_layout()
plt.savefig('scorecard_heatmap_comparison.png')
print("Generated Plot: scorecard_heatmap_comparison.png")
plt.close()

# 7. Accuracy by Emotion Category
# -------------------------------
def plot_emotion_accuracy(ground_truth_col, title_suffix, filename):
    emotions = sorted(df_clean[ground_truth_col].unique())
    emotion_acc_data = []

    for emotion in emotions:
        if emotion == 'Unknown': continue
        
        subset = df_clean[df_clean[ground_truth_col] == emotion]
        if len(subset) == 0: continue
        
        row = {'Emotion': emotion, 'Count': len(subset)}
        for model in model_cols.keys():
            correct_count = (subset[model] == subset[ground_truth_col]).sum()
            row[model] = correct_count / len(subset)
        emotion_acc_data.append(row)

    if not emotion_acc_data:
        print(f"No data for {title_suffix}")
        return

    df_emotion_acc = pd.DataFrame(emotion_acc_data).set_index('Emotion')
    
    # Plot
    colors = ['#87CEEB', '#90EE90', '#FA8072'] 
    ax = df_emotion_acc[list(model_cols.keys())].plot(kind='bar', figsize=(10, 6), 
                                                      color=colors, edgecolor='black', width=0.8)
    plt.title(f'Accuracy by Emotion Category ({title_suffix})', fontsize=16)
    plt.ylabel('Accuracy', fontsize=12)
    plt.xlabel('Emotion', fontsize=12)
    plt.ylim(0, 1.1)
    plt.legend(title='AI Model')
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    # Add counts to x-labels
    new_labels = [f"{e}\n(n={c})" for e, c in zip(df_emotion_acc.index, df_emotion_acc['Count'])]
    ax.set_xticklabels(new_labels, rotation=0)

    plt.tight_layout()
    plt.savefig(filename)
    print(f"Generated Plot: {filename}")
    plt.close()

# Generate for both
plot_emotion_accuracy('Psych', 'vs. Psychiatrist', 'emotion_accuracy_psych.png')
plot_emotion_accuracy('Dom', 'vs. Dominant', 'emotion_accuracy_dom.png')