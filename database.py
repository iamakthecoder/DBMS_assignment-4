# database.py

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import null
from sqlalchemy import func

db = SQLAlchemy()

class Users(db.Model):
    username = db.Column(db.String(100), primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(100), nullable=False)

class Student(db.Model):
    user_name = db.Column(db.String(100), db.ForeignKey('users.username', ondelete='CASCADE'), primary_key=True)
    roll_number= db.Column(db.String(100),primary_key=True)
    name = db.Column(db.String(100),nullable= False)
    department= db.Column(db.String(100),nullable=False)

class Participant(db.Model):
    user_name  = db.Column(db.String(100), db.ForeignKey('users.username', ondelete='CASCADE'), primary_key=True)
    participant_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    college_name = db.Column(db.String(255), db.ForeignKey('college.name', ondelete='CASCADE'))
    food_id = db.Column(db.Integer, db.ForeignKey('food.food_id', ondelete='SET NULL'), nullable=True)
    accommodation_id = db.Column(db.Integer, db.ForeignKey('accommodation.accommodation_id', ondelete='SET NULL'), nullable=True)

class Organizer(db.Model):
    user_name = db.Column(db.String(100), db.ForeignKey('users.username', ondelete='CASCADE'), primary_key=True)
    organizer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100),nullable= False)
    
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False)
    organizer_username = db.Column(db.String(100), db.ForeignKey('users.username', ondelete='CASCADE'), nullable=False)
    winner_username = db.Column(db.String(100), db.ForeignKey('users.username', ondelete='SET NULL'), nullable=True)

class College(db.Model):
    name = db.Column(db.String(255), primary_key=True)
    location = db.Column(db.Text, nullable=False)

class EventParticipant(db.Model):
    event_id = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'), primary_key=True)
    participant_id = db.Column(db.String(100), db.ForeignKey('users.username', ondelete='CASCADE'), primary_key=True)

class EventVolunteer(db.Model):
    event_id = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'), primary_key=True)
    volunteer_id = db.Column(db.String(100), db.ForeignKey('users.username', ondelete='CASCADE'), primary_key=True)

class Food(db.Model):
    food_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    food_desc = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)

class Accommodation(db.Model):
    accommodation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    price_per_day = db.Column(db.Float, nullable=False)

class Notifications(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    notification_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), nullable=False)

