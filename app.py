from app import create_app

# Create the Flask application instance
app = create_app()

if __name__ == '__main__':
    # Run the development server
    print("Starting Student-Led Workshop System...")
    print("Access the application at: http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
