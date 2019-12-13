from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField,IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, InputRequired
from firmware_update_patch.models import User, Patch
import random


class RegistrationForm(FlaskForm):

    username = StringField('Username',validators=[DataRequired(),Length(min=2,max=20)])
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(),EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self,username):

        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a diffrent one.')
    def validate_email(self,email):

        user = User.query.filter_by(email=email.data).first()
        if user:
           raise ValidationError('That email is taken. Please choose a diffrent one.')


class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired()])
    submit = SubmitField('Login')


class PatchForm(FlaskForm):
    #build_id = random.randint(1111,9999)
    patch_build_id = IntegerField('Patch Build Id',validators=[DataRequired()])
    patch_name = StringField('Patch Name',validators=[DataRequired()])
    patch_discription = TextAreaField('Description',validators=[DataRequired()])
   
    remove = TextAreaField('Remove')

    #boot_add = TextAreaField('Boot')
    #core_add = StringField('Core')
    #basic_add = TextAreaField('Basic')
    #apps_add = TextAreaField('Apps')
    #data_file_add = TextAreaField('Data')

    submit = SubmitField('Build')

