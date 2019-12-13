from flask import render_template, url_for, flash, redirect, request, abort, session,jsonify
from firmware_update_patch import app, db, bcrypt, login_manager, dropzone
from firmware_update_patch.forms import RegistrationForm, LoginForm, PatchForm
from firmware_update_patch.models import User, Patch
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug import secure_filename

import random
import os
import os.path
from os import path
import shutil
import pathlib
from pathlib import Path

#Login Page
@app.route('/',methods=['GET','POST'])
@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password','danger')

    return render_template('login.html',title='Login',form=form)


#Home Page
@app.route('/home')
@login_required
def home():
    page = request.args.get('page',1,type=int)
    patch = Patch.query.filter_by(author=current_user).order_by(Patch.date_posted.desc()).paginate(page=page,per_page=4)
    patch_len = len(db.session.query(Patch).all())

    return render_template('home.html',title='Home',patch_len=patch_len,patch=patch)


#Register Page
@app.route('/register',methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your Account has been created! You are now able to login','success')
        return redirect(url_for('login'))
    return render_template('register.html',title='Register',form=form)  


#Build Patch
@app.route('/build_patch',methods=['GET','POST'])
@login_required
def build_patch():
    form = PatchForm()

    #Generate Build-Id
    build_id = random.randint(1111,9999)
    patch_record_path = '/var/www/html/Firmware-Update-Patch-Records/'

    #Make Patch Id work directory
    #Check if the above path is empty
    if len(os.listdir(patch_record_path)) == 0:
        pass
    else:
        #Remove all the Folders which don't have finish.true files
        for f in os.listdir(patch_record_path):
            file = pathlib.Path(patch_record_path+f+"/"+"finish.true")
            if file.exists():
                pass
            else:
                shutil.rmtree(patch_record_path + f)


    #Make patch-id working Directory
    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id))
    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template")

    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/remove")

    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/add")
    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/add/boot")
    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/add/basic")
    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/add/core")
    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/add/apps")
    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/add/data")

    #Package Uploads Path
    uploads_boot_dir = os.path.join(app.instance_path, '/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/add/boot")
    
    if form.validate_on_submit():

        patch_update = Patch(patchgenid=form.patch_build_id.data,author=current_user,patchname=form.patch_name.data,discription=form.patch_discription.data)
        
        #Get the list of files to be removed
        remove_list = form.remove.data
        remove_list_list = []

        if not remove_list:

            Path('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/remove/"+"empty").touch()
        else:
            remove_list_list = remove_list.split(':')
            for r in remove_list_list:
                Path('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/remove/"+r).touch()

        db.session.add(patch_update)
        db.session.commit()
        
        #Finish
        Path('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"finish.true").touch()

        return redirect(url_for('home'))
        
    return render_template('build_patch.html',title='Build Patch',build_id=build_id,form=form)



#Logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))    