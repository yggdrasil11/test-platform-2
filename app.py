from flask import Flask, render_template, request, redirect, url_for, session
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Define the number of questions
NUM_QUESTIONS = 60

def load_users():
    with open('users.json') as f:
        return json.load(f)

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)  # Add indent parameter for human-readable format

logs = []

def log_event(user, event):
    timestamp = datetime.now().isoformat()
    log_entry = {'user': user, 'event': event, 'timestamp': timestamp}
    logs.append(log_entry)
    # Save log entry to a file
    with open('logs.json', 'a') as f:
        f.write(json.dumps(log_entry) + "\n")

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    users = load_users()
    if username in users and users[username]['password'] == password:
        if users[username]['used']:
            error = "This login has already been used."
            return render_template('login.html', error=error)
        else:
            users[username]['used'] = True
            save_users(users)
            session['username'] = username
            session['current_page'] = 1
            log_event(username, 'User logged in')
            return redirect(url_for('consent'))
    else:
        error = "Invalid credentials. Please try again."
        return render_template('login.html', error=error)

@app.route('/consent', methods=['GET'])
def consent():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('consent.html')

@app.route('/consent', methods=['POST'])
def consent_post():
    if 'username' not in session:
        return redirect(url_for('index'))
    username = session['username']
    session['consented'] = True
    log_event(username, 'User consented to participate in the assessment')
    return redirect(url_for('test_page', page_number=1))

@app.route('/test/<int:page_number>', methods=['GET'])
def test_page(page_number):
    if 'username' not in session or 'consented' not in session:
        return redirect(url_for('index'))
    if page_number > NUM_QUESTIONS:  # Use the variable here
        return redirect(url_for('thank_you'))
    image_url = url_for('static', filename=f'images/page{page_number}.jpeg')
    return render_template('main.html', image_url=image_url)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    answer = request.form['answer']
    username = session['username']
    current_page = session['current_page']
    timestamp = datetime.now().isoformat()
    log_entry = {'user': username, 'page': current_page, 'timestamp': timestamp, 'answer': answer}
    logs.append(log_entry)
    
    # Save log entry to a file
    with open('logs.json', 'a') as f:
        f.write(json.dumps(log_entry) + "\n")
    
    session['current_page'] += 1
    return redirect(url_for('test_page', page_number=session['current_page']))

@app.route('/thank_you', methods=['GET'])
def thank_you():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('thank_you.html')

if __name__ == '__main__':
    app.run(debug=True)
