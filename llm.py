import json
import sqlite3
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_database_schema(db_path):
    """Extracts the table structures from the SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Query SQLite's internal master table to get the CREATE TABLE statements
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    schema_rows = cursor.fetchall()
    conn.close()
    
    # Combine all CREATE TABLE statements into one string
    return "\n".join([row[0] for row in schema_rows if row[0]])

with open('spider_data/spider_data/dev.json', 'r') as f:
    spider_data = json.load(f)

sample = spider_data[0]
question = sample['question']
db_id = sample['db_id'] 

db_path = os.path.join('spider_data', 'spider_data', 'database', db_id, f"{db_id}.sqlite")
absolute_path = os.path.abspath(db_path)
schema = get_database_schema(absolute_path)

print(f"Sending Question: {question}")
print("Generating SQL via LLM...\n")

system_prompt = f"""
You are an expert database administrator. Your task is to translate natural language questions into executable SQL queries based on the provided database schema.

Database Schema:
{schema}

You must respond ONLY with a JSON object containing exactly two keys:
1. "generated_sql": The executable SQL query string.
2. "confidence_score": A float between 0.0 and 1.0 indicating how confident you are that this query perfectly answers the user's question without causing an execution error.
"""

response = client.chat.completions.create(
    model="llama-3.1-8b-instant", # Free and very fast!
    response_format={ "type": "json_object" }, 
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ],
    temperature=0.0 
)

llm_output = json.loads(response.choices[0].message.content)

print("--- LLM OUTPUT ---")
print(json.dumps(llm_output, indent=4))