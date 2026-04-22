"""
Demo account seeder.

CLI usage:
    flask seed-demo

Railway usage (no shell access):
    GET /admin/seed-demo?key=<SEED_KEY>   (set SEED_KEY env var on Railway)
"""
import random
from datetime import datetime, timezone, timedelta
from app import app, db
from app.models import User, Meal, Workout, WeightLog

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo1234"
DEMO_EMAIL = "demo@fitnesstracker.app"


# ---------------------------------------------------------------------------
# Meal pool — realistic entries with macros per serving
# ---------------------------------------------------------------------------
MEALS = [
    # (name, cal, protein, carbs, fats, meal_type)
    ("Scrambled eggs & toast",          380, 24, 32, 14, "Breakfast"),
    ("Oatmeal with banana",             320, 10, 58,  6, "Breakfast"),
    ("Greek yogurt & granola",          290, 18, 38,  6, "Breakfast"),
    ("Protein shake",                   210, 32,  8,  4, "Breakfast"),
    ("Avocado toast & eggs",            420, 20, 36, 18, "Breakfast"),
    ("Grilled chicken & rice",          520, 46, 52,  8, "Lunch"),
    ("Turkey wrap",                     460, 34, 44, 12, "Lunch"),
    ("Tuna salad sandwich",             410, 32, 38, 10, "Lunch"),
    ("Chicken Caesar salad",            390, 38, 18, 16, "Lunch"),
    ("Burrito bowl",                    580, 38, 64, 14, "Lunch"),
    ("Salmon & sweet potato",           540, 42, 44, 14, "Dinner"),
    ("Steak & roasted veg",             620, 52, 24, 28, "Dinner"),
    ("Ground turkey pasta",             580, 44, 58, 12, "Dinner"),
    ("Chicken stir-fry & rice",         510, 40, 52, 10, "Dinner"),
    ("Shrimp tacos",                    490, 36, 48, 12, "Dinner"),
    ("Cottage cheese & fruit",          180, 22, 18,  2, "Snack"),
    ("Apple & peanut butter",           210,  6, 26, 10, "Snack"),
    ("Protein bar",                     220, 20, 24,  6, "Snack"),
    ("Almonds",                         170,  6,  6, 14, "Snack"),
    ("Rice cakes & hummus",             190,  6, 28,  4, "Snack"),
]

# Heavier weekend options (push weekend average ~500 cal higher)
WEEKEND_EXTRAS = [
    ("Pancakes & syrup",                520, 12, 88, 14, "Breakfast"),
    ("Bacon & egg bagel",               580, 30, 52, 22, "Breakfast"),
    ("Burger & fries",                  880, 44, 80, 36, "Lunch"),
    ("Pizza (2 slices)",                720, 30, 84, 24, "Dinner"),
    ("Pasta with meat sauce",           680, 38, 72, 20, "Dinner"),
    ("Ice cream",                       310,  5, 42, 14, "Snack"),
    ("Chips & guac",                    380,  5, 42, 22, "Snack"),
]

WORKOUTS = [
    ("Running",          35, 320),
    ("Strength Training", 55, 380),
    ("HIIT",             30, 360),
    ("Cycling",          45, 340),
    ("Strength Training", 60, 410),
    ("Running",          40, 360),
    ("Strength Training", 50, 370),
    ("HIIT",             25, 300),
]


def _meal(user_id, entry, dt):
    name, cal, prot, carbs, fats, mtype = entry
    return Meal(
        user_id=user_id,
        name=name,
        calories=cal,
        protein=prot,
        carbs=carbs,
        fats=fats,
        meal_type=mtype,
        date=dt,
    )


def seed_demo():
    """Create (or reset) the demo account with 14 days of realistic data."""
    with app.app_context():
        # Wipe existing demo data
        existing = User.query.filter_by(username=DEMO_USERNAME).first()
        if existing:
            Meal.query.filter_by(user_id=existing.id).delete()
            Workout.query.filter_by(user_id=existing.id).delete()
            WeightLog.query.filter_by(user_id=existing.id).delete()
            db.session.delete(existing)
            db.session.commit()

        user = User(
            username=DEMO_USERNAME,
            name="Alex",
            email=DEMO_EMAIL,
            age=28,
            sex="male",
            weight=192.0,
            height=70.0,
            activity_level="moderately_active",
            fitness_goal="cutting",
        )
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        db.session.flush()

        today = datetime.now(timezone.utc).replace(
            hour=12, minute=0, second=0, microsecond=0
        )
        rng = random.Random(42)  # fixed seed for reproducibility

        # --- Meals (14 days) ---
        # Design: protein ~115-125g/day (target ~139g) → protein shortfall fires
        # Weekday cal ~1950, weekend cal ~2500 → weekend gap fires
        weekday_plan = [
            ("Scrambled eggs & toast",  380, 24, 32, 14, "Breakfast"),
            ("Grilled chicken & rice",  520, 46, 52,  8, "Lunch"),
            ("Chicken stir-fry & rice", 510, 40, 52, 10, "Dinner"),
            ("Cottage cheese & fruit",  180, 22, 18,  2, "Snack"),
        ]  # ~1590 cal, ~132g protein — add slight noise

        for day_offset in range(14, 0, -1):
            d = today - timedelta(days=day_offset)
            is_weekend = d.weekday() >= 5

            if is_weekend:
                pool = WEEKEND_EXTRAS
                entries = [
                    rng.choice([m for m in pool if m[5] == "Breakfast"]),
                    rng.choice([m for m in pool if m[5] == "Lunch"]),
                    rng.choice([m for m in pool if m[5] == "Dinner"]),
                    rng.choice([m for m in pool if m[5] == "Snack"]),
                ]
            else:
                entries = list(weekday_plan)
                # Add small calorie noise to avoid perfectly identical days
                noise = rng.randint(-60, 60)
                entries[0] = entries[0][:1] + (entries[0][1] + noise,) + entries[0][2:]

            for i, entry in enumerate(entries):
                hour = [7, 12, 18, 15][i]
                dt = d.replace(hour=hour, minute=rng.randint(0, 30))
                db.session.add(_meal(user.id, entry, dt))

        # --- Workouts ---
        # Last workout 4 days ago → cadence rule fires
        workout_days = [14, 12, 10, 8, 6, 4]
        for i, day_offset in enumerate(workout_days):
            w_type, duration, cals = WORKOUTS[i % len(WORKOUTS)]
            dt = today - timedelta(days=day_offset) - timedelta(hours=2)
            db.session.add(Workout(
                user_id=user.id,
                type=w_type,
                duration=duration,
                calories_burned=cals,
                date=dt,
            ))

        # --- Weight logs ---
        # 192 → ~188 over 14 days (gradual cut, ~0.3 lbs/day with noise)
        start_weight = 192.0
        for day_offset in range(14, -1, -1):
            days_in = 14 - day_offset
            # Gradual loss + small noise
            w = round(start_weight - (days_in * 0.28) + rng.uniform(-0.3, 0.3), 1)
            dt = today - timedelta(days=day_offset) - timedelta(hours=6)
            db.session.add(WeightLog(user_id=user.id, weight=w, date=dt))

        db.session.commit()
        print(f"Demo seeded — username: {DEMO_USERNAME}  password: {DEMO_PASSWORD}")
        return user


# Flask CLI command
import click

def register_commands(app):
    @app.cli.command("seed-demo")
    def seed_demo_command():
        """Create or reset the demo account."""
        seed_demo()
