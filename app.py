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
        role = request.form['role']
        mongo.db.users.insert_one({'username': username, 'password': password, 'role': role})
        flash('Successfully Registered! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = mongo.db.users.find_one({'username': username, 'password': password})
        
        if user:
            session['user'] = username
            session['role'] = user['role']
            return redirect(url_for('settings'))
        else:
            flash('Invalid username or password!', 'danger')
    return render_template('login.html')

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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
