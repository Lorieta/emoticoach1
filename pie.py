import matplotlib.pyplot as plt

# 1. Data (Age Distribution from previous chart)
labels = ['18', '19', '20', '21', '22', '23', '24', '27', '29']
counts = [4, 8, 10, 47, 26, 5, 1, 1, 1]
total_responses = sum(counts)

# 2. Define colors similar to the example (Google Forms palette)
colors = ['#4285F4', '#DB4437', '#F4B400', '#0F9D58', '#AB47BC', 
          '#00ACC1', '#FF7043', '#9E9D24', '#5C6BC0']

# 3. Create the plot
fig, ax = plt.subplots(figsize=(10, 5))

wedges, texts, autotexts = ax.pie(
    counts, 
    autopct='%1.1f%%',       # Show percentages only
    startangle=180,          # Rotate start to match the visual feel
    colors=colors,
    textprops={'color':"w", 'weight':'bold', 'fontsize':10}, # White text inside
    pctdistance=0.7          # Distance of percentage text from center
)

# 4. Create Legend on the right side
ax.legend(wedges, labels, 
          title="", 
          loc="center left", 
          bbox_to_anchor=(1, 0, 0.5, 1), # Coordinates to place legend outside
          frameon=False)     # Remove box border around legend to match style

# 5. Title with "Responses" count, aligned left
plt.title(f"Age Distribution\n{total_responses} responses", loc='left', fontsize=16)

# Ensure chart is a circle
ax.axis('equal')  

plt.tight_layout()
plt.show()