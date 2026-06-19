import json
import sqlite3
import os

with open('spider_data/spider_data/dev.json', 'r') as f:
    spider_data = json.load(f)

sample = spider_data[0]
question = sample['question']
expected_sql = sample['query']
db_id = sample['db_id'] 

print(f"NL Question: {question}")
print(f"Target DB: {db_id}")
print(f"Expected SQL: {expected_sql}\n")

db_path = os.path.join('spider_data', 'spider_data', 'database', db_id, f"{db_id}.sqlite")

# Initialize conn as None so the 'finally' block doesn't crash
conn = None

try:
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(expected_sql)
    results = cursor.fetchall()
    
    print(f"Connection Successful!")
    print(f"The query executed and returned {len(results)} rows.")
    print(f"Sample data: {results[0] if results else 'No data'}")
    
except sqlite3.Error as e:
    print(f"Database error: {e}")
finally:
    if conn:
        conn.close()