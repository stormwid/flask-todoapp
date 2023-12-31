from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, DateField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length
from app.models import User

# Login, RegistrationForm und EditProfileFormvon microblog uebernommen. TaskForm, EditTaskForm und ShareTaskListForm wurden von mir erstellt
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

# Form um Tasks zu erfassen
class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=140)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    due_date = DateField('Due Date', format='%Y-%m-%d')
    submit = SubmitField('Add Task')

# Form um Tasks zu editieren
class EditTaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=140)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    due_date = DateField('Due Date', format='%Y-%m-%d')
    submit = SubmitField('Save Task')

# Form um Username einzugeben mit dem Taskliste geteilt werden soll
class ShareTaskListForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=64)])
    share = SubmitField('Share Task List')

    