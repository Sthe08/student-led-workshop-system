# Setup script for Student-Led Workshop System

Write-Host "🚀 Starting Student-Led Workshop System Setup..." -ForegroundColor Cyan

# 1. Create Virtual Environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
} else {
    Write-Host "✅ Virtual environment already exists." -ForegroundColor Green
}

# 2. Activate venv and install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
& ".\.venv\Scripts\pip.exe" install -r requirements.txt

# 3. Create .env from .env.example if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "⚙️ Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "⚠️  Please update your .env file with actual secrets!" -ForegroundColor Red
} else {
    Write-Host "✅ .env file already exists." -ForegroundColor Green
}

# 4. Initialize Database and Admin
Write-Host "🗄️  Initializing database and admin account..." -ForegroundColor Yellow
& ".\.venv\Scripts\python.exe" create_admin.py
& ".\.venv\Scripts\python.exe" add_sample_venues.py

Write-Host "`n✨ Setup Complete!" -ForegroundColor Cyan
Write-Host "You can now run the app using: .\.venv\Scripts\python.exe app.py" -ForegroundColor Green
