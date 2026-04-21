# Smart Fitness Tracker

A full-stack fitness tracking application built with Flask and SQLite. Users can register, log in, track workouts, and receive personalized meal and workout recommendations based on biometric algorithms.

Live demo link: https://smart-fitness-tracker-production-8d95.up.railway.app/

![Smart Fitness Tracker Demo](docs/demo.gif)

## Features

- **Secure Authentication:** User registration & login implementing Flask-WTF protection and secure password hashing.
- **Dynamic Dashboards:** Personal hubs that surface logged workouts, nutritional stats, and algorithmic guidance.
- **Smart Nutrition:** Meal logging with macro tracking, USDA FoodData integration, and historical quick-add.
- **Algorithmic Recommendations:** Logic-driven meal & workout plans generated from user goals and progress history.
- **Progress Analytics:** Interactive visualization of weight trends and workout volume using Chart.js.
- **Infrastructure:** Modular Flask application structure with templating (Jinja2), form validation, and SQLite persistence (PostgreSQL-compatible).

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/merleezy/smart-fitness-tracker
cd smart-fitness-tracker
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

### 4. Configure Environment Variables

Create a `.env` file in the root directory and add your configuration. You can use `.env.example` as a template:

```bash
cp .env.example .env
```

Make sure to update the `SECRET_KEY` and `USDA_API_KEY` in the `.env` file. (`SECRET_KEY` can be anything)

### 5. Initialize the database

```bash
python init_db.py
python seed.py  # Optional
```

### 6. Run the app

```bash
python run.py
```

Visit: http://127.0.0.1:5000

---
