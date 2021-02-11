from flask_wtf import FlaskForm
from wtforms import TextField, StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo


class CustomerSignupForm(FlaskForm):
    email = TextField('Email', [DataRequired()])
    password = PasswordField('Password', [DataRequired(), EqualTo('confirm_password', message="Passwords must match.")])
    confirm_password = PasswordField('Confirm Password')
    accept_terms = BooleanField('I accept the Terms of Service and Privacy Notice', [DataRequired()])
    submit = SubmitField('Sign Up')


class CustomerLoginForm(FlaskForm):
    email = TextField('Email', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log in')
