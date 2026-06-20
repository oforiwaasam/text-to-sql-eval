import json
import sqlite3
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
my_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=my_key)

def get_database_schema(db_path):
    """Extracts the CREATE TABLE statements."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    schema_rows = cursor.fetchall()
    conn.close()
    return "\n".join([row[0] for row in schema_rows if row[0]])

def execute_sql(db_path, query):
    """Executes a query and returns the results. Returns None if the SQL is invalid."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        # If the LLM hallucinates bad SQL, it will trigger this exception
        return None

with open('spider_data/spider_data/dev.json', 'r') as f:
    spider_data = json.load(f)

sample = spider_data[0] # Still using the first question to test our logic
question = sample['question']
expected_sql = sample['query']
db_id = sample['db_id'] 

db_path = os.path.join('spider_data', 'spider_data', 'database', db_id, f"{db_id}.sqlite")
absolute_path = os.path.abspath(db_path)
schema = get_database_schema(absolute_path)

print(f"Question: {question}")
print("Evaluating...\n")

system_prompt = f"""
You are an expert database administrator. Your task is to translate natural language questions into executable SQL queries based on the provided database schema.
Database Schema:
{schema}
You must respond ONLY with a JSON object containing exactly two keys:
1. "generated_sql": The executable SQL query string.
2. "confidence_score": A float between 0.0 and 1.0.
"""

response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    response_format={ "type": "json_object" }, 
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ],
    temperature=0.0 
)

llm_output = json.loads(response.choices[0].message.content)
generated_sql = llm_output.get("generated_sql", "")
confidence = llm_output.get("confidence_score", 0.0)

# Run both queries against the local database
expected_results = execute_sql(absolute_path, expected_sql)
generated_results = execute_sql(absolute_path, generated_sql)

# Compare the results (converting to sets so row order doesn't matter)
is_correct = False
if generated_results is not None and expected_results is not None:
    is_correct = set(expected_results) == set(generated_results)

print("-" * 30)
print(f"Expected SQL:  {expected_sql}")
print(f"Generated SQL: {generated_sql}")
print("-" * 30)
print(f"Confidence Score: {confidence}")
print(f"Execution Match:  {'✅ PASS' if is_correct else '❌ FAIL'}")