from flask import render_template, url_for, flash, redirect, request, abort, session,jsonify
from firmware_update_patch import app, db, bcrypt, login_manager, dropzone
from firmware_update_patch.forms import RegistrationForm, LoginForm, PatchForm
from firmware_update_patch.models import User, Patch
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug import secure_filename
import urllib3
import random
import os
import os.path
from os import path
import shutil
import pathlib
from pathlib import Path
import wget
import subprocess
import tarfile

#Login Page
@app.route('/',methods=['GET','POST'])
@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        #if user and bcrypt.check_password_hash(user.password,form.password.data):
        if user and user.password == form.password.data:
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

    #return render_template('home.html',title='Home',patch_len=patch_len)
    return render_template('home.html',title='Home',patch_len=patch_len,patch=patch)


#Register Page
@app.route('/register',methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        #hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        #user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        user = User(username=form.username.data, email=form.email.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Your Account has been created! You are now able to login','success')
        return redirect(url_for('login'))
    return render_template('register.html',title='Register',form=form)  


#Function for Email
def send_mail(patchgenid,author,patchname,discription,pmd5sum):

    user = User.query.filter_by(username=current_user.username).first()
    
    send_to = user.email
    send_from = user.email
    server_mail = "mail.vxlsoftware.com"
    send_from_user_password = user.password
    subject = patchname.replace(' ','_')
    patch_url = "http://192.168.0.188/var/www/html/Firmware-Update-Patch-Records/"+str(patchgenid)+"/"+patchname.replace(' ','_')+'.tar.bz2'
    patch_md5sum = pmd5sum
    body_msg = f'" Hello All,\n Please find below details of Firmware Update :\n\nURL : {patch_url}\n\nMD5SUM : {pmd5sum}\n\nDescription:\n\n{discription}\n\nThanks and Regrads\n{user.username}"'

    cmd = "/usr/bin/swaks --to "+send_to+" --from "+send_from+" --server "+server_mail+" --auth LOGIN --auth-user "+send_from+" --auth-password "+send_from_user_password+" -tls --header "+"'Subject:Firmware Update Patch : '"+subject+" --body "+body_msg
    proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    o = proc.communicate()

    return print(o)
    return print(cmd)


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
    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update")

    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update/remove")

    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update/add")
    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update/add/boot")
    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update/add/basic")
    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update/add/core")
    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update/add/apps")
    os.makedirs('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update/add/data")
    
    if form.validate_on_submit():

        
        
        #Get the list of files to be removed
        remove_list = form.remove.data
        remove_list_list = []

        if not remove_list:
            Path('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update/remove/"+"empty").touch()
        else:
            remove_list_list = remove_list.split(':')
            for r in remove_list_list:
                Path('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update/remove/"+r).touch()

        #Get the list of files to be added
        add_list = form.add.data
        add_list_list = []

        if not add_list:
            Path('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update/add/"+"empty").touch()
        else:
            add_list_list = add_list.split(';')

            for a in add_list_list:
                prefix = a.split('-',1)

                #Check if Prefix have boot-,core-,apps-,basic-,data-
                if prefix[0].casefold() not in ['boot','core','basic','apps','data']:
                    flash(f'Missing Prefix in {prefix[0]}','danger')
                    return redirect(url_for('build_patch'))

                #Check URL is live or not
                try:

                    http = urllib3.PoolManager()
                    check_url = http.request('GET',prefix[1])

                    if check_url.status == 200:
                        print("URL IS LIVE and We are Downloading")

                        #Downloading Respect
                        if prefix[0].casefold() == 'boot':
                            print('BOOT FOUND')
                            wget.download(prefix[1],'/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update/add/boot/")

                        elif prefix[0].casefold() == 'core':
                            print('CORE FOUND')
                            wget.download(prefix[1],'/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update/add/core/")

                        elif prefix[0].casefold() == 'basic':
                            print('BASIC FOUND')
                            wget.download(prefix[1],'/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update/add/basic/")

                        elif prefix[0].casefold() == 'apps':
                            print('APPS FOUND')
                            wget.download(prefix[1],'/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update/add/apps/")

                        else:
                            print('DATA FOUND')
                            wget.download(prefix[1],'/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update/add/data/")

                    else:
                        flash(f'Invalid URL :{prefix[1]}','danger')
                        return redirect(url_for('build_patch'))
                
                except Exception as e:

                    print(str(e))
                    flash(f'Invalid URL :{prefix[1]}','danger')
                    return redirect(url_for('build_patch'))

        #Install script
        install_script = form.install_script.data
        if len(install_script) != 0:

            f = open('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/install","x")
            f.write("""#!/bin/bash\n\n""")

            install_list = form.install_script.data
            install_list_list = []

            #Writing Install Script        
            install_list_list = install_list.split(';')

            for i in install_list_list:
                f.write(i+'\n')

            f.close()
        else:
            f = open('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/install","x")
            f.write("""#!/bin/bash\n\n""")
            f.close()

        #Building Verify Patch script

        #Check for 32Bit 64Bit Arch
        user_arch_input = form.os_type.data

        if len(user_arch_input) == 0:
            flash(f'Please select the OS Architecture','danger')
            return redirect(url_for('build_patch'))

        #Get the size of packages to be added
        os.chdir('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/firmware_update/add")
        cmd = "du -schBM * | tail -n1 | awk -F' ' '{print $1}'"
        proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        o = proc.communicate()
        size_add_pkg = o[0].decode('utf8').replace("\n","")

        #Minimum and Maximum Build Version
        min_image_value = form.min_img_build.data   
        max_image_value = form.max_img_build.data

        #Check if min value should be less than max value
        if min_image_value > max_image_value:
            flash(f'Minimum Build {min_image_value} not validating Maximum Build {max_image_value}','danger')
            return redirect(url_for('build_patch'))

        #Writing findminmax script
        f = open('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/root/findminmax.sh","x")
        f.write(f"""#!/bin/bash\n
        #Check 32Bit 64bit Arch\n
        
        img_arch_type = `file /usr/verixo-bin/OS_Desktop`
        echo $img_arch_type | grep -i "ELF 32-bit LSB executable"
        img_status=$?
        
        img_type="Null"

        if [ $img_status -eq 0 ]
        then
            img_type=32
        else
            img_type=64
        fi
            
        if [ {user_arch_input} -ne "$img_type" ]
        then
            exit 1
        fi

        #Check for Min/Max Build

        /usr/verixo-bin/verify-patch.sh {min_image_value} {max_image_value}
        minmax_status=$?

        if [ $minmax_status -ne 0 ]
        then
            exit 1
        fi

        #Check for Update-Build\n
        if [ -f /root/firmware_update/add/basic/verixo-bin.sq ]
        then
            mkdir /opt/demo
            mount -o loop /root/firmware_update/add/basic/verixo-bin.sq /opt/demo
            build=`cat /opt/demo/usr/verixo-bin/.updatebuild`
            umount /opt/demo
            rm -rf /opt/demo

            /usr/verixo-bin/Firmwareupdate --checkupdatebuild $build
            build_status=$?

            if [ $build_status -ne 0 ]
            then
                exit 1
            fi
        fi

        #Check Add Packages Size
        /usr/verixo-bin/Firmwareupdate --checksize {size_add_pkg}
        size_status=$?

        if [ $size_status -ne 0 ]
        then
            exit 1
        fi
        
        #End of Script
        exit 0     """)

        f.close()

        

        #Check if Remove,Add TextField is empty
        if len(remove_list) == 0 and len(add_list) == 0 :

            flash(f'Invalid Patch Creation','danger')
            return redirect(url_for('build_patch'))


        #Building Patch Tar
        subprocess.call(['chmod','-R','755','/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)])
        patchname = form.patch_name.data.replace(' ','_')+'.tar.bz2'
        tar_file_path = '/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+'/'+patchname
        tar = tarfile.open(tar_file_path,mode='w:bz2')
        os.chdir('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"Build-Template/")
        tar.add(".")
        tar.close()

        #Damaging the Patch
        cmd = "damage corrupt /var/www/html/Firmware-Update-Patch-Records/"+str(build_id)+"/"+patchname+" 1"
        proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        o,e = proc.communicate()

        #MD5SUM of Patch
        cmd = "md5sum /var/www/html/Firmware-Update-Patch-Records/"+str(build_id)+"/"+patchname
        proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        o,e = proc.communicate()
        md5sum = o.decode('utf8')
        patch_md5sum = md5sum[:32]

        #Send Email
        #send_mail(patchgenid=form.patch_build_id.data,author=current_user,patchname=form.patch_name.data,discription=form.patch_discription.data,pmd5sum=patch_md5sum)
      
        #Finish
        #Path('/var/www/html/Firmware-Update-Patch-Records/'+str(build_id)+"/"+"finish.true").touch()

        #Update DataBase
        patch_update = Patch(patchgenid=form.patch_build_id.data,author=current_user,patchname=form.patch_name.data,discription=form.patch_discription.data,ostype=form.os_type.data)
        db.session.add(patch_update)
        db.session.commit()

        return redirect(url_for('home'))
        
    return render_template('build_patch.html',title='Build Patch',build_id=build_id,form=form)



#Logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))    