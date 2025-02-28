import os
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from flask_session import Session
import json
from datetime import timedelta

app = Flask(__name__)
app.config['MONGO_URI'] = "mongodb://localhost:27017/pomodoro"
app.config['SECRET_KEY'] = 'superkey'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
UPLOAD_FOLDER = 'static/profilePictures'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
mongo = PyMongo(app)
Session(app)

@app.route('/')
def index():
    if not session.get('user'):
        return redirect(url_for('login'))
    return render_template('index.html', role=session['role'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confPass = request.form['confirm_password']
        role = request.form['role']
        if mongo.db.users.find_one({'username': username}):
            error = "A user with this username already exists, please choose another one."
            return render_template('register.html', error=error)           
        if confPass != password:
            error = "Passwords do not match."
            return render_template('register.html', error=error)
        mongo.db.users.insert_one({'username': username, 
                                   'password': password, 
                                   'role': role,
                                   'about_me': 'Here you can add some information about you',
                                   'profile_stats': {'max_streak': 0},
                                   'profile_xp': 100,
                                   'custom_timer': {'work_time': 30, 'break_time': 5},
                                   'profile_pic': 'defaultProfPic.png'})
        flash('Successfully Registered! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user'):
        return redirect(url_for('mode_selection'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = mongo.db.users.find_one({'username': username, 'password': password})
        
        if user:
            session['user'] = username
            session['role'] = user['role']
            session['password'] = user['password']
            session['profile_pic'] = user['profile_pic']
            session['about_me'] = user['about_me']
            session['profile_stats'] = user['profile_stats']
            session['profile_xp'] = user['profile_xp']
            return redirect(url_for('mode_selection'))
        else:
            error = "Invalid username or password!"
            return render_template('login.html', error = error)  
    return render_template('login.html')

@app.route('/prof_settings', methods=['GET', 'POST'])
def prof_settings():
    if request.method == 'POST':
        password = request.form['password']
        confPass = request.form['confirm_password']     
        about_me = request.form['about_me'] 
        file = request.files['profile_pic']
        if confPass != password:
            error = "Passwords do not match."
            return render_template('prof_settings.html', error=error)
        if not password:
            password = session['password']
        else:
            session['password'] = password
        if not about_me:
            about_me = session['about_me']
        else:
            session['about_me'] = about_me
        if not file:
            profile_pic = session['profile_pic']
        else:
            if file.filename.endswith(('.png', '.jpg')):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                profile_pic = file.filename
                session['profile_pic'] = file.filename
            else:
                error = "You can only upload files with jpg extension!"
                return render_template('prof_settings.html', error = error)      
        mongo.db.users.update_one({'username': session['user']}, {'$set': {'password': password, 'about_me': about_me, 'profile_pic': profile_pic}})
        flash('Profile updated successfully!')
    return render_template('prof_settings.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('user'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        work_time = request.form.get('work_time', 25)
        break_time = request.form.get('break_time', 5)
        session['work_time'] = work_time
        session['break_time'] = break_time
        return redirect(url_for('index'))
    
    if session['role'] == 'student':
        work_time = 30
        break_time = 5
    else:  # employee
        work_time = 60
        break_time = 15

    session['work_time'] = work_time
    session['break_time'] = break_time
    return render_template('settings.html', work_time=work_time, break_time=break_time)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('user'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_role = request.form.get('role')
        mongo.db.users.update_one({'username': session['user']}, {'$set': {'role': new_role}})
        session['role'] = new_role  # update the role in the session
        flash('Role updated successfully!', 'success')

        # set timer values based on the new role
        if new_role == 'student':
            session['work_time'] = 30
            session['break_time'] = 5
        else:  # employee
            session['work_time'] = 60
            session['break_time'] = 15

        return redirect(url_for('index'))

    return render_template('profile.html', current_role=session['role'])

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/mode_selection')
def mode_selection():
    return render_template('mode_selection.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
