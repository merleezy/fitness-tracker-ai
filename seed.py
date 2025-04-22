from app import app, db
from app.models import User, Workout, Meal, WeightLog
from datetime import datetime, timedelta, UTC

with app.app_context():
    db.drop_all()
    db.create_all()

    # === Users: Representing Different Fitness Goals and Trends ===
    users = [
        User(username="isaac", name="Isaac", email="isaac@example.com", age=22, weight=218, height=75, fitness_goal="cutting"),
        User(username="emma", name="Emma", email="emma@example.com", age=28, weight=147.5, height=65, fitness_goal="lean muscle"),
        User(username="alex", name="Alex", email="alex@example.com", age=30, weight=180, height=70, fitness_goal="endurance"),
        User(username="maria", name="Maria", email="maria@example.com", age=26, weight=160, height=66, fitness_goal="balances"),
        User(username="jake", name="Jake", email="jake@example.com", age=32, weight=198, height=72, fitness_goal="lean muscle"),
    ]

    for user in users:
        user.set_password("password")

    db.session.add_all(users)
    db.session.commit()

    # === Map for Convenience ===
    user_map = {user.username: user for user in users}

    # === Workouts ===
    workouts = [
        # Isaac - Cutting
        Workout(type="HIIT", duration=25, calories_burned=360, user_id=user_map["isaac"].id),
        Workout(type="Strength", duration=45, calories_burned=400, user_id=user_map["isaac"].id),
        Workout(type="Zone 2 Cardio", duration=50, calories_burned=350, user_id=user_map["isaac"].id),

        # Emma - Lean Muscle
        Workout(type="Push Day", duration=40, calories_burned=380, user_id=user_map["emma"].id),
        Workout(type="Pull Day", duration=45, calories_burned=390, user_id=user_map["emma"].id),
        Workout(type="Leg Day", duration=50, calories_burned=420, user_id=user_map["emma"].id),

        # Alex - Endurance
        Workout(type="Cycling", duration=60, calories_burned=550, user_id=user_map["alex"].id),
        Workout(type="Running", duration=40, calories_burned=450, user_id=user_map["alex"].id),
        Workout(type="Swimming", duration=45, calories_burned=500, user_id=user_map["alex"].id),

        # Maria - Recomposition
        Workout(type="Circuit Training", duration=35, calories_burned=320, user_id=user_map["maria"].id),
        Workout(type="Pilates", duration=60, calories_burned=280, user_id=user_map["maria"].id),
        Workout(type="Bodyweight Strength", duration=30, calories_burned=300, user_id=user_map["maria"].id),

        # Jake - Bulking
        Workout(type="Heavy Upper Body", duration=60, calories_burned=420, user_id=user_map["jake"].id),
        Workout(type="Heavy Lower Body", duration=55, calories_burned=440, user_id=user_map["jake"].id),
        Workout(type="Hypertrophy Split", duration=45, calories_burned=400, user_id=user_map["jake"].id),
    ]
    db.session.add_all(workouts)

    # === Meals ===
    meals = [
        # Isaac
        Meal(name="Zoodles & Grilled Turkey", calories=320, protein=32, carbs=12, fats=10, user_id=user_map["isaac"].id),
        Meal(name="Protein Smoothie + Yogurt", calories=280, protein=35, carbs=8, fats=5, user_id=user_map["isaac"].id),

        # Emma
        Meal(name="Steak & Sweet Potato", calories=520, protein=40, carbs=30, fats=20, user_id=user_map["emma"].id),
        Meal(name="Quinoa Chicken Bowl", calories=480, protein=36, carbs=35, fats=18, user_id=user_map["emma"].id),

        # Alex
        Meal(name="Tofu Wrap", calories=420, protein=22, carbs=40, fats=15, user_id=user_map["alex"].id),
        Meal(name="Salmon + Brown Rice", calories=460, protein=35, carbs=30, fats=18, user_id=user_map["alex"].id),

        # Maria
        Meal(name="Egg White Omelet + Toast", calories=300, protein=28, carbs=22, fats=10, user_id=user_map["maria"].id),
        Meal(name="Greek Salad + Chicken", calories=350, protein=30, carbs=10, fats=15, user_id=user_map["maria"].id),

        # Jake
        Meal(name="Beef & Rice Bowl", calories=700, protein=45, carbs=60, fats=30, user_id=user_map["jake"].id),
        Meal(name="High-Calorie Shake", calories=600, protein=50, carbs=40, fats=20, user_id=user_map["jake"].id),
    ]
    db.session.add_all(meals)

    # === Weight Logs: Create trends (stable, slow gain, fast loss, etc.) ===
    now = datetime.now(UTC)
    
    weights = [
        # Isaac – Rapid weight loss (should trigger sustainability note)
        WeightLog(user_id=user_map["isaac"].id, weight=230, date=now - timedelta(days=21)),
        WeightLog(user_id=user_map["isaac"].id, weight=225, date=now - timedelta(days=14)),
        WeightLog(user_id=user_map["isaac"].id, weight=221, date=now - timedelta(days=7)),
        WeightLog(user_id=user_map["isaac"].id, weight=218, date=now),

        # Emma – Steady lean muscle gain (should trigger "on track")
        WeightLog(user_id=user_map["emma"].id, weight=145, date=now - timedelta(days=14)),
        WeightLog(user_id=user_map["emma"].id, weight=146.5, date=now - timedelta(days=7)),
        WeightLog(user_id=user_map["emma"].id, weight=147.5, date=now),

        # Alex – Endurance with fluctuating weight (should not trigger any extreme)
        WeightLog(user_id=user_map["alex"].id, weight=180, date=now - timedelta(days=14)),
        WeightLog(user_id=user_map["alex"].id, weight=179, date=now - timedelta(days=7)),
        WeightLog(user_id=user_map["alex"].id, weight=180, date=now),

        # Maria – Recomposition (no change at all, should suggest tweaks)
        WeightLog(user_id=user_map["maria"].id, weight=160, date=now - timedelta(days=21)),
        WeightLog(user_id=user_map["maria"].id, weight=160, date=now - timedelta(days=14)),
        WeightLog(user_id=user_map["maria"].id, weight=160, date=now - timedelta(days=7)),
        WeightLog(user_id=user_map["maria"].id, weight=160, date=now),

        # Jake – Bulking (slightly too fast — should suggest slower gain)
        WeightLog(user_id=user_map["jake"].id, weight=190, date=now - timedelta(days=14)),
        WeightLog(user_id=user_map["jake"].id, weight=195, date=now - timedelta(days=7)),
        WeightLog(user_id=user_map["jake"].id, weight=198, date=now),
    ]
    db.session.add_all(weights)

    db.session.commit()
    print("✅ Seed data loaded successfully.")
