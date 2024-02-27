from flask import Flask, render_template, request, redirect, url_for, session
from database import *

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://21CS10008:21CS10008@10.5.18.68/21CS10008'
db.init_app(app)


@app.route('/')
def index():
    if 'username' in session:
        session.pop('username')
    return render_template('index.html')

@app.route('/student_signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        roll_no = request.form['roll_number']
        name = request.form['name']
        dept = request.form['department']
        # Check if username already exists
        if not is_user_exists(username):
            create_user_student(username, password, roll_no, name, dept)
            return redirect(url_for('index'))
        else:
            return render_template('student_signup.html', error="Username already exists")
    return render_template('student_signup.html')

@app.route('/participant_signup', methods=['GET', 'POST'])
def participant_signup():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        college = request.form['college_name']
        # Check if username already exists
        if not is_user_exists(username):
            create_user_participant(username, password,  name, college)
            return redirect(url_for('index'))
        else:
            error = "Username already exists"
    college_names = get_college_names()
    return render_template('participant_signup.html', college_names=college_names, error=error)

@app.route('/organizer_signup', methods=['GET', 'POST'])
def organizer_signup():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        # Check if username already exists
        if not is_user_exists(username):
            create_user_organizer(username, password, name)
            return redirect(url_for('index'))
        else:
            error = "Username already exists"

    return render_template('organizer_signup.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        # Check if username and password are correct
        if user and user.password == password:
            session['username'] = username
            return redirect(url_for(f"{user.user_type}_dashboard"))
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

@app.route('/Student_dashboard')
def Student_dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    username = session['username']
    return render_template('student_dashboard.html')

@app.route('/Participant_dashboard')
def Participant_dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    username = session['username']
    return render_template('participant_dashboard.html')

@app.route('/Organizer_dashboard')
def Organizer_dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    events = get_all_events()
    return render_template('organizer_dashboard.html', events=events)

@app.route('/event/<int:event_id>/details')
def event_details(event_id):
    if 'username' not in session:
        return redirect(url_for('index'))
    event = get_event_details(event_id)
    volunteers = get_event_volunteers(event_id)
    return render_template('event_details.html', event=event, volunteers=volunteers)


@app.route('/student_register_events', methods=['GET', 'POST'])
def student_register_events():
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirect to login if not logged in
    
    username = session['username']
    
    if request.method == 'POST':
        participant_events = request.form.getlist('participant')
        volunteer_events = request.form.getlist('volunteer')
        
        for event_id in participant_events:
            register_as_participant(username, event_id)
        for event_id in volunteer_events:
            register_as_volunteer(username, event_id)
        
        return redirect(url_for('Student_dashboard'))  # Redirect to dashboard after registration
    
    # Get events not registered by the student
    events = get_events_not_registered(username)
    
    return render_template('student_register_event.html', events=events)

@app.route('/student_registered_in_events')
def student_registered_in_events():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    # Get the username from the session
    username = session['username']

    # Query the events the user is registered in as a participant
    participant_events = get_participant_events(username)

    # Query the events the user is registered in as a volunteer
    volunteer_events = get_volunteer_events(username)

    return render_template('student_registered_in_events.html', participant_events=participant_events, volunteer_events=volunteer_events)


@app.route('/participant_register_events', methods=['GET', 'POST'])
def participant_register_events():
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirect to login if not logged in
    
    username = session['username']
    
    if request.method == 'POST':
        participant_events = request.form.getlist('participant')
        
        for event_id in participant_events:
            register_as_participant(username, event_id)
        
        return redirect(url_for('Participant_dashboard'))  # Redirect to dashboard after registration
    
    # Get events not registered by the participant
    events = get_events_not_participated(username)
    
    return render_template('participant_register_event.html', events=events)

@app.route('/participant_registered_in_events')
def participant_registered_in_events():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    # Get the username from the session
    username = session['username']

    # Query the events the user is registered in as a participant
    participant_events = get_participant_events(username)

    return render_template('participant_registered_in_events.html', participant_events=participant_events)


if __name__=="__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
