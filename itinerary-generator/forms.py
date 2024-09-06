from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email, Length


class UserAddForm(FlaskForm):
    """Form to add a new user."""

    username = StringField('Username', validators=[DataRequired(message="Please enter a username.")])
    email = StringField('E-mail', validators=[DataRequired(message="Please enter your email."), Email(message="Please enter a valid email.")])
    password = PasswordField('Password', validators=[Length(min=6, message="Your password needs to be at least 6 characters.")])
    image_url = StringField('(Optional) Image URL')


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired(message="Please enter a username.")])
    password = PasswordField('Password', validators=[Length(min=6, message="Your password needs to be at least 6 characters.")])
    

