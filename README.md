# Student-Led Workshop System - Phase 1 & 2

## 🎉 Success! Your Flask Application is Running

The application is now accessible at: **http://127.0.0.1:5000**

Click the preview button above to view your application in the browser.

---

## 📋 What's Been Implemented

### ✅ Phase 1: Foundation & Setup
- **Environment Setup**: Python virtual environment configured
- **Project Structure**: Modular Flask architecture with separate folders for models, routes, templates, and static files
- **Database**: SQLite database with SQLAlchemy ORM
- **User Model**: Complete user model with roles (Student, Host, Admin)
- **Configuration**: Development and production configuration settings

### ✅ Phase 2: Authentication & User Management
- **User Registration**: Complete registration system with validation
  - Student number and email validation
  - Password hashing with bcrypt
  - Role selection (Student or Host)
  - Host approval workflow
- **Login System**: Secure authentication
  - Session-based login with Flask-Login
  - Remember me functionality
  - Last login tracking
- **User Profile**: Profile management
  - View and edit profile information
  - Bio and full name updates
- **Role-Based Access**: Different permissions for each role
- **Admin Panel**: Host approval dashboard for admins

---

## 🚀 How to Use the Application

### 1. Register a New Account
- Click "Register" in the navigation
- Fill in your student number, email, and password
- Choose your role:
  - **Student**: Immediate access to all student features
  - **Host**: Requires admin approval before creating workshops

### 2. Login
- Click "Login" in the navigation
- Enter your student number or email
- Enter your password
- Optionally check "Remember Me"

### 3. Update Your Profile
- After logging in, click "Profile" in the navigation
- Add your full name and bio
- Click "Update Profile"

### 4. Admin Features (Admin Accounts Only)
- Admin users can access the "Admin" menu
- View and approve/reject host requests
- Manage user permissions

---

## 📁 Project Structure

```
Flaskvprojecta/
├── app/
│   ├── __init__.py              # App factory
│   ├── forms.py                 # WTForms classes
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py              # User database model
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication routes
│   │   └── main.py              # Main routes
│   ├── static/
│   │   └── css/
│   │       └── style.css        # Custom styles
│   └── templates/
│       ├── admin/
│       │   └── approve_hosts.html
│       ├── about.html
│       ├── base.html            # Base template
│       ├── index.html           # Home page
│       ├── login.html
│       ├── profile.html
│       └── register.html
├── config.py                    # Configuration settings
├── requirements.txt             # Python dependencies
└── app.py                       # Main application entry point
```

---

## 🔐 Default Test Accounts

You can create test accounts manually by registering:

**Test Student:**
- Student Number: `STU001`
- Email: `student@test.com`
- Password: `password123`
- Role: Student

**Test Host (Pending Approval):**
- Student Number: `HOST001`
- Email: `host@test.com`
- Password: `password123`
- Role: Host

**Test Admin:**
- Student Number: `ADMIN01`
- Email: `admin@test.com`
- Password: `password123`
- Role: Admin

*Note: You'll need to manually update the database to set a user as admin:*
```python
# In Python shell after importing the app
from app.models.user import User
user= User.query.filter_by(student_number='ADMIN01').first()
user.role = 'admin'
db.session.commit()
```

---

## 🛠️ Technical Details

### Technologies Used
- **Backend**: Flask 3.0.0
- **Database**: SQLAlchemy with SQLite
- **Authentication**: Flask-Login with bcrypt password hashing
- **Forms**: Flask-WTF with WTForms
- **Frontend**: Bootstrap 5.3.2
- **Security**: CSRF protection, password hashing, session management

### Key Features
- ✅ Secure password hashing using bcrypt
- ✅ CSRF protection on all forms
- ✅ Input validation (client and server-side)
- ✅ Role-based access control
- ✅ Session management with "remember me"
- ✅ Flash messages for user feedback
- ✅ Responsive design with Bootstrap
- ✅ POPIA compliance ready (data protection)

---

## 📝 Next Steps (Future Phases)

### Phase 3: Workshop Management
- Create workshop CRUD operations
- Workshop listing and search
- Workshop categories and tags

### Phase 4: Registration & Attendance
- Student workshop registration
- Attendance tracking
- Waitlist management

### Phase 5: Notification System
- Email notifications
- Automated reminders
- SMS integration

### Phase 6: Feedback & Analytics
- Workshop feedback forms
- Rating system
- Analytics dashboard

---

## 🐛 Troubleshooting

### Application Won't Start?
1. Make sure virtual environment is activated:
   ```powershell
   .\Scripts\Activate.ps1
   ```

2. Reinstall dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Check if port 5000 is available

### Database Issues?
Delete the database file and restart:
```powershell
Remove-Item instance/workshop.db
python app.py
```

### Can't Login?
- Ensure you registered successfully
- Check student number/email spelling
- Verify password (minimum 6 characters)

---

## 📞 Support

For questions or issues, refer to:
- Flask documentation: https://flask.palletsprojects.com/
- Project proposal document
- Development plan document

---

**Built with ❤️ using Flask and Bootstrap**

*Student Workshop System © 2026*
