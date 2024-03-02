from flask import Flask, render_template, request, redirect, url_for, session
from database import *

app = Flask(__name__)
app.secret_key = 'secret_key'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://21CS10008:21CS10008@10.5.18.68/21CS10008'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://sujitkumar@localhost/postgres'
db.init_app(app)


@app.route('/')
def index():
    if 'username' in session:
        session.pop('username')
    if 'user_type' in session:
        session.pop('user_type')
    return render_template('index.html')

@app.route('/student_signup', methods=['GET', 'POST'])
def student_signup():
    if 'username' in session:
        return redirect(url_for('index'))
    error = None
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
            error="Username already exists"
    return render_template('student_signup.html', error=error)

@app.route('/participant_signup', methods=['GET', 'POST'])
def participant_signup():
    if 'username' in session:
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        college = request.form['college_name']
        food_id = request.form.get('food', None)
        accommodation_id = request.form.get('accommodation', None)
        
        # Check if username already exists
        if not is_user_exists(username):
            create_user_participant(username, password, name, college, food_id, accommodation_id)
            return redirect(url_for('index'))
        else:
            error = "Username already exists"
    
    college_names = get_college_names()
    food_options = get_food_options()
    accommodation_options = get_accommodation_options()
    return render_template('participant_signup.html', college_names=college_names, food_options=food_options, accommodation_options=accommodation_options, error=error)

@app.route('/organizer_signup', methods=['GET', 'POST'])
def organizer_signup():
    if 'username' in session:
        return redirect(url_for('index'))
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
    if 'username' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        # Check if username and password are correct
        if user and user.check_password(password):
            session['username'] = username
            session['user_type'] = user.user_type
            return redirect(url_for(f"{user.user_type}_dashboard"))
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

@app.route('/Student_dashboard')
def Student_dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    if session['user_type']!='Student':
        return redirect(url_for('index'))

    return render_template('student_dashboard.html')

@app.route('/Participant_dashboard')
def Participant_dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    if session['user_type']!='Participant':
        return redirect(url_for('index'))

    return render_template('participant_dashboard.html')

@app.route('/Organizer_dashboard')
def Organizer_dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    if session['user_type']!='Organizer':
        return redirect(url_for('index'))
    
    username = session['username']
    
    organizer_allowed = is_organizer_allowed(username)

    return render_template('organizer_dashboard.html', allowed = organizer_allowed)

@app.route('/Admin_dashboard')
def Admin_dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    if session['user_type']!='Admin':
        return redirect(url_for('index'))
    
    return render_template('admin_dashboard.html')

@app.route('/organizer_view_events')
def organizer_view_events():
    if 'username' not in session:
        return redirect(url_for('index'))
    if session['user_type']!='Organizer':
        return redirect(url_for('index'))
    
    org_username = session['username']
    org_allowed = is_organizer_allowed(org_username)
    if not org_allowed:
        return redirect(url_for('Organizer_dashboard'))

    events = get_all_events(org_username)
    return render_template('organizer_view_events.html', events=events)

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if 'username' not in session:
        return redirect(url_for('index'))
    if session['user_type']!='Organizer':
        return redirect(url_for('index'))
    
    org_username = session['username']
    org_allowed = is_organizer_allowed(org_username)
    if not org_allowed:
        return redirect(url_for('Organizer_dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        type = request.form['type']
        date = request.form['date']
        organizer_username = session['username']  # Assuming username is stored in session

        create_new_event(name, type, date, organizer_username)
        return redirect(url_for('Organizer_dashboard'))
        
    return render_template('create_event.html')
    

@app.route('/event/<int:event_id>/details')
def event_details(event_id):
    if 'username' not in session:
        return redirect(url_for('index'))
    if session['user_type']!='Organizer':
        return redirect(url_for('index'))
    
    org_username = session['username']
    org_allowed = is_organizer_allowed(org_username)
    if not org_allowed:
        return redirect(url_for('Organizer_dashboard'))
    
    event = get_event_details(event_id)
    volunteers = get_event_volunteers(event_id)
    participants = get_participants_for_event(event_id)
    winner_name = get_name_by_username(event.winner_username)
    return render_template('event_details.html', event=event, winner_name=winner_name, volunteers=volunteers, participants=participants)

@app.route('/submit_winner/<int:event_id>', methods=['GET', 'POST'])
def submit_winner(event_id):
    if 'username' not in session:
        return redirect(url_for('index'))
    if session['user_type']!='Organizer':
        return redirect(url_for('index'))
    
    org_username = session['username']
    org_allowed = is_organizer_allowed(org_username)
    if not org_allowed:
        return redirect(url_for('Organizer_dashboard'))
    
    if request.method=='POST':
        winner_username = request.form['winner']
        update_winner(event_id, winner_username)
        return redirect(url_for('Organizer_dashboard'))


@app.route('/student_register_events', methods=['GET', 'POST'])
def student_register_events():
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirect to login if not logged in
    if session['user_type']!='Student':
        return redirect(url_for('index'))
    
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
        return redirect(url_for('index'))  # Redirect to login if user is not logged in
    if session['user_type']!='Student':
        return redirect(url_for('index'))

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
    if session['user_type']!='Participant':
        return redirect(url_for('index'))
    
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
        return redirect(url_for('index'))  # Redirect to login if user is not logged in
    if session['user_type']!='Participant':
        return redirect(url_for('index'))

    # Get the username from the session
    username = session['username']

    # Query the events the user is registered in as a participant
    participant_events = get_participant_events(username)

    return render_template('participant_registered_in_events.html', participant_events=participant_events)

@app.route('/notifications')
def notifications():
    all_notifications = get_all_notifications()
    # You can now use all_notifications in your template or jsonify it if you're building an API
    return render_template('notifications.html', notifications=all_notifications)

@app.route('/see_winners')
def student_see_winners():
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirect to login if user is not logged in
    if session['user_type']!='Student' and session['user_type']!='Participant':
        return redirect(url_for('index'))
    
    username = session['username']

    events_and_winners = get_events_and_winners(username)

    return render_template('seeWinner.html', events_with_winners=events_and_winners)

@app.route('/allow_organizers')
def allow_organizers():
    if 'username' not in session:
        return redirect(url_for('index'))
    if session['user_type']!='Admin':
        return redirect(url_for('index'))
    
    organizers = get_organizers_to_allow()
    return render_template('allow_organizers.html', organizers=organizers)

@app.route('/update_organizers', methods=['POST'])
def update_organizers():
    if 'username' not in session:
        return redirect(url_for('index'))
    if session['user_type']!='Admin':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        organizers_to_allow = request.form.getlist('organizers[]')
        update_organizers_allowed_status(organizers_to_allow)
        return redirect(url_for('Admin_dashboard'))
    return redirect(url_for('allow_organizers'))

@app.route('/delete_users', methods=['GET', 'POST'])
def delete_users_page():
    if 'username' not in session:
        return redirect(url_for('index'))
    if session['user_type']!='Admin':
        return redirect(url_for('index'))
    
    elif request.method == 'POST':
        users_to_delete = request.form.getlist('users[]')
        delete_users(users_to_delete)
        return redirect(url_for('Admin_dashboard'))
    
    users = get_users_to_delete()
    return render_template('delete_users.html', users=users)

@app.route('/logout')
def logout():
    return redirect(url_for('index'))


if __name__=="__main__":
    with app.app_context():
        db.create_all()
    with app.app_context():
        with db.engine.connect() as connection:
            create_triggers_on_connect(connection.connection, None)
    with app.app_context():
        default_initialization()
    app.run(debug=True)
