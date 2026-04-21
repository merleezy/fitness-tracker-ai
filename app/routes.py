from datetime import datetime, timezone
from flask import jsonify, request, redirect, url_for, render_template, flash, session
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import or_
from app import app, db  # type: ignore
from app.models import Meal, User, WeightLog, Workout, Recommendation
from app.forms import (
    MealForm,
    ProfileForm,
    WeightForm,
    WorkoutForm,
    UserRegistrationForm,
    LoginForm,
)
from app.utils import (
    estimate_tdee,
    generate_recommendation,
    search_usda_food,
    calculate_progress_stats,
    get_daily_summary,
)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/dashboard")
@login_required
def user_dashboard():
    user = current_user

    # OPTIONAL: Auto-generate a rec if no recent one exists
    rec = (
        Recommendation.query.filter_by(user_id=user.id)
        .order_by(Recommendation.timestamp.desc())
        .first()
    )
    if (
        not rec
        or (
            datetime.now(timezone.utc) - rec.timestamp.replace(tzinfo=timezone.utc)
        ).total_seconds()
        > 3600
    ):
        meal, workout, note = generate_recommendation(user)
        rec = Recommendation(
            user_id=user.id, meal_rec=meal, workout_rec=workout, trend_note=note
        )
        db.session.add(rec)
        db.session.commit()

    workouts = Workout.query.filter_by(user_id=user.id).all()
    meals = Meal.query.filter_by(user_id=user.id).all()
    recommendation = (
        Recommendation.query.filter_by(user_id=user.id)
        .order_by(Recommendation.timestamp.desc())
        .first()
    )
    daily_summary = get_daily_summary(user)
    tdee = estimate_tdee(user)

    return render_template(
        "user_dashboard.html",
        user=user,
        workouts=workouts,
        meals=meals,
        recommendation=recommendation,
        daily_summary=daily_summary,
        tdee=tdee,
    )


@app.route("/dashboard_redirect", methods=["POST"])
def dashboard_redirect():
    # Redirect to the generic dashboard route
    return redirect(url_for("user_dashboard"))


@app.route("/log_workout", methods=["GET", "POST"])
@login_required
def log_workout():
    form = WorkoutForm()
    if form.validate_on_submit():
        workout = Workout(
            type=form.type.data,
            duration=form.duration.data,
            calories_burned=form.calories_burned.data,
            user_id=current_user.id,
        )
        db.session.add(workout)
        db.session.commit()
        flash("Workout logged successfully!", "success")
        return redirect(url_for("user_dashboard"))

    return render_template("log_workout.html", form=form, user=current_user)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("user_dashboard"))
    form = UserRegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        existing_username = User.query.filter_by(username=form.username.data).first()
        if existing_user or existing_username:
            flash("Email or username already in use.", "danger")
            return redirect(url_for("register"))

        user = User(
            username=form.username.data,
            name=form.name.data,
            email=form.email.data,
            age=form.age.data,
            weight=form.weight.data,
            height=form.height.data,
            fitness_goal=form.fitness_goal.data,
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        # Log initial weight
        log = WeightLog(
            user_id=user.id, weight=user.weight, date=datetime.now(timezone.utc)
        )
        db.session.add(log)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for("register_success"))
    return render_template("register.html", form=form)


@app.route("/register_success")
def register_success():
    return render_template("register_success.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("user_dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        identifier = (form.email.data or "").strip()
        user = User.query.filter(
            or_(User.email == identifier, User.username == identifier)
        ).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get("next")
            if not next_page or not next_page.startswith("/"):
                next_page = url_for("user_dashboard")
            return redirect(next_page)
        else:
            flash("Invalid email/username or password.", "danger")
    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/log_meal", methods=["GET", "POST"])
@login_required
def log_meal():
    form = MealForm()

    if request.method == "GET" and "prefill" in session:
        pre = session.pop("prefill")
        form.name.data = pre["name"]
        form.calories.data = pre["calories"]
        form.protein.data = pre["protein"]
        form.carbs.data = pre["carbs"]
        form.fats.data = pre["fats"]
        flash(f"Preloaded from: {pre['name']}", "info")

    if form.validate_on_submit():
        meal = Meal(
            name=form.name.data,
            calories=form.calories.data,
            protein=form.protein.data,
            carbs=form.carbs.data,
            fats=form.fats.data,
            user_id=current_user.id,
        )
        db.session.add(meal)
        db.session.commit()
        flash("Meal logged successfully!", "success")
        return redirect(url_for("user_dashboard"))

    return render_template("log_meal.html", form=form, user=current_user)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        # Check if username or email is changing to something already used
        if form.username.data != current_user.username:
            if User.query.filter_by(username=form.username.data).first():
                flash("Username already taken.", "danger")
                return render_template(
                    "edit_profile.html", form=form, user=current_user
                )

        if form.email.data != current_user.email:
            if User.query.filter_by(email=form.email.data).first():
                flash("Email already in use.", "danger")
                return render_template(
                    "edit_profile.html", form=form, user=current_user
                )

        # Update fields
        current_user.name = form.name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.age = form.age.data
        current_user.weight = form.weight.data
        if not WeightLog.query.filter_by(user_id=current_user.id).first():
            log = WeightLog(
                user_id=current_user.id,
                weight=current_user.weight,
                date=datetime.now(timezone.utc),
            )
            db.session.add(log)
        current_user.height = form.height.data
        current_user.fitness_goal = form.fitness_goal.data

        # Update password if provided
        if form.password.data:
            current_user.set_password(form.password.data)

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("user_dashboard"))

    return render_template("edit_profile.html", form=form, user=current_user)


