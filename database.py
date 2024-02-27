# database.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Users(db.Model):
    username = db.Column(db.String(100), primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(100), nullable=False)

class Student(db.Model):
    user_name = db.Column(db.String(100), db.ForeignKey('users.username'))
    name = db.Column(db.String(100),nullable= False)
    roll_number= db.Column(db.String(100),primary_key=True)
    department= db.Column(db.String(100),nullable=False)

class Participant(db.Model):
    user_name  = db.Column(db.String(100), db.ForeignKey('users.username'), primary_key=True)
    name = db.Column(db.String(100),nullable= False)
    college_name = db.Column(db.String(255), db.ForeignKey('college.name'))

class Organizer(db.Model):
    user_name = db.Column(db.String(100), db.ForeignKey('users.username'), primary_key=True)
    name = db.Column(db.String(100),nullable= False)
    
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False)

class College(db.Model):
    name = db.Column(db.String(255), primary_key=True)
    location = db.Column(db.Text, nullable=False)

class EventParticipant(db.Model):
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    participant_id = db.Column(db.String, db.ForeignKey('users.username'), primary_key=True)

class EventVolunteer(db.Model):
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    volunteer_id = db.Column(db.String, db.ForeignKey('users.username'), primary_key=True)

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

def create_user_participant(username, password, participant_name, college):
    user = Users(username=username, password=password, user_type='Participant')
    db.session.add(user)
    db.session.commit()
    participant = Participant(user_name=username, name=participant_name, college_name = college)
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

def get_all_events():
    return Event.query.all()

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