import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv('evaluation_results.csv')

# Clean data
df = df.dropna(subset=['Confidence', 'Is_Correct'])
df['Is_Correct'] = df['Is_Correct'].astype(bool)

n_total = len(df)
print(f"📊 Analyzing {n_total} evaluated queries...\n")

num_bins = 10
bins = np.linspace(0, 1.0, num_bins + 1)

bin_accuracies = []
bin_confidences = []
bin_counts = []

for i in range(num_bins):
    lower_bound = bins[i]
    upper_bound = bins[i+1]
    
    # Group the predictions that fall into this specific confidence bucket
    if i == 0:
        in_bin = df[(df['Confidence'] >= lower_bound) & (df['Confidence'] <= upper_bound)]
    else:
        in_bin = df[(df['Confidence'] > lower_bound) & (df['Confidence'] <= upper_bound)]
        
    count = len(in_bin)
    bin_counts.append(count)
    
    # Calculate the actual accuracy vs the average confidence in this bucket
    if count > 0:
        accuracy = in_bin['Is_Correct'].mean()
        avg_confidence = in_bin['Confidence'].mean()
    else:
        accuracy = 0.0
        avg_confidence = 0.0
        
    bin_accuracies.append(accuracy)
    bin_confidences.append(avg_confidence)

# ECE = Sum of (Weight of Bin * |Accuracy - Confidence|)
ece = sum([(count / n_total) * abs(acc - conf) for count, acc, conf in zip(bin_counts, bin_accuracies, bin_confidences) if count > 0])

overall_acc = df['Is_Correct'].mean()
overall_conf = df['Confidence'].mean()

print(f"📈 Overall Accuracy:   {overall_acc:.4f} ({overall_acc*100:.1f}%)")
print(f"🧠 Average Confidence: {overall_conf:.4f} ({overall_conf*100:.1f}%)")
print(f"⚖️ Expected Calibration Error (ECE): {ece:.4f}\n")

if overall_conf > overall_acc:
    print("Conclusion: The model is OVERCONFIDENT.")
else:
    print("Conclusion: The model is UNDERCONFIDENT.")

plt.figure(figsize=(8, 8))

# Plot the "Perfect Calibration" baseline (A diagonal line)
plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Perfect Calibration')

# Filter out empty bins for a clean line plot
valid_accs = [acc for count, acc in zip(bin_counts, bin_accuracies) if count > 0]
valid_confs = [conf for count, conf in zip(bin_counts, bin_confidences) if count > 0]

# Plot our model's actual calibration curve
plt.plot(valid_confs, valid_accs, marker='o', color='blue', linewidth=2, label='Llama-3.1-8B (Zero-Shot)')

# Add a subtle bar chart showing the distribution of the model's confidence scores
weights = [c / n_total for c in bin_counts]
plt.bar(bins[:-1] + 0.05, weights, width=0.1, align='center', alpha=0.3, color='orange', label='% of Samples in Bin')

plt.xlabel('Confidence Score (Predicted Probability)')
plt.ylabel('Actual Accuracy (Execution Match)')
plt.title(f'Reliability Diagram: Text-to-SQL Calibration\nECE: {ece:.4f}')
plt.legend(loc='upper left')
plt.grid(True, alpha=0.3)
plt.xlim([0, 1.05])
plt.ylim([0, 1.05])

# Save and show
plt.savefig('reliability_diagram.png', dpi=300, bbox_inches='tight')
print("\n✅ Chart generated and saved as 'reliability_diagram.png'")
plt.show()