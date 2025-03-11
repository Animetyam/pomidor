import os
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
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
    mode = request.args.get('mode')
    work_time = session['custom_timer']['work_time']
    break_time = session['custom_timer']['break_time']
    timer = mongo.db.modes.find_one({'role': session['role']})
    if timer:
        if mode == 'low':
            work_time = timer['low_work_time']
            break_time = timer['low_break_time']
        if mode == 'full':
            work_time = timer['work_time']
            break_time = timer['break_time']
    return render_template('index.html', work_time=work_time, break_time=break_time)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user'):
        return redirect(url_for('mode_selection'))
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
                                   'password': generate_password_hash(password, method='pbkdf2:sha256'), 
                                   'role': role,
                                   'about_me': 'Here you can add some information about you',
                                   'profile_stats': {'max_streak': 0, 'champion': False},
                                   'profile_xp': 0,
                                   'friends': [],
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
        user = mongo.db.users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['user'] = username
            session['role'] = user['role']
            session['profile_pic'] = user['profile_pic']
            session['about_me'] = user['about_me']
            session['profile_xp'] = user['profile_xp']
            session['custom_timer'] = user['custom_timer']
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
            password = mongo.db.users.find_one({'username': session['user']})['password']
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
        return redirect(url_for('profile'))
    return render_template('prof_settings.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('user'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        if request.form['work_time']:
            session['custom_timer']['work_time'] = request.form['work_time']
        if request.form['break_time']:
            session['custom_timer']['break_time'] = request.form['break_time']
        mongo.db.users.update_one({'username': session['user']}, {'$set': {'custom_timer': {'work_time': session['custom_timer']['work_time'], 'break_time': session['custom_timer']['break_time']}}})
        flash('Timer updated successfully!')
        return redirect(url_for('index'))
    
    work_time = session['custom_timer']['work_time']
    break_time = session['custom_timer']['break_time']
    return render_template('settings.html', work_time=work_time, break_time=break_time)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('user'):
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'username': session['user']})
    if user:
        session['user'] = user['username']
        session['role'] = user['role']
        session['profile_pic'] = user['profile_pic']
        session['about_me'] = user['about_me']
        session['profile_xp'] = user['profile_xp']
        session['custom_timer'] = user['custom_timer']
        session['profile_stats'] = user['profile_stats']
    
    if request.method == 'POST':
        new_role = request.form.get('role')
        mongo.db.users.update_one({'username': session['user']}, {'$set': {'role': new_role}})
        flash('Role updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', current_role=session['role'])

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/mode_selection')
def mode_selection():
    if not session.get('user'):
        return redirect(url_for('login'))
    return render_template('mode_selection.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/update_streak', methods=['POST'])
def update_streak():
    if 'current_streak' in session:
        session['current_streak'] += 1
    else:
        session['current_streak'] = 1
    return 'Streak updated'

@app.route('/reset_streak', methods=['POST'])
def reset_streak():
    if 'current_streak' in session:
        session['profile_xp'] = session['profile_xp'] + session['current_streak']*100 + session['current_streak']**4
        user = mongo.db.users.find_one({'username': session['user']})
        if user['profile_stats']['max_streak']<session['current_streak']:
            user['profile_stats']['max_streak'] = session['current_streak']
        mongo.db.users.update_one({'username': session['user']}, {'$set': {'profile_xp': session['profile_xp'], 'profile_stats': {'max_streak': user['profile_stats']['max_streak'], 'champion': user['profile_stats']['champion']}}})
        users = mongo.db.users.find().sort('profile_xp', -1)
        if users:
            if users[0] and users[0]['profile_xp'] > 0 and users[0]['profile_stats']['champion'] == False:
                mongo.db.users.update_one({'username': users[0]['username']}, {'$set': {'profile_stats': {'max_streak': users[0]['profile_stats']['max_streak'], 'champion': True}}})  
        session.pop('current_streak')
    return 'Streak reset'

@app.route('/leaderboard')
def leaderboard():
    users = mongo.db.users.find().sort('profile_xp', -1)
    
    current_user = session.get('user')
    friends = []
    if current_user:
        user_data = mongo.db.users.find_one({'username': current_user})
        if user_data and 'friends' in user_data:
            friends = list(mongo.db.users.find(
                {'username': {'$in': user_data['friends']}}
            ).sort('profile_xp', -1))
    return render_template('leaderboard.html', users=users, friends=friends)

@app.route('/add_friend/<string:username_to_add>', methods=['GET'])
def add_friend(username_to_add):
    if 'user' not in session:
        return redirect(url_for('login')) 
    current_user = session['user']
    if current_user == username_to_add:
        error = "You can't add yourself as a friend."
        return render_template('error_template.html', error=error)
    user_to_add = mongo.db.users.find_one({'username': username_to_add})
    if not user_to_add:
        error = "User to add does not exist."
        return render_template('error_template.html', error=error)
    mongo.db.users.update_one(
        {'username': current_user},
        {'$addToSet': {'friends': username_to_add}} 
    )
    mongo.db.users.update_one(
        {'username': username_to_add},
        {'$addToSet': {'friends': current_user}} 
    )

    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True)
