import os
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from app import db
from app.models import Meal, WeightLog, Workout
import requests

API_KEY = os.environ.get("USDA_API_KEY")


def analyze_weight_trend(user_id):
    logs = (
        WeightLog.query.filter_by(user_id=user_id).order_by(WeightLog.date.asc()).all()
    )

    if len(logs) < 2:
        return None  # Not enough data

    first = logs[0]
    last = logs[-1]

    delta_days = (last.date - first.date).days
    if delta_days == 0:
        return None  # Avoid division by zero

    delta_weight = last.weight - first.weight
    rate_per_week = (delta_weight / delta_days) * 7

    return {
        "change": round(delta_weight, 1),
        "rate_per_week": round(rate_per_week, 2),
        "since": first.date.strftime("%b %d"),
    }


def _format_portion_label(portion):
    amount = portion.get("amount")
    measure = (portion.get("measureUnit") or {}).get("name")
    modifier = portion.get("modifier")
    parts = []
    if amount:
        parts.append(str(int(amount)) if amount == int(amount) else f"{amount:g}")
    if measure and measure not in ("undetermined", ""):
        parts.append(measure)
    if modifier:
        parts.append(modifier)
    return " ".join(parts).strip()


def search_usda_food(query, max_results=5):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "api_key": API_KEY,
        "query": query,
        "pageSize": max_results,
    }

    response = requests.get(url, params=params)
    data = response.json()

    results = []
    for item in data.get("foods", []):
        full_name = item.get("description", "")
        short_name = ", ".join(full_name.split(",")[:2]).strip()
        nutrients = {
            n["nutrientName"]: n["value"] for n in item.get("foodNutrients", [])
        }
        portions = []
        for p in item.get("foodPortions", []):
            grams = p.get("gramWeight")
            if not grams:
                continue
            label = _format_portion_label(p) or f"{grams:g}g"
            portions.append({"label": label, "grams": round(grams, 1)})
        # Deduplicate by (label, grams) keeping first-seen order
        seen = set()
        deduped = []
        for p in portions:
            key = (p["label"], p["grams"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(p)
        results.append(
            {
                "fdc_id": item.get("fdcId"),
                "name": short_name or full_name,
                "full_name": full_name,
                "calories": nutrients.get("Energy", 0),
                "protein": nutrients.get("Protein", 0),
                "carbs": nutrients.get("Carbohydrate, by difference", 0),
                "fat": nutrients.get("Total lipid (fat)", 0),
                "portions": deduped,
            }
        )

    return results


def get_food_portions(fdc_id):
    """Fetch foodPortions from the USDA detail endpoint for a single food."""
    url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
    try:
        resp = requests.get(url, params={"api_key": API_KEY}, timeout=5)
        if not resp.ok:
            return []
        data = resp.json()
    except Exception:
        return []
    portions = []
    for p in data.get("foodPortions", []):
        grams = p.get("gramWeight")
        if not grams:
            continue
        label = _format_portion_label(p) or f"{grams:g}g"
        portions.append({"label": label, "grams": round(grams, 1)})
    seen = set()
    deduped = []
    for p in portions:
        key = (p["label"], p["grams"])
        if key not in seen:
            seen.add(key)
            deduped.append(p)
    return deduped


def estimate_tdee(user):
    weight_kg = (user.weight or 150) * 0.4536
    height_cm = (user.height or 68) * 2.54
    age = user.age or 25

    # Mifflin-St Jeor BMR (sex-aware)
    if (user.sex or "male") == "female":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5

    activity_multipliers = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extra_active": 1.9,
    }
    multiplier = activity_multipliers.get(user.activity_level or "moderately_active", 1.55)
    maintenance = round(bmr * multiplier)

    goal_adjustments = {
        "cutting": -500,
        "lean muscle": +300,
        "endurance": 0,
        "balanced": 0,
    }
    target = maintenance + goal_adjustments.get(user.fitness_goal or "balanced", 0)

    return {"maintenance": maintenance, "target": target}


def get_daily_summary(user):
    """Returns total calories and macros logged today."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    meals = Meal.query.filter(
        Meal.user_id == user.id,
        Meal.date >= today_start,
        Meal.date < today_end,
    ).all()

    return {
        "calories": round(sum(m.calories for m in meals), 1),
        "protein": round(sum(m.protein for m in meals), 1),
        "carbs": round(sum(m.carbs for m in meals), 1),
        "fats": round(sum(m.fats for m in meals), 1),
        "count": len(meals),
    }


def calculate_progress_stats(user):
    """Calculates macro averages and totals for the last 7 days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    meals = Meal.query.filter(
        Meal.user_id == user.id,
        Meal.date >= cutoff,
    ).all()

    if not meals:
        return None, 0, 0, 0

    avg_macros = {
        "calories": round(sum(m.calories for m in meals) / len(meals), 1),
        "protein": round(sum(m.protein for m in meals) / len(meals), 1),
        "carbs": round(sum(m.carbs for m in meals) / len(meals), 1),
        "fats": round(sum(m.fats for m in meals) / len(meals), 1),
    }
    total_protein = round(sum(m.protein for m in meals), 1)
    total_carbs = round(sum(m.carbs for m in meals), 1)
    total_fats = round(sum(m.fats for m in meals), 1)

    return avg_macros, total_protein, total_carbs, total_fats


def get_daily_calorie_history(user, days=7):
    """Returns daily calorie totals for the last N days as (labels, values)."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    labels, values = [], []
    for i in range(days - 1, -1, -1):
        day_start = today_start - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        meals = Meal.query.filter(
            Meal.user_id == user.id,
            Meal.date >= day_start,
            Meal.date < day_end,
        ).all()
        labels.append(day_start.strftime("%b %d"))
        values.append(round(sum(m.calories for m in meals), 1))
    return labels, values


@dataclass
class Insight:
    category: str   # nutrition | outcome | behavior | pattern | streak | nudge
    message: str
    severity: float
    extra: str = ""


def _aware(dt):
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _days_since_last_workout(user_id):
    last = (
        Workout.query.filter_by(user_id=user_id)
        .order_by(Workout.date.desc())
        .first()
    )
    if not last:
        return None
    return (datetime.now(timezone.utc) - _aware(last.date)).days


def _workouts_last_7_days(user_id):
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    return Workout.query.filter(
        Workout.user_id == user_id, Workout.date >= cutoff
    ).count()


def _weekday_weekend_avg(user_id, days=14):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    meals = Meal.query.filter(
        Meal.user_id == user_id, Meal.date >= cutoff
    ).all()
    totals = {}
    for m in meals:
        day = _aware(m.date).date()
        totals[day] = totals.get(day, 0) + (m.calories or 0)
    weekday = [v for d, v in totals.items() if d.weekday() < 5]
    weekend = [v for d, v in totals.items() if d.weekday() >= 5]
    if len(weekday) < 3 or len(weekend) < 2:
        return None
    return sum(weekday) / len(weekday), sum(weekend) / len(weekend)


def _calorie_streak(user, target):
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    streak = 0
    for i in range(30):
        day_start = today_start - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        cals = (
            db.session.query(func.coalesce(func.sum(Meal.calories), 0))
            .filter(
                Meal.user_id == user.id,
                Meal.date >= day_start,
                Meal.date < day_end,
            )
            .scalar()
            or 0
        )
        if cals == 0:
            break
        if cals <= target:
            streak += 1
        else:
            break
    return streak


# --- Rules -------------------------------------------------------------

def _rule_calorie_gap_today(user, tdee, daily):
    if datetime.now(timezone.utc).hour < 18 or daily["count"] == 0:
        return None
    target = tdee["target"]
    if daily["calories"] >= target * 0.6:
        return None
    gap = target - daily["calories"]
    if gap < 300:
        return None
    return Insight(
        category="nutrition",
        severity=min(gap / target, 1.0),
        message=(
            f"{daily['calories']:.0f}/{target} cal with the evening left. "
            f"Aim for a ~{gap:.0f} cal dinner."
        ),
    )

def _rule_protein_shortfall(user):
    avg, _, _, _ = calculate_progress_stats(user)
    if not avg:
        return None
    weight_kg = (user.weight or 150) * 0.4536
    target_p = weight_kg * 1.6
    if avg["protein"] >= target_p * 0.9:
        return None
    gap = target_p - avg["protein"]
    return Insight(
        category="nutrition",
        severity=min(gap / target_p, 1.0),
        message=(
            f"Protein averaging {avg['protein']:.0f}g, target {target_p:.0f}g. "
            "Front-load it at breakfast."
        ),
    )

def _rule_weight_trend(user):
    trend = analyze_weight_trend(user.id)
    if not trend:
        return None
    rate = trend["rate_per_week"]
    change = trend["change"]
    since = trend["since"]
    goal = user.fitness_goal or "balanced"

    if goal == "cutting":
        if rate < -2:
            return Insight("outcome", f"Losing {abs(rate):.1f} lbs/wk — too fast. Add 100-150 cal to protect muscle.", 0.9)
        if abs(rate) < 0.2:
            return Insight("outcome", f"Weight flat since {since} on a cut. Drop ~150 cal or add a cardio session.", 0.8)
        if rate > 0.3:
            return Insight("outcome", f"Gaining on a cut ({rate:+.1f} lbs/wk). Recheck logged portions.", 0.85)
        return Insight("outcome", f"Down {abs(change):.1f} lbs since {since}. Cut is working.", 0.35)
    if goal == "lean muscle":
        if rate > 1:
            return Insight("outcome", f"Up {rate:.1f} lbs/wk — likely more fat than needed. Pull back ~100 cal.", 0.7)
        if abs(rate) < 0.2:
            return Insight("outcome", f"Not gaining since {since}. Add ~200 cal, mostly carbs around workouts.", 0.75)
        if rate > 0.25:
            return Insight("outcome", f"Up {change:.1f} lbs since {since}. On pace for lean gains.", 0.35)
        return None
    if goal == "endurance":
        if abs(rate) > 1.5:
            return Insight("outcome", f"Weight swinging {rate:+.1f} lbs/wk. Stable fueling supports mileage.", 0.7)
        return None
    # balanced
    if rate > 1:
        return Insight("outcome", f"Up {rate:.1f} lbs/wk — faster than balanced. Tighten portions or add cardio.", 0.6)
    if abs(rate) < 0.3:
        return Insight("outcome", f"Weight steady since {since}. Maintenance is dialed in.", 0.3)
    return None

def _rule_workout_cadence(user):
    days = _days_since_last_workout(user.id)
    weekly = _workouts_last_7_days(user.id)
    if days is None:
        return Insight("behavior", "No workouts logged yet. A 20-min walk counts.", 0.6)
    if days < 3:
        return None
    return Insight(
        category="behavior",
        severity=min(days / 7, 1.0),
        message=f"{days} days since last workout. Weekly total: {weekly}. Even 20 min keeps the habit.",
    )

def _rule_weekend_gap(user):
    split = _weekday_weekend_avg(user.id)
    if not split:
        return None
    wd, we = split
    if we - wd < 400:
        return None
    return Insight(
        category="pattern",
        severity=min((we - wd) / 1000, 1.0),
        message=f"Weekdays avg {wd:.0f} cal, weekends {we:.0f}. The deficit leaks on Sat/Sun.",
    )

def _rule_streak(user, tdee):
    streak = _calorie_streak(user, tdee["target"])
    if streak < 5:
        return None
    return Insight(
        category="streak",
        severity=0.5,
        message=f"{streak}-day streak under target. Weight's tracking with it.",
    )

# --- Orchestrator ------------------------------------------------------

def _unlock_hints(user, daily):
    hints = []
    if daily["count"] == 0:
        hints.append("Log a meal today to unlock nutrition insights.")
    weight_count = WeightLog.query.filter_by(user_id=user.id).count()
    if weight_count < 2:
        hints.append("Log your weight a couple of times to unlock trend insights.")
    cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    meal_days = (
        db.session.query(func.count(func.distinct(func.date(Meal.date))))
        .filter(Meal.user_id == user.id, Meal.date >= cutoff)
        .scalar()
        or 0
    )
    if meal_days < 7:
        hints.append("Log meals across more days to unlock pattern insights.")
    return hints

def compute_insights(user, limit=3):
    """Return (ranked_insights, unlock_hints)."""
    tdee = estimate_tdee(user)
    daily = get_daily_summary(user)

    candidates = [
        _rule_calorie_gap_today(user, tdee, daily),
        _rule_protein_shortfall(user),
        _rule_weight_trend(user),
        _rule_workout_cadence(user),
        _rule_weekend_gap(user),
        _rule_streak(user, tdee),
    ]
    insights = [c for c in candidates if c is not None]
    insights.sort(key=lambda x: x.severity, reverse=True)
    return insights[:limit], _unlock_hints(user, daily)

def generate_recommendation(user):
    insights, _ = compute_insights(user, limit=2)
    if not insights:
        return (
            "Log a few more meals and workouts to unlock personalised insights.",
            "nudge",
            "",
        )
    top = insights[0]
    extra = ""
    if len(insights) > 1 and insights[1].category != top.category:
        extra = insights[1].message
    return top.message, top.category, extra