# Define the SQL command for the trigger function
create_func_winner_update = """
CREATE OR REPLACE FUNCTION winner_updated_func()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO notifications (notification_text, timestamp)
    VALUES ('Winner is updated for the ' || (SELECT name FROM event WHERE id = NEW.id), CURRENT_TIMESTAMP);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

# Define the SQL command for creating the trigger for winner update
create_trigger_winner_update = """
CREATE TRIGGER winner_updated_trigger
AFTER UPDATE OF winner_username ON event
FOR EACH ROW
WHEN (OLD.winner_username IS DISTINCT FROM NEW.winner_username)
EXECUTE FUNCTION winner_updated_func();
"""

def create_triggers_on_connect(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()

    #check if function already exist
    cursor.execute("SELECT proname FROM pg_proc WHERE proname = 'winner_updated_func'")
    func_exists = cursor.fetchone() is not None
    if not func_exists:
        cursor.execute(create_func_winner_update)
        dbapi_connection.commit()
    
    # Check if trigger already exist
    cursor.execute("SELECT * FROM pg_trigger WHERE tgname = 'winner_updated_trigger'")
    trigger_exists = cursor.fetchone() is not None 
    if not trigger_exists:
        cursor.execute(create_trigger_winner_update)
        dbapi_connection.commit()
    
    cursor.close()

def is_user_exists(username):
    return Users.query.filter_by(username=username).first() is not None

def get_user(username):
    return Users.query.filter_by(username=username).first()

def create_user_student(username, password, roll_no, stud_name, dept):
    user = Users(username=username, password=password, user_type='Student')
    db.session.add(user)
    db.session.commit()
    stud = Student(user_name = username, roll_number=roll_no, name=stud_name, department = dept)
    db.session.add(stud)
    db.session.commit()

def create_user_participant(username, password, participant_name, college, food_id, accommodation_id):
    user = Users(username=username, password=password, user_type='Participant')
    db.session.add(user)
    db.session.commit()
    participant = Participant(
        user_name=username,
        name=participant_name,
        college_name=college
    )
    if (food_id is not None) and (food_id!=""):
        participant.food_id=food_id
    else:
        participant.food_id=null()
    if (accommodation_id is not None) and (accommodation_id!=""):
        participant.accommodation_id=accommodation_id
    else:
        participant.accommodation_id=null()
    db.session.add(participant)
    db.session.commit()

def create_user_organizer(username, password, organizer_name):
    user = Users(username=username, password=password, user_type = 'Organizer')
    db.session.add(user)
    db.session.commit()
    organizer = Organizer(user_name=username, name=organizer_name)
    db.session.add(organizer)
    db.session.commit()

def get_events_not_registered(username):
    # Query events not registered by the student
    events = Event.query.filter(Event.id.notin_(db.session.query(EventParticipant.event_id).filter_by(participant_id=username)),
                                Event.id.notin_(db.session.query(EventVolunteer.event_id).filter_by(volunteer_id=username))).all()
    return events

def get_events_not_participated(username):
    events = Event.query.filter(Event.id.notin_(db.session.query(EventParticipant.event_id).filter_by(participant_id=username))).all()
    return events

def register_as_participant(username, event_id):
    # Register the student as a participant for the event
    event_participant = EventParticipant(event_id=event_id, participant_id=username)
    db.session.add(event_participant)
    db.session.commit()

def register_as_volunteer(username, event_id):
    # Register the student as a volunteer for the event
    event_volunteer = EventVolunteer(event_id=event_id, volunteer_id=username)
    db.session.add(event_volunteer)
    db.session.commit()

def get_participant_events(username):
    """
    Get the events the user is registered in as a participant.
    """
    participant_events = Event.query.join(EventParticipant).filter(EventParticipant.participant_id == username).all()
    return participant_events

def get_volunteer_events(username):
    """
    Get the events the user is registered in as a volunteer.
    """
    volunteer_events = Event.query.join(EventVolunteer).filter(EventVolunteer.volunteer_id == username).all()
    return volunteer_events

def get_college_names():
    # Query all colleges and retrieve their names
    college_names = College.query.with_entities(College.name).all()
    # Extract names from the result
    college_names = [name[0] for name in college_names]
    return college_names

def get_all_events(username):
    return Event.query.filter_by(organizer_username=username).all()

def get_event_details(event_id):
    return Event.query.get(event_id)

def get_event_volunteers(event_id):
    # Joining EventVolunteer and Student tables
    query = db.session.query(EventVolunteer, Student).join(Student, EventVolunteer.volunteer_id == Student.user_name).filter(EventVolunteer.event_id == event_id)
    
    # Extracting required information
    volunteers = []
    for event_volunteer, student in query:
        volunteers.append({
            'name': student.name,
            'roll_number': student.roll_number
        })
    
    return volunteers

def get_food_options():
    # Assuming Food is your SQLAlchemy model for the food table
    return Food.query.all()

def get_accommodation_options():
    # Assuming Accommodation is your SQLAlchemy model for the accommodation table
    return Accommodation.query.all()

def get_organizer(username):
    return Organizer.query.filter_by(user_name=username).first()

def create_new_event(name, type, date, organizer_username):
    event = Event(name=name, type=type, date=date, organizer_username=organizer_username)
    db.session.add(event)
    db.session.commit()

def get_participants_for_event(event_id):
    participants = db.session.query(Users.username, func.coalesce(Student.name, Participant.name)).\
        join(EventParticipant, EventParticipant.participant_id == Users.username).\
        outerjoin(Student, Student.user_name == Users.username).\
        outerjoin(Participant, Participant.user_name == Users.username).\
        filter(EventParticipant.event_id == event_id).all()
    
    return participants

def update_winner(event_id, winner_username):
    # Fetch the event object
    event = Event.query.get(event_id)
    
    # Check if the event exists
    if event:
        # Update the winner_username
        event.winner_username = winner_username
        
        # Commit the changes to the database
        db.session.commit()

def get_name_by_username(username):
    # Check if the username belongs to a Student
    student = Student.query.filter_by(user_name=username).first()
    if student:
        return student.name

    # Check if the username belongs to a Participant
    participant = Participant.query.filter_by(user_name=username).first()
    if participant:
        return participant.name

    return None

def get_all_notifications():
    # Query all notifications and order them by timestamp in descending order
    notifications = Notifications.query.order_by(Notifications.timestamp.desc()).all()
    return notifications