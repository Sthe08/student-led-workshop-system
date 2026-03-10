
from app import create_app
from app.models.user import db, User

app = create_app()

with app.app_context():
    # Check if admin already exists
    admin = User.query.filter_by(student_number='ADMIN01').first()
    
    if admin:
        print("✅ Admin user found!")
        print(f"Current Role: {admin.role}")
        print(f"Current Email: {admin.email}")
        
        # Update to admin role
        admin.role = 'admin'
        admin.approved_host = True
        admin.set_password('admin123')
        
        db.session.commit()
        
        print("\n✅ Admin user updated successfully!")
        print(f"New Role: {admin.role}")
    else:
        # Create new admin user
        admin = User(
            student_number='ADMIN01',
            email='admin@workshop.com',
            full_name='System Administrator',
            role='admin',
            approved_host=True
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin user created successfully!")
    
    print("\n📋 Login Credentials:")
    print("   Student Number: ADMIN01")
    print("   Email: admin@workshop.com (or use ADMIN01)")
    print("   Password: admin123")
    print("\n🔄 Now try logging in at: http://127.0.0.1:5000/auth/login")