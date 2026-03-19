import sqlite3
import sys

try:
    conn = sqlite3.connect('instance/workshop.db')
    c = conn.cursor()
    c.execute("ALTER TABLE workshops ADD COLUMN venue_status VARCHAR(20) DEFAULT 'approved'")
    conn.commit()
    print("Column venue_status added successfully.")
except Exception as e:
    print(f"Error: {e}")
finally:
    if conn:
        conn.close()
