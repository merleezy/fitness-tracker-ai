# 🏋️‍♂️ Fitness Tracker with Personalized Meal & Workout AI

A full-stack fitness tracking application built with Flask and SQLite. Users can register, log in, track workouts, and receive personalized AI-based meal and workout recommendations. Designed for extensibility, clean code, and real-world deployment.

---

## 📦 Features

- User registration & login (Flask-WTF + hashed passwords)
- Personal user dashboards with real-time workout tracking
- Forms to log workouts (meal logging and AI recommendation engine planned)
- SQLite for local development (PostgreSQL-compatible)
- Modular Flask structure with templating, form validation, and routing
- Designed for future integration with wearable APIs (Fitbit, Apple HealthKit)
- Virtual environment + requirements management

---

## 📁 Project Structure

```
fitness_tracker/
│
├── app/                     # Main application package
│   ├── __init__.py          # App & DB setup
│   ├── routes.py            # Flask routes
│   ├── models.py            # SQLAlchemy models
│   ├── forms.py             # WTForms classes
│   └── templates/           # Jinja2 HTML templates
│       ├── home.html
│       ├── register.html
│       ├── login.html
│       ├── user_dashboard.html
│       └── log_workout.html
│
├── static/                  # (Optional) CSS or JS
├── venv/                    # Virtual environment (not committed)
├── config.py                # App config (DB URI, secret key)
├── run.py                   # Main entry point
├── init_db.py               # Creates SQLite DB from models
├── seed.py                  # Optional: Seed sample data
├── requirements.txt         # Python dependencies
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/fitness-tracker.git
cd fitness-tracker
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

## ✅ Roadmap

- [x] User dashboard
- [x] Workout logging
- [ ] Meal logging
- [ ] User authentication (register/login/logout)
- [ ] AI recommendation engine
- [ ] Wearable device integration

---

## 🛠 Technologies

- Python 3.12
- Flask
- SQLAlchemy
- SQLite (dev) / PostgreSQL (prod-ready)
- WTForms / Flask-WTF
- Jinja2 templates

---

## 🤝 Contributing

Pull requests are welcome! Please:
1. Fork the repo and create a feature branch
2. Follow PEP8 and clean Flask structure
3. Ensure routes are modular and templates extend `base.html` where possible
4. Add your name to the CONTRIBUTORS.md (if added)

---

## 📃 License

This project is for academic/educational use — feel free to adapt and extend.
