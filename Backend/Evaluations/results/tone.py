import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

# 1. Load the Data
# Replace these filenames with your actual file paths if running locally
file_path = os.path.join(os.path.dirname(__file__), 'tone mapping f1.xlsx')
samples_df = pd.read_excel(file_path, sheet_name='samples')
per_polarity_df = pd.read_excel(file_path, sheet_name='per_polarity')
summary_df = pd.read_excel(file_path, sheet_name='summary')

# Set visual style
sns.set_theme(style="whitegrid")

# ==========================================
# PART A: Generate the 2 Data Tables
# ==========================================

# 1. Tone Confusion Matrix (Table Data)
tone_cm_data = pd.crosstab(samples_df['expected_tone'], samples_df['predicted_tone'])
print("--- Tone Confusion Matrix Data ---")
print(tone_cm_data)
print("\n")

# 2. Emotion Transition Matrix (Table Data)
emotion_cm_data = pd.crosstab(samples_df['original_emotion'], samples_df['response_emotion'])
print("--- Emotion Transition Matrix Data ---")
print(emotion_cm_data)
print("\n")

# ==========================================
# PART B: Generate the 6 Plots
# ==========================================

# --- Plot 1: Tone Confusion Matrix Heatmap ---
plt.figure(figsize=(8, 6))
sns.heatmap(tone_cm_data, annot=True, fmt='d', cmap='Blues', square=True)
plt.title('Confusion Matrix: Expected vs Predicted Tone')
plt.ylabel('Expected Tone')
plt.xlabel('Predicted Tone')
plt.tight_layout()
plt.show() # or plt.savefig('tone_confusion_matrix.png')

# --- Plot 2: Emotion Transition Heatmap ---
plt.figure(figsize=(8, 6))
sns.heatmap(emotion_cm_data, annot=True, fmt='d', cmap='Greens', square=True)
plt.title('Emotion Transition: Original vs Response')
plt.ylabel('Original Emotion')
plt.xlabel('Response Emotion')
plt.tight_layout()
plt.show()

# --- Plot 3: Summary Metrics (Rates) ---
plt.figure(figsize=(8, 5))
rates_df = summary_df[summary_df['metric'].isin(['Tone Switch Accuracy', 'Macro F1 (Polarity)'])]
sns.barplot(data=rates_df, y='metric', x='value', palette='viridis')
plt.title('Performance Metrics (Rates)')
plt.xlim(0, 1)
# Add labels
for index, value in enumerate(rates_df['value']):
    plt.text(value + 0.01, index, f'{value:.2f}', va='center')
plt.tight_layout()
plt.show()

# --- Plot 4: Summary Metrics (Counts) ---
plt.figure(figsize=(8, 5))
counts_df = summary_df[summary_df['metric'].isin(['Samples Evaluated', 'Appropriate Switches', 'Inappropriate Switches'])]
sns.barplot(data=counts_df, y='metric', x='value', palette='magma')
plt.title('Performance Metrics (Counts)')
# Add labels
for index, value in enumerate(counts_df['value']):
    plt.text(value + 0.1, index, f'{int(value)}', va='center')
plt.tight_layout()
plt.show()

# --- Plot 5: Polarity Performance ---
plt.figure(figsize=(10, 6))
# Melt data for easier plotting with seaborn
polarity_melted = per_polarity_df.melt(id_vars=['polarity', 'support'], 
                                       value_vars=['precision', 'recall', 'f1'], 
                                       var_name='metric', value_name='score')
sns.barplot(data=polarity_melted, x='polarity', y='score', hue='metric', palette='Set2')
plt.title('Performance by Polarity')
plt.ylim(0, 1.1)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()

# --- Plot 6: Appropriate Switch Distribution ---
plt.figure(figsize=(6, 6))
switch_counts = samples_df['appropriate_switch'].value_counts()
plt.pie(switch_counts, labels=switch_counts.index, autopct='%1.1f%%', 
        colors=sns.color_palette('pastel'), startangle=90)
plt.title('Distribution of Appropriate Switches')
plt.tight_layout()
plt.show()

# --- Plot 7: Emotion to Predicted Tone Heatmap ---
emotion_tone_data = pd.crosstab(samples_df['original_emotion'], samples_df['predicted_tone'])
print("--- Emotion to Predicted Tone Data ---")
print(emotion_tone_data)
print("\n")

plt.figure(figsize=(10, 8))
sns.heatmap(emotion_tone_data, annot=True, fmt='d', cmap='Purples', square=True)
plt.title('Mapping: Original Emotion to Predicted Tone')
plt.ylabel('Original Emotion')
plt.xlabel('Predicted Tone')
plt.tight_layout()
plt.savefig('emotion_to_predicted_tone.png')
print("Generated Plot: emotion_to_predicted_tone.png")
plt.show()