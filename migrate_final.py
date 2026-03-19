import sqlite3
import os

db_path = 'instance/workshop.db'

def migrate():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Check workshops table for venue_status
    try:
        c.execute("SELECT venue_status FROM workshops LIMIT 1")
    except sqlite3.OperationalError:
        print("Adding venue_status to workshops...")
        c.execute("ALTER TABLE workshops ADD COLUMN venue_status VARCHAR(20) DEFAULT 'approved'")
    
    # Check registrations table for QR fields
    try:
        c.execute("SELECT check_in_token FROM registrations LIMIT 1")
    except sqlite3.OperationalError:
        print("Adding QR fields to registrations...")
        # SQLite doesn't support multiple columns in one ALTER TABLE, so do them one by one
        c.execute("ALTER TABLE registrations ADD COLUMN check_in_token VARCHAR(36) UNIQUE")
        c.execute("ALTER TABLE registrations ADD COLUMN checked_in BOOLEAN DEFAULT 0")
        c.execute("ALTER TABLE registrations ADD COLUMN check_in_time DATETIME")
    
    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
