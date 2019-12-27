from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField,IntegerField,RadioField
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
    patch_build_id = IntegerField('Patch Build Id',render_kw={'readonly':True},validators=[DataRequired()])
    patch_name = StringField('Patch Name',validators=[DataRequired()])
    min_img_build = IntegerField('Minimum')
    max_img_build = IntegerField('Maximum')
    os_type = SelectField('OS Architecture',choices=[('32','32-Bit'),('64','64-Bit')])
    
    patch_discription = TextAreaField('Description',validators=[DataRequired()])
    remove = TextAreaField('Remove')
    add = TextAreaField('Add')
    install_script = TextAreaField('install')
    submit = SubmitField('Build')

