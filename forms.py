from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, EqualTo, Email, Regexp, Length, ValidationError

from models import User

class RegistrationForm(Form):
    username = StringField('Username', validators=[Regexp("\A[a-zA-Z0-9]+\Z")])
    email = StringField('Email address', validators=[Email()])
    password = PasswordField('Password', validators=[
        Length(min=8, message='Password must be at least 8 characters long.'),
        EqualTo('confirm', message='Passwords must match.')
    ])
    confirm = PasswordField('Confirm password')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("That username is already in use.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("That email address is already in use.")

class LoginForm(Form):
    username_or_email = StringField('Username or email address', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

    def __init__(self, *a, **kw):
        self.validated_user = None
        super(LoginForm, self).__init__(*a, **kw)

    def validate_username_or_email(self, field):
        try:
            self.validated_user = User.validate(field.data, self.password.data)
        except RuntimeError:
            raise ValidationError("Invalid username/email or password.")
