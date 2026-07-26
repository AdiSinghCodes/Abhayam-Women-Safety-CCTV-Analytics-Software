from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
import subprocess
import os
import csv
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'abhayam_women_safety_key'
app.config['SESSION_TYPE'] = 'filesystem'

# Constants
CREDENTIALS_FILE = "credentials.csv"
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Global variables to track processes
processes = {
    "main_process": None,
    "flask_process": None,
    "geminiLabel_process": None
}

# Helper Functions
def verify_credentials(username, password):
    """Verify credentials."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, mode="r") as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == username and check_password_hash(row[1], password):
                    return True
    return False

def save_credentials(username, password):
    """Save credentials."""
    if not credentials_exist(username):
        with open(CREDENTIALS_FILE, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([username, generate_password_hash(password)])
        return True
    return False

def credentials_exist(username):
    """Check if username exists."""
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, mode="r") as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == username:
                    return True
    return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def start_processing():
    """Start main.py, 1.py, geminiLabel.py for processing."""
    try:
        # Start main.py
        main_process = subprocess.Popen(["python", "main.py"])
        processes["main_process"] = main_process

        one_female_process = subprocess.Popen(["python", "one_female.py"])
        processes["one_female_process"] = one_female_process

        # Start geminiLabel.py
        geminiLabel_process = subprocess.Popen(["python", "geminiLabel.py"])
        processes["geminiLabel_process"] = geminiLabel_process

        return True, "Processing started successfully."
    except Exception as e:
        return False, f"Error starting processing: {e}"

def stop_processing():
    """Stop all running processes."""
    try:
        # Stop main.py process
        if processes["main_process"]:
            processes["main_process"].kill()
            processes["main_process"] = None

        # Stop 1.py process (Flask app)
        if processes["flask_process"]:
            processes["flask_process"].kill()
            processes["flask_process"] = None

        # Stop geminiLabel.py process
        if processes["geminiLabel_process"]:
            processes["geminiLabel_process"].kill()
            processes["geminiLabel_process"] = None

        return True, "All processes stopped successfully."
    except Exception as e:
        return False, f"Error stopping processing: {e}"


def get_plot_base64(fig):
    """Convert matplotlib figure to base64 string for embedding in HTML."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    return img_str

def load_incident_data():
    """Load incident data from CSV file."""
    try:
        # Assuming the CSV file is named violence_log.csv
        df = pd.read_csv('violence_log.csv')
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        return df
    except Exception as e:
        print(f"Error loading incident data: {e}")
        return pd.DataFrame(columns=['Timestamp', 'Action Detected', 'Male Count', 'Female Count', 'Location'])

# Routes
@app.route('/')
def index():
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if verify_credentials(username, password):
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if save_credentials(username, password):
            flash('Signup successful! You can now login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username already exists.', 'error')
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session.get('username', 'User'))

@app.route('/start-processing', methods=['POST'])
@login_required
def start_processing_route():
    success, message = start_processing()
    if success:
        return jsonify({'status': 'success', 'message': message})
    else:
        return jsonify({'status': 'error', 'message': message})

@app.route('/stop-processing', methods=['POST'])
@login_required
def stop_processing_route():
    success, message = stop_processing()
    if success:
        return jsonify({'status': 'success', 'message': message})
    else:
        return jsonify({'status': 'error', 'message': message})


@app.route('/hotspot-analytics')
@login_required
def hotspot_analytics():
    # Check if the CSV file exists
    file_path = "hotspot.csv"
    if os.path.exists(file_path):
        # Load CSV data
        df = pd.read_csv(file_path)
        # Convert DataFrame to HTML table
        table_html = df.to_html(classes='table table-striped table-hover', index=False)
        return render_template('hotspot_analytics.html', table_html=table_html, csv_exists=True)
    else:
        return render_template('hotspot_analytics.html', csv_exists=False)

@app.route('/download-hotspot-csv')
@login_required
def download_hotspot_csv():
    file_path = "hotspot.csv"
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('Hotspot CSV file not found.', 'error')
        return redirect(url_for('hotspot_analytics'))

