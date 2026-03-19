# Student-Led Workshop System

A comprehensive workshop management platform developed with Flask, designed to facilitate student-led learning and professional development.

## 🚀 Quick Start (Windows)

To get the application running locally on your Windows machine, follow these steps:

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Flaskvprojecta
```

### 2. Set Up Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the `.env.example` file to `.env` and fill in your details:
```powershell
copy .env.example .env
```
> [!IMPORTANT]
> Make sure to set a secure `SECRET_KEY` and provide valid mail server credentials for notifications to work.

### 5. Initialize the Database
Run the following scripts to set up your database, admin account, and initial data:
```powershell
# Create the initial database and admin user (ADMIN01 / admin123)
python create_admin.py

# Add sample venues to the system
python add_sample_venues.py
```

### 6. Run the Application
```powershell
python app.py
```
The application will be accessible at: **http://127.0.0.1:5000**

---

## 📋 Features

- **User Roles**: Students, Hosts, and Administrators with custom dashboards.
- **Workshop Management**: Create, edit, and manage physical or virtual workshops.
- **Venue Booking**: Check availability and book physical venues across the campus.
- **Virtual Integration**: Automated links for Google Meet and Microsoft Teams.
- **Attendance System**: QR code-based check-in and attendance tracking.
- **Notification Engine**: Automated email reminders (24h and 1h before events).
- **Admin Dashboard**: Comprehensive management of users, hosts, and venues.

---

## 📁 Project Structure

```
Flaskvprojecta/
├── app/                  # Main application package
│   ├── models/           # Database models
│   ├── routes/           # Blueprints and route handlers
│   ├── services/         # Business logic (reminders, integration)
│   ├── static/           # CSS, JS, and Images
│   └── templates/        # Jinja2 HTML templates
├── docs/                 # Detailed documentation and phase guides
├── instance/             # Local database (git-ignored)
├── tests/                # Automated test suite
├── config.py             # Application configuration
└── app.py                # Main entry point
```

---

## 🛠️ Technologies

- **Frontend**: Bootstrap 5, Jinja2, Vanilla CSS
- **Backend**: Flask 3.0, Flask-SQLAlchemy, Flask-Login, Flask-Mail
- **Security**: Bcrypt hashing, CSRF protection, Role-based Access (RBAC)
- **Integration**: Google Calendar API, MS Graph API (for virtual meetings)

---

## 📞 Support & Documentation

Detailed guides and implementation notes can be found in the [docs/](file:///c:/Users/Promi/Desktop/2026_Projects/Flaskvprojecta/docs/) folder.

*Student Workshop System © 2026*
