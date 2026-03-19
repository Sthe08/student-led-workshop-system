"""
Test script to verify workshop creation with venues is working.
Run this to check if the issue is fixed.
"""
from app import create_app, db
from app.models.user import User
from app.models.venue import Venue
from app.models.workshop import Workshop
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    print("=" * 60)
    print("TESTING WORKSHOP CREATION WITH VENUES")
    print("=" * 60)
    
    # Check if we have venues
    venues = Venue.query.filter_by(status='active').all()
    print(f"\n✓ Active venues found: {len(venues)}")
    
    if not venues:
        print("\n❌ ERROR: No active venues found!")
        print("Run: python add_sample_venues.py")
        exit()
    
    for venue in venues:
        print(f"  - {venue.name} (Capacity: {venue.capacity})")
    
    # Check if we have an approved host
    host = User.query.filter_by(role='host', approved_host=True).first()
    
    if not host:
        print("\n⚠️  No approved host found. Creating one for testing...")
        host = User(
            student_number='testhost001',
            email='testhost@workshop.system',
            full_name='Test Host',
            role='host',
            approved_host=True
        )
        host.set_password('password123')
        db.session.add(host)
        db.session.commit()
        print(f"✓ Created test host: {host.full_name}")
    
    print(f"\n✓ Using host: {host.full_name} (ID: {host.id})")
    
    # Create a test workshop
    print("\n" + "=" * 60)
    print("CREATING TEST WORKSHOP...")
    print("=" * 60)
    
    workshop_date = datetime.utcnow() + timedelta(days=7)
    selected_venue = venues[0]
    
    try:
        workshop = Workshop(
            title='Test Workshop - Flask Basics',
            description='This is a test workshop to verify the venue booking system is working correctly.',
            category='Web Development',
            date_time=workshop_date,
            duration_minutes=90,
            venue_id=selected_venue.id,
            venue=None,
            capacity=20,
            host_id=host.id
        )
        
        db.session.add(workshop)
        db.session.commit()
        
        print(f"\n✅ SUCCESS! Workshop created:")
        print(f"   Title: {workshop.title}")
        print(f"   Venue: {workshop.venue_name}")
        print(f"   Date: {workshop.date_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Capacity: {workshop.capacity}")
        print(f"   Host: {workshop.host.full_name}")
        
        # Verify venue relationship works
        print(f"\n✓ Venue relationship test:")
        print(f"   - venue_details: {workshop.venue_details}")
        print(f"   - venue_name property: {workshop.venue_name}")
        
        # Clean up - delete the test workshop
        db.session.delete(workshop)
        db.session.commit()
        print(f"\n✓ Test workshop deleted (cleanup complete)")
        
    except Exception as e:
        print(f"\n❌ ERROR creating workshop: {str(e)}")
        db.session.rollback()
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nIf you see ✅ SUCCESS above, the issue is FIXED!")
    print("Try creating a workshop again via the web interface.")
