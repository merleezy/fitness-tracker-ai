# Fitness Tracker with Personalized Meal & Workout AI

A full-stack fitness tracking application built with Flask and SQLite. Users can register, log in, track workouts, and receive personalized AI-based meal and workout recommendations. 


## Features

- User registration & login (Flask-WTF + hashed passwords)
- Personal dashboards that surface logged workouts, meals, and the latest AI guidance
- Meal logging with macro tracking, USDA food lookup/autocomplete, and one-click reuse of previous meals
- AI-generated meal & workout recommendations with history and follow/skip feedback tracking
- Workout logging with recent history and progress charts alongside weight trend analysis
- SQLite for local development (PostgreSQL-compatible)
- Modular Flask structure with templating, form validation, and routing
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
