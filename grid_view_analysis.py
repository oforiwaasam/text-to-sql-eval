import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

CSV_FILENAME = 'mass_evaluation_results.csv'
df = pd.read_csv(CSV_FILENAME)

df = df.dropna(subset=['Confidence', 'Is_Correct'])
df['Is_Correct'] = df['Is_Correct'].astype(bool)

models = df['Model_Name'].unique()
num_models = len(models)
print(f"Generating grid view for {num_models} models...\n")

# For 13 models, a 4-column layout works best
cols = 4
rows = math.ceil(num_models / cols)

fig, axes = plt.subplots(rows, cols, figsize=(16, rows * 4))
axes = axes.flatten()

num_bins = 10
bins = np.linspace(0, 1.0, num_bins + 1)

for idx, model in enumerate(models):
    ax = axes[idx]
    model_df = df[df['Model_Name'] == model]
    n_total = len(model_df)
    
    if n_total == 0:
        ax.set_visible(False)
        continue
        
    bin_accuracies = []
    bin_confidences = []
    bin_counts = []

    for i in range(num_bins):
        lower_bound = bins[i]
        upper_bound = bins[i+1]
        
        if i == 0:
            in_bin = model_df[(model_df['Confidence'] >= lower_bound) & (model_df['Confidence'] <= upper_bound)]
        else:
            in_bin = model_df[(model_df['Confidence'] > lower_bound) & (model_df['Confidence'] <= upper_bound)]
            
        count = len(in_bin)
        bin_counts.append(count)
        
        if count > 0:
            bin_accuracies.append(in_bin['Is_Correct'].mean())
            bin_confidences.append(in_bin['Confidence'].mean())
        else:
            bin_accuracies.append(0.0)
            bin_confidences.append(0.0)

    # Calculate the ECE
    ece = sum([(count / n_total) * abs(acc - conf) for count, acc, conf in zip(bin_counts, bin_accuracies, bin_confidences) if count > 0])
    
    # Plots 
    ax.plot([0, 1], [0, 1], linestyle='--', color='gray', zorder=1)
    
    valid_accs = [acc for count, acc in zip(bin_counts, bin_accuracies) if count > 0]
    valid_confs = [conf for count, conf in zip(bin_counts, bin_confidences) if count > 0]
    ax.plot(valid_confs, valid_accs, marker='o', color='blue', linewidth=2, zorder=3)
    
    weights = [c / n_total for c in bin_counts]
    ax.bar(bins[:-1] + 0.05, weights, width=0.1, align='center', alpha=0.3, color='orange', zorder=2)
    
    ax.set_title(f"{model}\nECE: {ece:.3f}", fontsize=11, fontweight='bold')
    ax.set_xlim([0, 1.05])
    ax.set_ylim([0, 1.05])
    ax.grid(True, alpha=0.3)
    
    if idx % cols == 0:
        ax.set_ylabel('Actual Accuracy')
    if idx >= (rows - 1) * cols:
        ax.set_xlabel('Confidence Score')

for idx in range(num_models, len(axes)):
    axes[idx].set_visible(False)

# Title
plt.suptitle("Reliability Diagrams: Confidence Distribution & Accuracy by Model", fontsize=18, y=1.02)
plt.tight_layout()


plt.savefig('reliability_grid_view.png', dpi=300, bbox_inches='tight')
print("Grid view generated and saved as 'reliability_grid_view.png'")
plt.show()