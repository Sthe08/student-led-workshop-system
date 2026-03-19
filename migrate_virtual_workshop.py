"""
Add virtual workshop support to existing workshops table.

This migration adds columns for:
- workshop_type: 'physical' or 'virtual'
- meeting_link: URL for virtual meetings
- meeting_id: Meeting identifier from provider
- meeting_provider: 'google_meet' or 'teams'
"""

from app import create_app, db
from sqlalchemy import text

def migrate():
    """Run migration to add virtual workshop columns"""
    app = create_app('development')
    
    with app.app_context():
        # Check if columns already exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('workshops')]
        
        print("Current workshop table columns:", columns)
        print("=" * 50)
        
        # Add workshop_type column if it doesn't exist
        if 'workshop_type' not in columns:
            print("Adding workshop_type column...")
            with db.engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE workshops ADD COLUMN workshop_type VARCHAR(20) DEFAULT 'physical'"
                ))
                conn.commit()
            print("✓ workshop_type column added")
        else:
            print("✓ workshop_type column already exists")
        
        # Add meeting_link column if it doesn't exist
        if 'meeting_link' not in columns:
            print("Adding meeting_link column...")
            with db.engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE workshops ADD COLUMN meeting_link VARCHAR(500)"
                ))
                conn.commit()
            print("✓ meeting_link column added")
        else:
            print("✓ meeting_link column already exists")
        
        # Add meeting_id column if it doesn't exist
        if 'meeting_id' not in columns:
            print("Adding meeting_id column...")
            with db.engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE workshops ADD COLUMN meeting_id VARCHAR(100)"
                ))
                conn.commit()
            print("✓ meeting_id column added")
        else:
            print("✓ meeting_id column already exists")
        
        # Add meeting_provider column if it doesn't exist
        if 'meeting_provider' not in columns:
            print("Adding meeting_provider column...")
            with db.engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE workshops ADD COLUMN meeting_provider VARCHAR(20)"
                ))
                conn.commit()
            print("✓ meeting_provider column added")
        else:
            print("✓ meeting_provider column already exists")
        
        print("\n" + "=" * 50)
        print("✅ Migration completed successfully!")
        print("\nNote: Existing workshops will have NULL values for the new columns.")
        print("They will be treated as physical workshops by default.")
        print("\nNext steps:")
        print("1. Restart your Flask application")
        print("2. Test creating a virtual workshop")
        print("3. Verify meeting links are generated correctly")

if __name__ == '__main__':
    print("Starting virtual workshop migration...")
    print("=" * 50)
    migrate()
