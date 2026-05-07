"""Count ROI records in database."""
import sqlite3

conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM roi_records")
count = cursor.fetchone()[0]
print(f"Total ROI records: {count}")

if count > 0:
    cursor.execute("SELECT * FROM roi_records ORDER BY captured_at DESC LIMIT 5")
    records = cursor.fetchall()
    print(f"\nLast 5 records:")
    for record in records:
        print(f"  ID: {record[0][:8]}..., has_face: {record[11]}, confidence: {record[8]}")

conn.close()
