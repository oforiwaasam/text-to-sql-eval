# Evaluating Text-to-SQL Calibration and LLM Overconfidence Across Architectures

## Abstract
As Generative AI is increasingly deployed in enterprise environments, model reliability and calibration have become critical safety metrics. This project evaluates the confidence calibration of 5 different Open-Source LLMs, spanning various parameter scales (7B to 120B) and model families, on the complex **Spider** Text-to-SQL benchmark. 

## Methodology
1. **Dataset:** Evaluated 100 zero-shot natural language queries from the Spider dataset against complex SQLite schemas.
2. **Inference (Groq API):** Prompted 5 distinct models to output a JSON object containing the generated SQL and a self-assessed `confidence_score` between 0.0 to 1.0.
3. **Execution Match:** Bypassed simple string comparison by executing both the LLM-generated SQL and the Gold Standard SQL against the same SQLite database to verify identical row outputs.
4. **Calibration Math:** Calculated the **Expected Calibration Error (ECE)** for each model to measure the gap between model confidence and actual execution accuracy.

## Results
 
| Model | Accuracy | Avg. Confidence | ECE | Structured-Output Errors |
|---|---|---|---|---|
| qwen/qwen3.6-27b | 0.880 | 0.987 | 0.107 | 25 / 100 |
| llama-3.3-70b-versatile | 0.810 | 0.923 | 0.113 | 0 / 100 |
| openai/gpt-oss-20b | 0.810 | 0.981 | 0.171 | 0 / 100 |
| openai/gpt-oss-120b | 0.810 | 0.982 | 0.172 | 0 / 100 |
| llama-3.1-8b-instant | 0.750 | 0.985 | 0.235 | 0 / 100 |


*The Qwen model's accuracy/confidence/ECE were computed on the 75 questions it completed successfully (a smaller, likely easier-skewed sample than the other four models, which all completed all 100 questions). Rows where a model failed to return a valid JSON (rate limits, malformed output) are excluded from all metrics above and reported separately in the Errors column (see Limitations).

## Key findings
 
- **Universal overconfidence.** Every model in this study reported confidence far exceeding its actual accuracy, regardless of size or lab.
- **Scale's effect on calibration is inconsistent, not absent.** A sixfold parameter increase (GPT-OSS 20B → 120B) produced almost no change in ECE. A roughly ninefold increase in a different family (Llama 8B → 70B) roughly halved ECE. Calibration does not appear to be a simple function of parameter count; it depends on factors this study wasn't designed to isolate (training method, data, RLHF approach, etc.).
- **Calibration and reliability are separate axes.** Qwen3.6-27B had the best accuracy and calibration among its completed questions, but failed structured-output validation on 25% of prompts (far more than any other model). A model can be well-calibrated when it works and still be the least dependable choice overall.

### Multi-Model Calibration 
The chart below highlights the massive gap between the "Perfect Calibration" baseline (gray dashed line) and the models' actual performance, demonstrating universal overconfidence.

![Multi-Model Reliability Diagram](multi_model_reliability_diagram.png)

## Limitations
 
- **Sample size:** 100 questions per model is a reasonable starting point but a small n for precise ECE estimates. Treat point estimates, especially Qwen's (n=75), as directional rather than exact.
- **Single benchmark:** Findings are specific to Spider and zero-shot text-to-SQL. They may not generalize to other structured-generation tasks or to multi-turn settings.
- **Model selection:** Models were chosen based on availability on Groq's free tier at the time of testing. This is a convenience sample, not a representative one across the broader LLM landscape.
- **No confidence intervals reported yet on ECE:** a natural next step, likely via bootstrapping.

## Reproducing this study
 
```bash
git clone https://github.com/oforiwaasam/text-to-sql-eval.git
cd text-to-sql-eval
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
 
# Download Spider dataset into spider_data/ (see https://yale-lily.github.io/spider)
 
# Set your Groq API key
export GROQ_API_KEY="your-key-here"
 
python mass_model_eval.py       # runs all models, writes mass_evaluation_results.csv
python multi_model_analysis.py  # produces reliability diagram + model_leaderboard.csv
```

Note: model availability and deprecation status change over time on Groq — check [console.groq.com/docs/deprecations](https://console.groq.com/docs/deprecations) before rerunning, and update `MODELS_TO_TEST` in `mass_model_eval.py` accordingly.

## Next steps
* Test whether post-hoc calibration techniques (e.g., Temperature Scaling or Platt Scaling) close the gap, and whether they help model families like GPT-OSS where raw scale did not.
* Expand the evaluation pipeline to multi-turn, agentic settings where early-step confidence may compound into later steps.
- Add bootstrap confidence intervals around ECE estimates.

## Acknowledgements & Citations
This evaluation framework utilizes the **Spider (1.0)** dataset for complex, cross-domain Text-to-SQL benchmarking. 

> Yu, T., Zhang, R., Yang, K., Yasunaga, M., Wang, D., Li, Z., Ma, J., Li, I., Yao, Q., Roman, S., Zhang, Z., & Radev, D. (2018). *Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task*. EMNLP 2018.

```bibtex
@inproceedings{Yu&al.18c,
  title     = {Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task},
  author    = {Tao Yu and Rui Zhang and Kai Yang and Michihiro Yasunaga and Dongxu Wang and Zifan Li and James Ma and Irene Li and Qingning Yao and Shanelle Roman and Zilin Zhang and Dragomir Radev},
  booktitle = "Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing",
  address   = "Brussels, Belgium",
  publisher = "Association for Computational Linguistics",
  year      = 2018
}
