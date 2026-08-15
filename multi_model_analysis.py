import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm


CSV_FILENAME = 'mass_evaluation_results.csv'
df = pd.read_csv(CSV_FILENAME)

df = df.dropna(subset=['Confidence', 'Is_Correct'])
df['Is_Correct'] = df['Is_Correct'].astype(bool)

models = df['Model_Name'].unique()
print(f"📊 Analyzing data for {len(models)} models...\n")

num_bins = 10
bins = np.linspace(0, 1.0, num_bins + 1)

# Plot
plt.figure(figsize=(12, 10))
plt.plot([0, 1], [0, 1], linestyle='--', color='gray', linewidth=2, label='Perfect Calibration')

colors = cm.tab20(np.linspace(0, 1, len(models)))

# Store results for the console leaderboard
results_summary = []

for idx, model in enumerate(models):
    model_df = df[df['Model_Name'] == model]
    n_total = len(model_df)
    
    if n_total == 0:
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

    # Calculate ECE
    ece = sum([(count / n_total) * abs(acc - conf) for count, acc, conf in zip(bin_counts, bin_accuracies, bin_confidences) if count > 0])
    
    overall_acc = model_df['Is_Correct'].mean()
    overall_conf = model_df['Confidence'].mean()
    
    results_summary.append({
        'Model': model,
        'Accuracy': overall_acc,
        'Confidence': overall_conf,
        'ECE': ece
    })

    # Filter out empty bins for drawing the line
    valid_accs = [acc for count, acc in zip(bin_counts, bin_accuracies) if count > 0]
    valid_confs = [conf for count, conf in zip(bin_counts, bin_confidences) if count > 0]

    # Plot this model's line
    plt.plot(valid_confs, valid_accs, marker='o', markersize=4, color=colors[idx], linewidth=1.5, alpha=0.8, label=f"{model} (ECE: {ece:.3f})")


plt.xlabel('Confidence Score (Predicted Probability)', fontsize=12)
plt.ylabel('Actual Accuracy (Execution Match)', fontsize=12)
plt.title('Multi-Model Reliability Diagram: Text-to-SQL Calibration', fontsize=14, pad=20)

# Put legend outside the plot so it doesn't cover the lines
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0., fontsize=9)
plt.grid(True, alpha=0.3)
plt.xlim([0, 1.05])
plt.ylim([0, 1.05])

plt.savefig('multi_model_reliability_diagram.png', dpi=300, bbox_inches='tight')
print("✅ Chart generated and saved as 'multi_model_reliability_diagram.png'\n")
plt.show()

print("-" * 65)
print(f"{'Model Name':<40} | {'Acc':<5} | {'Conf':<5} | {'ECE':<5}")
print("-" * 65)
# Sort by ECE
results_summary.sort(key=lambda x: x['ECE'])
for res in results_summary:
    print(f"{res['Model']:<40} | {res['Accuracy']:.3f} | {res['Confidence']:.3f} | {res['ECE']:.3f}")
print("-" * 65)