"""
Script to recreate the database with updated schema.
Run this when you add new columns to models.
"""
from app import create_app, db

app = create_app()

with app.app_context():
    # Drop all tables
    print("Dropping all tables...")
    db.drop_all()
    
    # Create all tables with new schema
    print("Creating new tables with updated schema...")
    db.create_all()
    
    print("✅ Database recreated successfully!")
    print("\nNote: All data has been cleared. You'll need to:")
    print("1. Create a new admin account")
    print("2. Create new workshops")
    print("3. Register for workshops to test features")
