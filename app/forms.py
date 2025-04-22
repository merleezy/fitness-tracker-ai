from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, FloatField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, InputRequired

goal_choices = [
    ('cutting', 'Cutting (Fat Loss)'),
    ('lean muscle', 'Lean Muscle Gain'),
    ('endurance', 'Endurance'),
    ('balanced', 'General Fitness')
]

class UserRegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')])
    fitness_goal = SelectField("Fitness Goal", choices=[
        ('cutting', 'Cutting (Fat Loss)'),
        ('lean muscle', 'Lean Muscle Gain'),
        ('endurance', 'Endurance'),
        ('balanced', 'General Fitness')
    ], validators=[DataRequired()])
    age = IntegerField("Age", validators=[DataRequired()])
    weight = FloatField("Weight (lbs)", validators=[DataRequired()])
    height = FloatField("Height (inches)", validators=[DataRequired()])
    submit = SubmitField("Register")

class WorkoutForm(FlaskForm):
    type = SelectField('Workout Type', choices=[
        ('Cardio', 'Cardio'),
        ('Strength', 'Strength'),
        ('Flexibility', 'Flexibility'),
        ('HIIT', 'HIIT'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    
    duration = IntegerField('Duration (minutes)', validators=[DataRequired(), NumberRange(min=1)])
    calories_burned = IntegerField('Calories Burned', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Log Workout')
    
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')
    
class MealForm(FlaskForm):
    name = StringField("Meal Name", validators=[InputRequired()])
    calories = FloatField("Calories", validators=[InputRequired()])
    protein = FloatField("Protein", validators=[InputRequired()])
    carbs = FloatField("Carbs", validators=[InputRequired()])
    fats = FloatField("Fats", validators=[InputRequired()])
    submit = SubmitField("Save Meal")
    
class ProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("New Password", validators=[Optional()])
    confirm = PasswordField("Confirm Password", validators=[Optional(), EqualTo('password')])
    age = IntegerField('Age', validators=[DataRequired()])
    weight = FloatField('Weight (lbs)', validators=[DataRequired()])
    height = FloatField('Height (inches)', validators=[DataRequired()])
    fitness_goal = SelectField('Fitness Goal', choices=goal_choices, validators=[DataRequired()])
    submit = SubmitField('Update Profile')
    
class WeightForm(FlaskForm):
    weight = FloatField("Your Current Weight (lbs)", validators=[DataRequired()])
    submit = SubmitField("Log Weight")