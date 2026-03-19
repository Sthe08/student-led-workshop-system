"""
Script to add sample venues to the database.
Run this after recreating the database to populate initial venue data.
"""
from app import create_app, db
from app.models.venue import Venue

app = create_app()

with app.app_context():
    # Sample venues for DUT context
    venues_data = [
        {
            'name': 'Computer Lab 1',
            'building': 'Engineering Building',
            'room_number': 'Room 101',
            'capacity': 30,
            'facilities': 'Computers, Projector, WiFi, Whiteboard',
            'description': 'Modern computer lab with 30 workstations, ideal for programming workshops.',
            'status': 'active'
        },
        {
            'name': 'Conference Room A',
            'building': 'Library',
            'room_number': 'Ground Floor',
            'capacity': 50,
            'facilities': 'Projector, Sound System, WiFi, Video Conferencing',
            'description': 'Large conference room suitable for presentations and seminars.',
            'status': 'active'
        },
        {
            'name': 'Design Studio',
            'building': 'Arts Building',
            'room_number': 'Studio 2',
            'capacity': 25,
            'facilities': 'Drawing Tables, Computers, Design Software, Scanner',
            'description': 'Creative space equipped for design and multimedia workshops.',
            'status': 'active'
        },
        {
            'name': 'Business Lab',
            'building': 'Commerce Building',
            'room_number': 'Room 204',
            'capacity': 40,
            'facilities': 'Projector, Whiteboard, WiFi, Breakout Rooms',
            'description': 'Collaborative space for business and entrepreneurship workshops.',
            'status': 'active'
        },
        {
            'name': 'Innovation Hub',
            'building': 'Student Center',
            'room_number': 'Level 3',
            'capacity': 60,
            'facilities': 'Projector, Sound System, WiFi, Movable Seating, Recording Equipment',
            'description': 'Flexible multi-purpose space for large workshops and hackathons.',
            'status': 'active'
        },
        {
            'name': 'Media Lab',
            'building': 'Engineering Building',
            'room_number': 'Room 305',
            'capacity': 20,
            'facilities': 'Green Screen, Cameras, Editing Suites, Audio Booth',
            'description': 'Professional media production facility for content creation workshops.',
            'status': 'maintenance'
        }
    ]
    
    # Create venues
    print("Adding sample venues...")
    for venue_data in venues_data:
        venue = Venue(**venue_data)
        db.session.add(venue)
        print(f"  ✓ Added: {venue_data['name']}")
    
    db.session.commit()
    
    print("\n✅ Sample venues added successfully!")
    print(f"Total venues: {Venue.query.count()}")
    print(f"Active venues: {Venue.query.filter_by(status='active').count()}")
    print(f"Under maintenance: {Venue.query.filter_by(status='maintenance').count()}")
    print("\nYou can now:")
    print("1. Log in as admin")
    print("2. Navigate to Admin > Venue Management")
    print("3. View, edit, or add more venues")
    print("4. Create workshops and assign them to venues")
