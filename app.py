from dotenv import load_dotenv
load_dotenv()  # Load .env file (MAIL_USERNAME, MAIL_PASSWORD, etc.)

from app import create_app
from app.services.reminder_service import init_scheduler

# Create the Flask application instance
app = create_app()

with app.app_context():
    # Initialize reminder scheduler
    init_scheduler(app)

if __name__ == '__main__':
    # Run the development server
    print("Starting Student-Led Workshop System...")
    print("Access the application at: http://127.0.0.1:5000")
    print("Reminder system: Active (sends emails 24h and 1h before workshops)")
    app.run(debug=True, host='0.0.0.0', port=5000)
