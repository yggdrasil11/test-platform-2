from flask import Flask, render_template, request, redirect, url_for, session
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Define the number of questions
NUM_QUESTIONS = 6

def load_users():
    with open('users.json') as f:
        return json.load(f)

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)  # Add indent parameter for human-readable format

logs = []

def log_event(user, event, filename='logs.json'):
    timestamp = datetime.now().isoformat()
    log_entry = {'user': user, 'event': event, 'timestamp': timestamp}
    logs.append(log_entry)
    # Save log entry to a file
    with open(filename, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")

def load_viewed_pages():
    try:
        with open('viewed_pages.json') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_viewed_pages(viewed_pages):
    with open('viewed_pages.json', 'w') as f:
        json.dump(viewed_pages, f, indent=4)

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
            session['viewed_pages'] = []  # Track viewed pages
            log_event(username, 'User logged in')
            return redirect(url_for('consent'))
    else:
        error = "Invalid credentials. Please try again."
        return render_template('login.html', error=error)

@app.route('/consent', methods=['GET', 'POST'])
def consent():
    if 'username' not in session:
        return redirect(url_for('index'))
    username = session['username']
    viewed_pages = load_viewed_pages()
    if request.method == 'POST':
        session['consented'] = True
        log_event(username, 'User consented to participate in the assessment')
        viewed_pages[username] = viewed_pages.get(username, []) + ['consent']
        save_viewed_pages(viewed_pages)
        return redirect(url_for('test_page', page_number=1))
    if 'consent' in viewed_pages.get(username, []):
        return render_template('error.html', message="You cannot view this page again.")
    return render_template('consent.html')

@app.route('/test/<int:page_number>', methods=['GET'])
def test_page(page_number):
    if 'username' not in session or 'consented' not in session:
        return redirect(url_for('index'))
    username = session['username']
    viewed_pages = load_viewed_pages()
    session['viewed_pages'] = viewed_pages.get(username, [])  # Update session with latest viewed pages
    
    if page_number > NUM_QUESTIONS:  # Redirect to thank_you page if page_number exceeds NUM_QUESTIONS
        return redirect(url_for('thank_you'))
    
    page_key = f'test_page_{page_number}'
    if page_key in session['viewed_pages']:
        return render_template('error.html', message="You cannot view this page again.")
    
    # Update the session and viewed pages
    session['viewed_pages'].append(page_key)
    viewed_pages[username] = session['viewed_pages']
    save_viewed_pages(viewed_pages)
    
    image_url = url_for('static', filename=f'images/page{page_number}.jpeg')
    session['current_page'] = page_number
    return render_template('main.html', image_url=image_url, page_number=page_number)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    answer = request.form['answer']
    username = session['username']
    page_number = request.form['page_number']  # Get the actual page number from the form
    timestamp = datetime.now().isoformat()
    log_entry = {'user': username, 'page': page_number, 'timestamp': timestamp, 'answer': answer}
    logs.append(log_entry)
    
    # Save log entry to a file
    with open('logs.json', 'a') as f:
        f.write(json.dumps(log_entry) + "\n")
    
    # Read the latest viewed pages from the file
    viewed_pages = load_viewed_pages()
    
    # Only add the current page if it hasn't been logged before
    page_key = f'test_page_{page_number}'
    if page_key not in viewed_pages.get(username, []):
        viewed_pages[username] = viewed_pages.get(username, []) + [page_key]
        save_viewed_pages(viewed_pages)
    
    session['viewed_pages'] = viewed_pages[username]  # Update the session with the latest viewed pages
    session['current_page'] += 1
    return redirect(url_for('test_page', page_number=session['current_page']))

@app.route('/thank_you', methods=['GET'])
def thank_you():
    if 'username' not in session:
        return redirect(url_for('index'))
    username = session['username']
    viewed_pages = load_viewed_pages()
    if 'thank_you' in viewed_pages.get(username, []):
        return render_template('error.html', message="You cannot view this page again.")
    viewed_pages[username] = viewed_pages.get(username, []) + ['thank_you']
    save_viewed_pages(viewed_pages)
    return render_template('thank_you.html')

if __name__ == '__main__':
    app.run(debug=True)
