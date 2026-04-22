# Smart Fitness Tracker

Flask app for tracking meals, workouts, and weight — with live coaching insights based on your actual data.

**Live demo:** https://smart-fitness-tracker-production-8d95.up.railway.app/

![Landing Page](./docs/demo.png)

## Features

- **Meal logging** — USDA food search with household serving picker, macro auto-fill, re-log from history
- **Workout logging** — type, duration, and calories burned with full history
- **Weight tracking** — trend analysis with weekly rate of change
- **Daily nutrition summary** — calories, protein, carbs, and fat vs. your TDEE target
- **Progress analytics** — calorie history chart, 7-day macro breakdown, weight trend
- **Insight engine** — data-driven coaching tips computed from logged data: protein gaps, stalled cuts, workout cadence, weekend calorie patterns
- **Personalised TDEE** — Mifflin-St Jeor BMR with activity multipliers and goal-based targets
- **Secure auth** — Flask-Login, CSRF protection, scrypt hashing

## Stack

- **Backend:** Flask, SQLAlchemy, Flask-Login, Flask-WTF
- **Database:** SQLite (local) · PostgreSQL (production via Railway)
- **Frontend:** Jinja2, Bootstrap 5, Chart.js
- **APIs:** USDA FoodData Central

## Setup

```bash
git clone https://github.com/merleezy/smart-fitness-tracker
cd smart-fitness-tracker
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # fill in values below
python run.py
```

| Variable | Description |
|---|---|
| `SECRET_KEY` | Random string — `python -c "import secrets; print(secrets.token_hex(32))"` |
| `USDA_API_KEY` | Free key from [FoodData Central](https://fdc.nal.usda.gov/api-guide.html) |
| `DATABASE_URL` | `sqlite:///app.db` for local dev |
| `SEED_KEY` | Any secret string — enables `/admin/seed-demo?key=<SEED_KEY>` |

Visit **http://127.0.0.1:5000**. Database is created on first run.
