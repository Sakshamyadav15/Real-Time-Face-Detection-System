"""Check database tables."""
import sqlite3

conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Tables in database: {tables}")

if tables:
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print(f"\nColumns in {table[0]}:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

conn.close()