@app.route('/general-analytics')
@login_required
def general_analytics():
    # Check if CSV files exist
    violence_log_path = "violence_log.csv"
    sos_gestures_path = "sos_gestures.csv"
    
    if not os.path.exists(violence_log_path) or not os.path.exists(sos_gestures_path):
        return render_template('general_analytics.html', data_exists=False)
    
    # Load datasets
    violence_data = pd.read_csv(violence_log_path, parse_dates=['Timestamp'])
    sos_columns = ['Timestamp', 'Location', 'Image_URL']
    sos_data = pd.read_csv(sos_gestures_path, header=None, names=sos_columns, parse_dates=['Timestamp'])

    # Set seaborn style
    sns.set(style="whitegrid")
    
    # Generate plots and convert to base64 for embedding in HTML
    plots = {}
    
    # 1. Incidents Over Time
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    incident_counts = violence_data.groupby(['Timestamp']).size()
    incident_counts.plot(kind='line', ax=ax1)
    plt.xlabel("Time")
    plt.ylabel("Incident Count")
    plt.title("Incidents Over Time")
    plots['incidents_over_time'] = get_plot_base64(fig1)
    plt.close(fig1)
    
    # 2. Location-Based Analysis
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    location_counts = violence_data['Location'].value_counts()
    location_counts.plot(kind='bar', ax=ax2)
    plt.xlabel("Location")
    plt.ylabel("Incident Count")
    plt.title("Incidents Per Location")
    plots['incidents_per_location'] = get_plot_base64(fig2)
    plt.close(fig2)
    
    # 3. Gender Count Per Incident Type
    fig3, ax3 = plt.subplots(figsize=(8, 6))
    gender_incidents = violence_data.groupby(['Action Detected']).agg(
        male_count=('Male Count', 'sum'),
        female_count=('Female Count', 'sum')
    )
    gender_incidents.plot(kind='bar', stacked=True, ax=ax3)
    plt.xlabel("Incident Type")
    plt.ylabel("Count")
    plt.title("Gender Count Per Incident Type")
    plots['gender_count'] = get_plot_base64(fig3)
    plt.close(fig3)
    
    # 4. Hourly Patterns
    fig4, ax4 = plt.subplots(figsize=(10, 6))
    violence_data['Hour'] = violence_data['Timestamp'].dt.hour
    hourly_incidents = violence_data.groupby('Hour').size()
    sns.heatmap(hourly_incidents.values.reshape(1, -1), annot=True, cmap="coolwarm", 
               xticklabels=hourly_incidents.index, ax=ax4)
    plt.title("Hourly Incident Frequency")
    plots['hourly_incidents'] = get_plot_base64(fig4)
    plt.close(fig4)
    
    # 5. SOS Alerts Over Time
    fig5, ax5 = plt.subplots(figsize=(10, 6))
    sos_counts = sos_data.groupby(['Timestamp']).size()
    sos_counts.plot(kind='line', ax=ax5)
    plt.xlabel("Time")
    plt.ylabel("SOS Alert Count")
    plt.title("SOS Alerts Over Time")
    plots['sos_alerts'] = get_plot_base64(fig5)
    plt.close(fig5)
    
    # 6. Location-Based SOS Alerts
    fig6, ax6 = plt.subplots(figsize=(8, 6))
    sos_location_counts = sos_data['Location'].value_counts()
    sos_location_counts.plot(kind='bar', ax=ax6)
    plt.xlabel("Location")
    plt.ylabel("SOS Alert Count")
    plt.title("SOS Alerts Per Location")
    plots['sos_location'] = get_plot_base64(fig6)
    plt.close(fig6)
    
    return render_template('general_analytics.html', plots=plots, data_exists=True)

@app.route('/select-camera')
@login_required
def select_camera():
    return render_template('select_cam.html')

@app.route('/run-region-manager', methods=['POST'])
@login_required
def run_region_manager():
    try:
        # Start the region manager
        region_manager_process = subprocess.Popen(["python", "region_manager.py"])
        
        # Store the process ID in the session (optional)
        session['region_manager_process'] = region_manager_process.pid
        
        return jsonify({'status': 'success', 'message': 'Region Manager is running.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error starting Region Manager: {e}'})
    
def run_region_manager():
    try:
        # Start the region manager
        region_manager_process = subprocess.Popen(["python", "region_manager.py"])
        return jsonify({'status': 'success', 'message': 'Region Manager is running.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error starting Region Manager: {e}'})

@app.route('/about-us')
@login_required
def about_us():
    return render_template('about_us.html')


@app.route('/web-cam')
@login_required
def web_cam():
    try:
        # Start the webcam processing script
        webcam_process = subprocess.Popen(["python", "webcam_processing.py"])
        session['webcam_process'] = webcam_process.pid
        flash('Webcam processing started successfully.', 'success')
    except Exception as e:
        flash(f'Error starting webcam processing: {e}', 'error')
    return redirect(url_for('dashboard'))

@app.route('/api/incident-data')
@login_required
def api_incident_data():
    try:
        # Load the CSV data
        df = pd.read_csv('violence_log.csv')
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        # Get filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        location = request.args.get('location')
        detection_types = request.args.get('detection_type')
        
        # Apply filters
        if start_date:
            df = df[df['Timestamp'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['Timestamp'] <= pd.to_datetime(end_date) + pd.Timedelta(days=1)]
        if location and location != 'All':
            df = df[df['Location'] == location]
        if detection_types:
            detection_types = detection_types.split(',')
            df = df[df['Action Detected'].isin(detection_types)]
        
        # Prepare data for charts
        incidents_by_date = df.groupby(df['Timestamp'].dt.date).size().reset_index()
        incidents_by_date.columns = ['date', 'count']
        incidents_by_date['date'] = incidents_by_date['date'].astype(str)
        
        incidents_by_type = df.groupby('Action Detected').size().reset_index()
        incidents_by_type.columns = ['type', 'count']
        
        incidents_by_location = df.groupby('Location').size().reset_index()
        incidents_by_location.columns = ['location', 'count']
        
        # Hourly distribution
        df['hour'] = df['Timestamp'].dt.hour
        hourly_distribution = df.groupby('hour').size().reset_index()
        hourly_distribution.columns = ['hour', 'count']
        
        # Gender distribution
        gender_data = {
            'male': df['Male Count'].sum(),
            'female': df['Female Count'].sum()
        }
        
        # Recent incidents (last 20)
        recent_incidents = df.sort_values('Timestamp', ascending=False).head(20)
        recent_incidents['Timestamp'] = recent_incidents['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        recent_incidents_list = recent_incidents.to_dict('records')
        
        # Return JSON response
        return jsonify({
            'incidents_by_date': incidents_by_date.to_dict('records'),
            'incidents_by_type': incidents_by_type.to_dict('records'),
            'incidents_by_location': incidents_by_location.to_dict('records'),
            'hourly_distribution': hourly_distribution.to_dict('records'),
            'gender_data': gender_data,
            'recent_incidents': recent_incidents_list,
            'total_incidents': len(df),
            'total_locations': len(df['Location'].unique()),
            'total_males': df['Male Count'].sum(),
            'total_females': df['Female Count'].sum()
        })
    except Exception as e:
        print(f"Error fetching data: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create credentials file if it doesn't exist
    if not os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            # Add a default admin user
            writer.writerow(["admin", generate_password_hash("admin")])
    
    app.run(debug=True)