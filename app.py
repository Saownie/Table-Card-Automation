from flask import Flask, render_template, request, send_file, session, redirect, url_for
from datetime import timedelta
import os
import uuid
import sys
import traceback

app = Flask(__name__)

# --- SECURITY & CONFIGURATION ---
# 1. Secret Key: Needed to encrypt your login session
app.secret_key = '8f4b2e19a0d3c4e5f6a7b8c9d0e1f2a3' 

# 2. Login Credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'

# 3. Auto-Logout Timer (5 Minutes)
app.permanent_session_lifetime = timedelta(minutes=1)

# --- FOLDER SETUP ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'temp_uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'temp_generated')
TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'master_templates')

# Ensure temp folders exist so the app doesn't crash
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Template Map (Radio buttons -> Filenames)
TEMPLATE_MAP = {
    'balcony': 'Balcony Cards.docx',
    'phh': 'PHH Cards.docx',
    'crush': 'Crush Cards.docx'
}

# --- INACTIVITY CHECKER ---
# This runs before every single click to check if the user has been idle
@app.before_request
def make_session_permanent():
    session.permanent = True  # Activates the timer
    # The timer is reset to 5 minutes every time the user interacts with the page.
    # If they do nothing for 5 minutes, the session expires.

# --- ROUTES ---

# 1. LOGIN ROUTE
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Verify Credentials
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.clear()          # Clear any old session data
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = "Invalid Credentials. Please try again."
            
    return render_template('login.html', error=error)

# 2. LOGOUT ROUTE
@app.route('/logout')
def logout():
    session.clear() # Wipes the session completely
    return redirect(url_for('login'))

# 3. HOMEPAGE (Protected)
@app.route('/', methods=['GET'])
def index():
    # If not logged in, kick them to the login page
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

# 4. GENERATE ROUTE (Protected + Logic)
@app.route('/generate', methods=['POST'])
def generate():
    # Security Check
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Lazy Import: Loads the script only when needed to prevent startup crashes
    try:
        from card_processor import process_and_generate
    except ImportError as e:
        return f"<h1>Configuration Error</h1><p>Could not load card_processor.py</p><p>Error: {e}</p>", 500

    # Handle File Upload
    if 'csv_file' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['csv_file']
    template_type = request.form.get('template_type')

    if file.filename == '':
        return "No selected file", 400

    if file and template_type in TEMPLATE_MAP:
        # Create unique filenames to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        csv_filename = f"upload_{unique_id}_{file.filename}"
        upload_path = os.path.join(UPLOAD_FOLDER, csv_filename)
        
        file.save(upload_path)

        selected_template_filename = TEMPLATE_MAP[template_type]
        template_path = os.path.join(TEMPLATE_FOLDER, selected_template_filename)
        output_filename = f"{template_type.upper()}_Cards_COMPLETE_{unique_id}.docx"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        try:
            # RUN THE PROCESSOR
            process_and_generate(upload_path, template_path, output_path)
            
            # Send the file to the user
            return send_file(output_path, as_attachment=True, download_name=output_filename)

        except Exception as e:
            # Print error to screen for debugging
            return f"<h1>Processing Failed</h1><pre>{traceback.format_exc()}</pre>", 500
        finally:
            # CLEANUP: Delete the input CSV immediately (GDPR)
            if os.path.exists(upload_path):
                os.remove(upload_path)

    return "Invalid request", 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)