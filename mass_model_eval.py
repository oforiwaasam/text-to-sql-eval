import json
import sqlite3
import os
import csv
import time
from dotenv import load_dotenv
from groq import Groq
from groq import RateLimitError


load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Number of questions to evaluate
NUM_SAMPLES = 100
CSV_FILENAME = "mass_evaluation_results.csv"
SLEEP_SECONDS = 2.5
MAX_RETRIES = 3
MODELS_TO_TEST = [
    "llama-3.1-8b-instant",       
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
]


def get_database_schema(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    schema_rows = cursor.fetchall()
    conn.close()
    return "\n".join([row[0] for row in schema_rows if row[0]])

def execute_sql(db_path, query):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception:
        return None


def call_model_with_retry(model_name, system_prompt, question):
    """Retries on rate-limit errors specifically, so 429s don't get logged
    as model failures. Raises the last exception if all retries are exhausted."""
    for attempt in range(MAX_RETRIES):
        try:
            return client.chat.completions.create(
                model=model_name,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.0
            )
        except RateLimitError:
            wait = SLEEP_SECONDS * (2 ** (attempt + 1))  # backoff: 5s, 10s, 20s
            print(f"   ⏳ Rate limited, waiting {wait}s (attempt {attempt+1}/{MAX_RETRIES})...")
            time.sleep(wait)

    # Final attempt — let it raise if it fails again, caller will log as a real error
    return client.chat.completions.create(
        model=model_name,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0.0
    )


with open('spider_data/dev.json', 'r') as f:
    spider_data = json.load(f)

# Slice the list to only take the first NUM_SAMPLES
test_samples = spider_data[:NUM_SAMPLES]

# Open the CSV file in 'write' mode and add the header row
with open(CSV_FILENAME, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Model_Name", "Question_ID", "Database", "Question", "Expected_SQL", "Generated_SQL", "Confidence", "Is_Correct", "Error_Note"])

    print(f"🚀 Starting Mass Model Evaluation for {NUM_SAMPLES} questions...\n")

    for model_name in MODELS_TO_TEST:
        print(f"Starting experiment run for model: {model_name}")
        for i, sample in enumerate(test_samples):
            question = sample['question']
            expected_sql = sample['query']
            db_id = sample['db_id'] 
        
            db_path = os.path.join('spider_data', 'database', db_id, f"{db_id}.sqlite")
            absolute_path = os.path.abspath(db_path)
        
            print(f"[{i+1}/{NUM_SAMPLES}] Model: {model_name} | DB: {db_id}...")

            try:
                schema = get_database_schema(absolute_path)
                
                system_prompt = f"""
                You are an expert database administrator. Translate natural language questions into executable SQL queries.
                Database Schema:
                {schema}
                You must respond ONLY with a JSON object containing exactly two keys:
                1. "generated_sql": The executable SQL query string.
                2. "confidence_score": A float between 0.0 and 1.0.
                """

                response = call_model_with_retry(model_name, system_prompt, question)

                # Parse Output
                llm_output = json.loads(response.choices[0].message.content)
                generated_sql = llm_output.get("generated_sql", "")
                confidence = llm_output.get("confidence_score", 0.0)

                # Evaluate
                expected_results = execute_sql(absolute_path, expected_sql)
                generated_results = execute_sql(absolute_path, generated_sql)

                is_correct = False
                error_note = "None"
                
                if generated_results is None:
                    error_note = "Execution Error (Bad SQL)"
                elif expected_results is not None:
                    is_correct = set(expected_results) == set(generated_results)

                # Write to CSV
                writer.writerow([model_name, i+1, db_id, question, expected_sql, generated_sql, confidence, is_correct, error_note])

            except RateLimitError as e:
                # Distinguished from other failures so it doesn't silently count against the model's accuracy in this analysis.
                print(f"⚠️ Rate limit exhausted retries on model {model_name}, question {i+1}: {e}")
                writer.writerow([model_name, i+1, db_id, question, expected_sql, "ERROR", 0.0, False, f"Rate Limit Error: {e}"])

            except Exception as e:
                # If API fails, model is unavailable, or JSON is mangled, log the error but KEEP GOING
                print(f"⚠️ Error on model {model_name}, question {i+1}: {e}")
                writer.writerow([model_name, i+1, db_id, question, expected_sql, "ERROR", 0.0, False, str(e)])

            # Flush after every row so a mid-run crash doesn't lose progress.
            file.flush()

            # Rate Limiting: Pause for {SLEEP_SECONDS} seconds so Groq doesn't block us
            time.sleep(SLEEP_SECONDS)

print(f"\n✅ Mass model evaluation complete! Check your folder for '{CSV_FILENAME}'.")