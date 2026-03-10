from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, SubmitField, DateTimeField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from app.models.user import User


class RegistrationForm(FlaskForm):
    """Registration form with validation"""
    
    student_number = StringField('Student Number', validators=[
        DataRequired(message='Student number is required'),
        Length(min=5, max=20, message='Student number must be between 5 and 20 characters')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    
    full_name = StringField('Full Name')
    
    role = SelectField('Role', choices=[
        ('student', 'Student'),
        ('host', 'Host (Requires Approval)')
    ], default='student')
    
    submit = SubmitField('Register')
    
    def validate_student_number(self, field):
        """Check if student number already exists"""
        user = User.query.filter_by(student_number=field.data).first()
        if user:
            raise ValidationError('Student number already registered.')
    
    def validate_email(self, field):
        """Check if email already exists"""
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('Email address already registered.')


class LoginForm(FlaskForm):
    """Login form"""
    
    student_number = StringField('Student Number or Email', validators=[
        DataRequired(message='Please enter your student number or email')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Please enter your password')
    ])
    
    remember_me = BooleanField('Remember Me')
    
    submit = SubmitField('Login')


class ProfileForm(FlaskForm):
    """Profile update form"""
    
    full_name = StringField('Full Name')
    bio = TextAreaField('Bio', render_kw={"rows": 5})
    
    submit = SubmitField('Update Profile')


class WorkshopForm(FlaskForm):
    """Form for creating and editing workshops"""
    
    title = StringField('Workshop Title', validators=[
        DataRequired(message='Workshop title is required'),
        Length(min=5, max=200, message='Title must be between 5 and 200 characters')
    ])
    
    description = TextAreaField('Description', validators=[
        DataRequired(message='Workshop description is required'),
        Length(min=20, message='Description must be at least 20 characters')
    ])
    
    category = SelectField('Category', choices=[
        ('Programming', 'Programming'),
        ('Web Development', 'Web Development'),
        ('Data Science', 'Data Science'),
        ('Mobile Development', 'Mobile Development'),
        ('Design', 'Design'),
        ('Business', 'Business'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    
    date_time = DateTimeField('Date & Time', format='%Y-%m-%dT%H:%M', validators=[
        DataRequired(message='Date and time are required')
    ])
    
    venue = StringField('Venue', validators=[
        DataRequired(message='Venue is required'),
        Length(min=3, max=200, message='Venue must be between 3 and 200 characters')
    ])
    
    capacity = IntegerField('Capacity', validators=[
        DataRequired(message='Capacity is required'),
        NumberRange(min=1, max=500, message='Capacity must be between 1 and 500')
    ])
    
    submit = SubmitField('Save Workshop')
