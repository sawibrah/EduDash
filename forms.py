from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from flask_babel import lazy_gettext as _l
from models import User

class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[
        DataRequired(), 
        Length(min=4, max=20, message=_l("Username must be between 4 and 20 characters"))
    ])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    first_name = StringField(_l('First Name'), validators=[
        DataRequired(), 
        Length(min=2, max=50)
    ])
    last_name = StringField(_l('Last Name'), validators=[
        DataRequired(), 
        Length(min=2, max=50)
    ])
    password = PasswordField(_l('Password'), validators=[
        DataRequired(), 
        Length(min=6, message=_l("Password must be at least 6 characters"))
    ])
    confirm_password = PasswordField(_l('Confirm Password'), validators=[
        DataRequired(), 
        EqualTo('password', message=_l('Passwords must match'))
    ])
    
    # Additional fields for student profile (all new users are students by default)
    grade_level = SelectField(_l('Grade Level'), choices=[
        ('9th Grade', _l('9th Grade')),
        ('10th Grade', _l('10th Grade')),
        ('11th Grade', _l('11th Grade')),
        ('12th Grade', _l('12th Grade')),
        ('College', _l('College')),
        ('Graduate', _l('Graduate'))
    ], default='9th Grade')
    
    submit = SubmitField(_l('Create Account'))
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(_l('Username already taken. Please choose a different one.'))
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(_l('Email already registered. Please use a different email.'))

class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    submit = SubmitField(_l('Sign In'))

class ProfileForm(FlaskForm):
    first_name = StringField(_l('First Name'), validators=[
        DataRequired(), 
        Length(min=2, max=50)
    ])
    last_name = StringField(_l('Last Name'), validators=[
        DataRequired(), 
        Length(min=2, max=50)
    ])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Update Profile'))

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(_l('Current Password'), validators=[DataRequired()])
    new_password = PasswordField(_l('New Password'), validators=[
        DataRequired(), 
        Length(min=6, message=_l("Password must be at least 6 characters"))
    ])
    confirm_password = PasswordField(_l('Confirm New Password'), validators=[
        DataRequired(), 
        EqualTo('new_password', message=_l('Passwords must match'))
    ])
    submit = SubmitField(_l('Change Password'))