@app.route("/recommend", methods=["POST"])
@login_required
def create_recommendation():
    meal, workout, trend_note = generate_recommendation(current_user)
    rec = Recommendation(
        user_id=current_user.id,
        meal_rec=meal,
        workout_rec=workout,
        trend_note=trend_note,
    )
    db.session.add(rec)
    db.session.commit()

    flash("New recommendation generated!", "success")
    return redirect(
        url_for("user_dashboard", ts=datetime.now(timezone.utc).timestamp())
    )


@app.route("/recommendations")
@login_required
def recommendation_history():
    recommendations = (
        Recommendation.query.filter_by(user_id=current_user.id)
        .order_by(Recommendation.timestamp.desc())
        .all()
    )
    return render_template(
        "recommendation_history.html",
        user=current_user,
        recommendations=recommendations,
    )


@app.route("/recommendation_feedback/<int:rec_id>/<status>", methods=["POST"])
@login_required
def recommendation_feedback(rec_id, status):
    recommendation = Recommendation.query.get_or_404(rec_id)

    if recommendation.user_id != current_user.id:
        flash("You are not authorized to modify this recommendation.", "danger")
        return redirect(url_for("user_dashboard"))

    if status not in ["followed", "skipped"]:
        flash("Invalid feedback option.", "danger")
        return redirect(url_for("user_dashboard"))

    recommendation.followed = status
    db.session.commit()
    flash(f"Recommendation marked as {status}.", "success")
    return redirect(url_for("user_dashboard"))


@app.route("/search_food", methods=["POST"])
def search_food():
    data = request.get_json()
    query = data.get("query") if data else None
    if not query:
        return jsonify({"error": "No query provided"}), 400

    results = search_usda_food(query)
    if results:
        return jsonify(results[0])  # return top match
    return jsonify({"error": "No results found"}), 404


@app.route("/autocomplete_food", methods=["GET"])
def autocomplete_food():
    query = request.args.get("q", "")
    if not query.strip():
        return jsonify([])

    results = search_usda_food(query, max_results=10)
    suggestions = [{"label": f["name"], "value": f} for f in results]
    return jsonify(suggestions)


@app.route("/previous_meals")
@login_required
def previous_meals():
    meals = (
        Meal.query.filter_by(user_id=current_user.id)
        .order_by(Meal.id.desc())
        .limit(10)
        .all()
    )
    return render_template("previous_meals.html", user=current_user, meals=meals)


@app.route("/reuse_meal/<int:meal_id>")
@login_required
def reuse_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)

    if meal.user_id != current_user.id:
        flash("Unauthorized meal access.", "danger")
        return redirect(url_for("user_dashboard"))

    # Temporarily store meal data in session
    session["prefill"] = {
        "name": meal.name,
        "calories": meal.calories,
        "protein": meal.protein,
        "carbs": meal.carbs,
        "fats": meal.fats,
    }

    return redirect(url_for("log_meal"))


@app.route("/progress")
@login_required
def progress():
    workouts = Workout.query.filter_by(user_id=current_user.id).all()
    meals = Meal.query.filter_by(user_id=current_user.id).all()
    tdee = estimate_tdee(current_user)

    weight_logs = (
        WeightLog.query.filter_by(user_id=current_user.id)
        .order_by(WeightLog.date.asc())
        .all()
    )

    # Extract labels (dates) and data (weights)
    weight_labels = [log.date.strftime("%b %d") for log in weight_logs]
    weight_values = [log.weight for log in weight_logs]

    avg_macros, total_protein, total_carbs, total_fats = calculate_progress_stats(
        current_user
    )

    return render_template(
        "progress.html",
        user=current_user,
        workouts=workouts,
        meals=meals,
        tdee=tdee,
        avg_macros=avg_macros,
        total_protein=total_protein,
        total_carbs=total_carbs,
        total_fats=total_fats,
        weight_logs=weight_logs,
        weight_labels=weight_labels,
        weight_values=weight_values,
    )


@app.route("/log_weight", methods=["GET", "POST"])
@login_required
def log_weight():
    form = WeightForm()

    if form.validate_on_submit():
        new_weight = form.weight.data

        # Save to weight log
        log = WeightLog(
            user_id=current_user.id, weight=new_weight, date=datetime.now(timezone.utc)
        )
        db.session.add(log)

        # Update the user's current weight
        current_user.weight = new_weight
        db.session.commit()

        flash("Weight logged and profile updated!", "success")
        return redirect(url_for("progress"))

    return render_template("log_weight.html", form=form, user=current_user)


@app.route("/previous_workouts")
@login_required
def previous_workouts():
    workouts = (
        Workout.query.filter_by(user_id=current_user.id)
        .order_by(Workout.date.desc())
        .all()
    )
    return render_template(
        "previous_workouts.html", workouts=workouts, user=current_user
    )


@app.route("/delete_weight/<int:log_id>", methods=["POST"])
@login_required
def delete_weight(log_id):
    log = WeightLog.query.get_or_404(log_id)

    if log.user_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("progress"))

    if WeightLog.query.filter_by(user_id=log.user_id).count() <= 1:
        flash("You must have at least one weight entry.", "warning")
        return redirect(url_for("progress"))

    db.session.delete(log)
    db.session.commit()
    flash("Weight log deleted.", "success")

    # Recalculate the user's current weight
    latest_log = (
        WeightLog.query.filter_by(user_id=log.user_id)
        .order_by(WeightLog.date.desc())
        .first()
    )

    if latest_log:
        current_user.weight = latest_log.weight
    else:
        current_user.weight = None  # or default value like 0
    db.session.commit()

    return redirect(url_for("progress"))
