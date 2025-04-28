# Fitness Tracker with Personalized Meal & Workout AI

A full-stack fitness tracking application built with Flask and SQLite. Users can register, log in, track workouts, and receive personalized AI-based meal and workout recommendations. 


## Features

- User registration & login (Flask-WTF + hashed passwords)
- Personal user dashboards with real-time workout tracking
- Forms to log workouts (meal logging and AI recommendation engine planned)
- SQLite for local development (PostgreSQL-compatible)
- Modular Flask structure with templating, form validation, and routing
- Designed for future integration with wearable APIs (Fitbit, Apple HealthKit)
- Virtual environment + requirements management

##  Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/merleezy/fitness-tracker-ai
cd fitness-tracker-ai
```

### 2. Set up a virtual environment
```bash
python -m venv venv
venv\Scripts\activate           # Windows
# OR
source venv/bin/activate        # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize the database
```bash
python init_db.py
python seed.py  # Optional
```

### 5. Run the app
```bash
python run.py
```

Visit: http://127.0.0.1:5000

---
