# Smart Fitness Tracker

A full-stack fitness tracking application built with Flask and SQLite. Users can register, log in, track workouts, and receive personalized meal and workout recommendations based on a custom recommendation algorithm.

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
