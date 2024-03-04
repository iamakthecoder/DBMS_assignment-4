from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import null
from sqlalchemy import func, or_, Table, MetaData
import bcrypt

db = SQLAlchemy()

class Users(db.Model):
    username = db.Column(db.String(100), primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(100), nullable=False)

    def set_password(self, pswd):
        hashed_password = bcrypt.hashpw(pswd.encode('utf-8'), bcrypt.gensalt())
        self.password = hashed_password.decode('utf-8')

    def check_password(self, pswd):
        return bcrypt.checkpw(pswd.encode('utf-8'), self.password.encode('utf-8'))

class Student(db.Model):
    user_name = db.Column(db.String(100), db.ForeignKey('users.username', ondelete='CASCADE'), primary_key=True)
    roll_number = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)

class Participant(db.Model):
    user_name  = db.Column(db.String(100), db.ForeignKey('users.username', ondelete='CASCADE'), primary_key=True)
    # participant_id = db.Column(db.Integer, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    college_name = db.Column(db.String(255), db.ForeignKey('college.name', ondelete='CASCADE'))
    food_id = db.Column(db.Integer, db.ForeignKey('food.food_id', ondelete='SET NULL'), nullable=True)
    accommodation_id = db.Column(db.Integer, db.ForeignKey('accommodation.accommodation_id', ondelete='SET NULL'), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)

class Organizer(db.Model):
    user_name = db.Column(db.String(100), db.ForeignKey('users.username', ondelete='CASCADE'), primary_key=True)
    # organizer_id = db.Column(db.Integer, autoincrement=True, nullable=False, unique=True)
    name = db.Column(db.String(100),nullable= False)
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    

class Venue(db.Model):
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    name=db.Column(db.String(255),nullable=False)
    capacity=db.Column(db.Integer,nullable=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)
    prize =db.Column(db.Integer,nullable=False)
    venueid =db.Column(db.Integer,db.ForeignKey('venue.id',ondelete='CASCADE'),nullable=False)
    organizer_username = db.Column(db.String(100), db.ForeignKey('organizer.user_name', ondelete='CASCADE'), nullable=False)
    winner_username = db.Column(db.String(100), db.ForeignKey('users.username', ondelete='SET NULL'), nullable=True)

class College(db.Model):
    name = db.Column(db.String(255), primary_key=True)
    location = db.Column(db.Text, nullable=False)

class EventParticipant(db.Model):
    event_id = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'), primary_key=True)
    participant_id = db.Column(db.String(100), db.ForeignKey('users.username', ondelete='CASCADE'), primary_key=True)

class EventVolunteer(db.Model):
    event_id = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'), primary_key=True)
    volunteer_id = db.Column(db.String(100), db.ForeignKey('student.user_name', ondelete='CASCADE'), primary_key=True)

class Food(db.Model):
    food_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    food_desc = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)

class Accommodation(db.Model):
    accommodation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    price_per_day = db.Column(db.Float, nullable=True)
    capacity = db.Column(db.Integer, nullable=True)
    current_participants = db.Column(db.Integer, default=0, nullable=True)

class Notifications(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    notification_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), nullable=False)

class OrganizersAllowed(db.Model):
    user_name = db.Column(db.String(100), db.ForeignKey('users.username', ondelete='CASCADE'), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    allowed = db.Column(db.Boolean, nullable=False, default=False)

#views
username_name_view = None
event_participants_view = None
events_with_winners_view = None

# Define the SQL command for the trigger function
create_func_winner_update = """
CREATE OR REPLACE FUNCTION winner_updated_func()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO notifications (notification_text, timestamp)
    VALUES ('Winner is updated for the event ' || (SELECT name FROM event WHERE id = NEW.id), CURRENT_TIMESTAMP);
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

create_func_insert_into_organizer = """
CREATE OR REPLACE FUNCTION insert_into_organizer()
RETURNS TRIGGER AS
$$
BEGIN
    IF NEW.allowed = TRUE THEN
        INSERT INTO Organizer (user_name, name, phone_number, email)
        VALUES (NEW.user_name, NEW.name, NEW.phone_number, NEW.email);
    END IF;
    RETURN NEW;
END;
$$
LANGUAGE plpgsql;
"""

create_trigger_insert_into_organizer = """
CREATE TRIGGER insert_into_organizer_trigger
AFTER UPDATE OF allowed ON organizers_allowed
FOR EACH ROW
EXECUTE FUNCTION insert_into_organizer();
"""

create_func_create_event_notification = """
CREATE OR REPLACE FUNCTION create_event_notification()
RETURNS TRIGGER AS
$$
BEGIN
    INSERT INTO Notifications (notification_text, timestamp)
    VALUES (CONCAT('New event "', NEW.name, '" has been created and is now available.'), CURRENT_TIMESTAMP);
    RETURN NEW;
END;
$$
LANGUAGE plpgsql;
"""

create_trigger_event_insert_notification = """
CREATE TRIGGER event_insert_notification_trigger
AFTER INSERT ON Event
FOR EACH ROW
EXECUTE FUNCTION create_event_notification();
"""

create_func_update_current_participants = """
CREATE OR REPLACE FUNCTION update_current_participants()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.accommodation_id IS NOT NULL THEN
        UPDATE accommodation
        SET current_participants = current_participants + 1
        WHERE accommodation_id = NEW.accommodation_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

create_trigger_update_current_participants = """
CREATE TRIGGER update_current_participants_trigger
AFTER INSERT ON participant
FOR EACH ROW
EXECUTE FUNCTION update_current_participants();
"""

create_func_decrement_current_participants = """
CREATE OR REPLACE FUNCTION decrement_current_participants()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.accommodation_id IS NOT NULL THEN
        UPDATE accommodation
        SET current_participants = current_participants - 1
        WHERE accommodation_id = OLD.accommodation_id;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;
"""

create_trigger_decrement_current_participants = """
CREATE TRIGGER decrement_current_participants_trigger
AFTER DELETE ON participant
FOR EACH ROW
EXECUTE FUNCTION decrement_current_participants();
"""

create_view_username_name = """
CREATE VIEW username_name_view AS
SELECT Users.username AS username,
       COALESCE(Student.name, Participant.name, Organizer.name, Organizers_allowed.name) AS name
FROM Users
LEFT JOIN Student ON Student.user_name = Users.username
LEFT JOIN Participant ON Participant.user_name = Users.username
LEFT JOIN Organizer ON Organizer.user_name = Users.username
LEFT JOIN Organizers_allowed ON Organizers_allowed.user_name = Users.username;
"""

create_view_event_participants = """
CREATE VIEW event_participants_view AS
SELECT Users.username,
       Event_participant.event_id,
       COALESCE(Student.name, Participant.name) AS participant_name
FROM Users
JOIN Event_participant ON Event_participant.participant_id = Users.username
LEFT JOIN Student ON Student.user_name = Users.username
LEFT JOIN Participant ON Participant.user_name = Users.username;
"""

create_view_events_with_winners = """
CREATE VIEW events_with_winners_view AS
SELECT Event.name AS event_name,
       Event.winner_username AS winner_username,
       COALESCE(Student.name, Participant.name) AS winner_name,
       Event_participant.participant_id as participant_id
FROM Event
JOIN Event_participant ON Event.id = Event_participant.event_id
LEFT JOIN Student ON Student.user_name = Event.winner_username
LEFT JOIN Participant ON Participant.user_name = Event.winner_username;
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

    #check if function already exist
    cursor.execute("SELECT proname FROM pg_proc WHERE proname = 'insert_into_organizer'")
    func_exists = cursor.fetchone() is not None
    if not func_exists:
        cursor.execute(create_func_insert_into_organizer)
        dbapi_connection.commit()
    
    # Check if trigger already exist
    cursor.execute("SELECT * FROM pg_trigger WHERE tgname = 'insert_into_organizer_trigger'")
    trigger_exists = cursor.fetchone() is not None 
    if not trigger_exists:
        cursor.execute(create_trigger_insert_into_organizer)
        dbapi_connection.commit()

    #check if function already exist
    cursor.execute("SELECT proname FROM pg_proc WHERE proname = 'create_event_notification'")
    func_exists = cursor.fetchone() is not None
    if not func_exists:
        cursor.execute(create_func_create_event_notification)
        dbapi_connection.commit()
    
    # Check if trigger already exist
    cursor.execute("SELECT * FROM pg_trigger WHERE tgname = 'event_insert_notification_trigger'")
    trigger_exists = cursor.fetchone() is not None 
    if not trigger_exists:
        cursor.execute(create_trigger_event_insert_notification)
        dbapi_connection.commit()

    #check if function already exist
    cursor.execute("SELECT proname FROM pg_proc WHERE proname = 'update_current_participants'")
    func_exists = cursor.fetchone() is not None
    if not func_exists:
        cursor.execute(create_func_update_current_participants)
        dbapi_connection.commit()
    
    # Check if trigger already exist
    cursor.execute("SELECT * FROM pg_trigger WHERE tgname = 'update_current_participants_trigger'")
    trigger_exists = cursor.fetchone() is not None 
    if not trigger_exists:
        cursor.execute(create_trigger_update_current_participants)
        dbapi_connection.commit()

    #check if function already exist
    cursor.execute("SELECT proname FROM pg_proc WHERE proname = 'decrement_current_participants'")
    func_exists = cursor.fetchone() is not None
    if not func_exists:
        cursor.execute(create_func_decrement_current_participants)
        dbapi_connection.commit()
    
    # Check if trigger already exist
    cursor.execute("SELECT * FROM pg_trigger WHERE tgname = 'decrement_current_participants_trigger'")
    trigger_exists = cursor.fetchone() is not None 
    if not trigger_exists:
        cursor.execute(create_trigger_decrement_current_participants)
        dbapi_connection.commit()
    
    cursor.close()

def create_views_on_connect(dbapi_connection, connection_record):
    global username_name_view
    global event_participants_view
    global events_with_winners_view
    cursor = dbapi_connection.cursor()

    metadata = MetaData()

    view_exists = db.engine.dialect.has_table(db.engine.connect(), 'username_name_view')
    # If the view doesn't exist, create it
    if not view_exists:
        cursor.execute(create_view_username_name)
        dbapi_connection.commit()
    username_name_view = Table(
        'username_name_view',
        metadata,
        # autoload=True,  # Corrected parameter name
        autoload_with=db.engine
    )

    view_exists = db.engine.dialect.has_table(db.engine.connect(), 'event_participants_view')
    if not view_exists:
        cursor.execute(create_view_event_participants)
        dbapi_connection.commit()
    event_participants_view = Table(
        'event_participants_view',
        metadata,
        # autoload=True,  # Corrected parameter name
        autoload_with=db.engine
    )

    view_exists = db.engine.dialect.has_table(db.engine.connect(), 'events_with_winners_view')
    if not view_exists:
        cursor.execute(create_view_events_with_winners)
        dbapi_connection.commit()
    events_with_winners_view = Table(
        'events_with_winners_view',
        metadata,
        # autoload=True,  # Corrected parameter name
        autoload_with=db.engine
    )

    cursor.close()

def is_user_exists(username):
    return Users.query.filter_by(username=username).first() is not None

def get_user(username):
    return Users.query.filter_by(username=username).first()

def create_user_student(username, password, roll_no, stud_name, dept, phone, email):
    user = Users(username=username, user_type='Student')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    stud = Student(user_name = username, roll_number=roll_no, name=stud_name, department = dept, phone_number = phone, email=email)
    db.session.add(stud)
    db.session.commit()

def create_user_participant(username, password, participant_name, college, phone, email, food_id, accommodation_id):
    user = Users(username=username, user_type='Participant')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    participant = Participant(
        user_name=username,
        name=participant_name,
        college_name=college,
        phone_number = phone,
        email = email
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

def create_user_organizer(username, password, organizer_name, phone, email):
    user = Users(username=username, user_type = 'Organizer')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    organizer = OrganizersAllowed(user_name=username, name=organizer_name, phone_number=phone, email=email, allowed=False)
    db.session.add(organizer)
    db.session.commit()

def get_events_not_registered(username):
    # Query events not registered by the student
    events_with_venue = db.session.query(Event, Venue.name)\
    .join(Venue, Venue.id == Event.venueid)\
    .filter(Event.id.notin_(db.session.query(EventParticipant.event_id).filter_by(participant_id=username)),
            Event.id.notin_(db.session.query(EventVolunteer.event_id).filter_by(volunteer_id=username)))\
    .all()
 
    events_data = []

    for event, venue_name in events_with_venue:
        event_data = {
            'id': event.id,
            'name': event.name,
            'type': event.type,
            'description': event.description,
            'date': event.date,
            'prize': event.prize,
            'venue': venue_name  # Add venue name as a separate key
        }
        events_data.append(event_data)
    return events_data

def get_events_not_participated(username):
    # events = Event.query.filter(Event.id.notin_(db.session.query(EventParticipant.event_id).filter_by(participant_id=username))).all()
    # return events
    events_with_venue = db.session.query(Event, Venue.name)\
        .join(Venue, Venue.id == Event.venueid)\
        .filter(Event.id.notin_(db.session.query(EventParticipant.event_id).filter_by(participant_id=username)))\
        .all()
    
    events_data = []

    for event, venue_name in events_with_venue:
        event_data = {
            'id': event.id,
            'name': event.name,
            'type': event.type,
            'description': event.description,
            'date': event.date,
            'prize': event.prize,
            'venue': venue_name  # Add venue name as a separate key
        }
        events_data.append(event_data)
    return events_data

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

    participant_events = db.session.query(EventParticipant.participant_id, Event, Venue.name).\
        join(Event, Event.id == EventParticipant.event_id).\
        join(Venue, Venue.id == Event.venueid).\
        filter(EventParticipant.participant_id == username).all()
    
    # participant_events = Event.query.join(EventParticipant).filter(EventParticipant.participant_id == username).all()
    participant_events_data = []

    for participant, event, venue_name in participant_events:
        event_data = {
            'id': event.id,
            'name': event.name,
            'type': event.type,
            'description': event.description,
            'date': event.date,
            'prize': event.prize,
            'venue': venue_name  # Add venue name as a separate key
        }
        participant_events_data.append(event_data)
    return participant_events_data

def get_volunteer_events(username):
    """
    Get the events the user is registered in as a volunteer.
    """
    volunteer_events = db.session.query(EventVolunteer.volunteer_id, Event, Venue.name).\
        join(Event, Event.id == EventVolunteer.event_id).\
        join(Venue, Venue.id == Event.venueid).\
        filter(EventVolunteer.volunteer_id == username).all()
    
    volunteer_events_data = []

    for volunteer, event, venue_name in volunteer_events:
        event_data = {
            'id': event.id,
            'name': event.name,
            'type': event.type,
            'description': event.description,
            'date': event.date,
            'prize': event.prize,
            'venue': venue_name  # Add venue name as a separate key
        }
        volunteer_events_data.append(event_data)
    return volunteer_events_data

def get_college_names():
    # Query all colleges and retrieve their names
    college_names = College.query.with_entities(College.name).all()
    # Extract names from the result
    college_names = [name[0] for name in college_names]
    return college_names

def get_all_events(username):
    # return Event.query.filter_by(organizer_username=username).all()
    events = db.session.query(Event, Venue.name).\
        join(Venue, Venue.id == Event.venueid).\
        filter(Event.organizer_username==username).all()
    
    # participant_events = Event.query.join(EventParticipant).filter(EventParticipant.participant_id == username).all()
    events_data = []

    for event, venue_name in events:
        event_data = {
            'id': event.id,
            'name': event.name,
            'type': event.type,
            'description': event.description,
            'date': event.date,
            'prize': event.prize,
            'venue': venue_name  # Add venue name as a separate key
        }
        events_data.append(event_data)
    return events_data


def get_all_events2():
    # return Event.query.all()
    events = db.session.query(Event, Venue.name).\
        join(Venue, Venue.id == Event.venueid).\
        all()
    
    # participant_events = Event.query.join(EventParticipant).filter(EventParticipant.participant_id == username).all()
    events_data = []

    for event, venue_name in events:
        event_data = {
            'id': event.id,
            'name': event.name,
            'type': event.type,
            'description': event.description,
            'date': event.date,
            'prize': event.prize,
            'venue': venue_name  # Add venue name as a separate key
        }
        events_data.append(event_data)
    return events_data

# def get_event_details(event_id):
#     return Event.query.get(event_id)

def get_event_volunteers(event_id):
    # Joining EventVolunteer and Student tables
    query = db.session.query(EventVolunteer, Student).join(Student, EventVolunteer.volunteer_id == Student.user_name).filter(EventVolunteer.event_id == event_id)
    
    # Extracting required information
    volunteers = []
    for event_volunteer, student in query:
        volunteers.append({
            'name': student.name,
            'roll_number': student.roll_number,
            'phone_number': student.phone_number,
            'email':student.email 
        })
    
    return volunteers

def get_food_options():
    # Assuming Food is your SQLAlchemy model for the food table
    return Food.query.all()

def get_accommodation_options():
    # Assuming Accommodation is your SQLAlchemy model for the accommodation table
    return Accommodation.query.filter(or_(Accommodation.current_participants < Accommodation.capacity,
                                          Accommodation.capacity.is_(None))).all()

def get_organizer(username):
    return Organizer.query.filter_by(user_name=username).first()

def create_new_event(name, type, date, organizer_username,venueid,prize,description):
    event = Event(name=name, type=type, date=date, organizer_username=organizer_username,venueid=venueid,prize=prize,description=description)
    db.session.add(event)
    db.session.commit()

def get_participants_for_event(event_id):
    participants = db.session.query(event_participants_view.c.username, event_participants_view.c.participant_name).\
        filter(event_participants_view.c.event_id == event_id).all()
    
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

def get_events_and_winners(username):
    # Query events and winners for the given participant username
    
    events_with_winners = db.session.query(events_with_winners_view.c.event_name, 
                                            events_with_winners_view.c.winner_username, 
                                            events_with_winners_view.c.winner_name).\
        filter(events_with_winners_view.c.participant_id == username).all()
    
    return events_with_winners


def is_organizer_allowed(username):
    # Query the OrganizersAllowed table to check if the organizer is allowed
    organizer = OrganizersAllowed.query.filter_by(user_name=username).first()
    if organizer:
        return organizer.allowed
    else:
        # If the organizer is not found, return False
        return False
    
def get_organizers_to_allow():
    return OrganizersAllowed.query.filter_by(allowed=False).all()

def update_organizers_allowed_status(organizers_to_allow):
    for username in organizers_to_allow:
        organizer = OrganizersAllowed.query.filter_by(user_name=username).first()
        if organizer:
            organizer.allowed = True
            db.session.commit()

def get_users_to_delete():
    users_list = db.session.query(Users.username, Users.user_type, func.coalesce(Student.name, Participant.name, Organizer.name, OrganizersAllowed.name)).\
        outerjoin(Student, Student.user_name == Users.username).\
        outerjoin(Participant, Participant.user_name == Users.username).\
        outerjoin(Organizer, Organizer.user_name == Users.username).\
        outerjoin(OrganizersAllowed, OrganizersAllowed.user_name == Users.username).\
        filter(Users.user_type != 'Admin').all()
    return users_list

def delete_users(users_to_delete):
    for username in users_to_delete:
        user = Users.query.filter_by(username=username).first()
        if user:
            db.session.delete(user)
            db.session.commit()

def default_initialization():
    # Check if there is an admin user
    admin_user = Users.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = Users(username='admin', user_type='Admin')
        admin_user.set_password('123')
        db.session.add(admin_user)

    # Check if there are any entries in the Food table
    if not Food.query.first():
        vegetarian_food = Food(food_desc='Vegetarian', price=70)
        non_vegetarian_food = Food(food_desc='Non-vegetarian', price=100)
        db.session.add(vegetarian_food)
        db.session.add(non_vegetarian_food)

    # Check if there are any entries in the Accommodation table
    if not Accommodation.query.first():
        tgh_accommodation = Accommodation(name='TGH', price_per_day=1000, capacity=400)
        vgh_accommodation = Accommodation(name='VGH', price_per_day=800, capacity=200)
        db.session.add(tgh_accommodation)
        db.session.add(vgh_accommodation)

    #entries for colleges
    college_data = [
        ('IITB', 'Mumbai'),
        ('IITD', 'Delhi'),
        ('IITM', 'Chennai'),
        ('NITW', 'Warangal'),
        ('BITS', 'Pilani')
    ]
    
    for name, location in college_data:
        college = College.query.filter_by(name=name).first()
        if not college:
            college = College(name=name, location=location)
            db.session.add(college)

    venue_data = [
        ('Online', None),
        ('Kalidas',400),
        ('TOAT',3000),
        ('MG Ground',10000),
        ('Nehru Museum',3000)
    ]

    for vname,capacity in venue_data:
        venue  =Venue.query.filter_by(name=vname).first()
        if not venue:
            venue=Venue(name=vname,capacity=capacity)
            db.session.add(venue)

    db.session.commit()

def get_venue():
    return Venue.query.all()
def get_venue_from_id(venueid):
    return Venue.query.get(venueid)
def get_all_participants():
    """
    Get the name and username of all participants.
    """
    # Query the Participant table to fetch all participants
    participants_info = db.session.query(Users.username, Participant.name).\
        join(Participant, Users.username == Participant.user_name).all()
    
    return participants_info

def get_organizers():
    # Query the database to retrieve the name and username of all organizers
    organizers = Organizer.query.with_entities(Organizer.name, Organizer.user_name).all()
    return organizers

def get_students():
    """
    Get the username and name of all students.
    Returns:
        List of tuples containing (username, name).
    """
    students = db.session.query(Student.user_name, Student.name).all()
    return students


# def get_participant_events(username):
#     """
#     Get the events the user is registered in as a participant.
#     """
#     participant_events = Event.query.join(EventParticipant).filter(EventParticipant.participant_id == username).all()
#     return participant_events

# def get_volunteer_events(username):
#     """
#     Get the events the user is registered in as a volunteer.
#     """
#     volunteer_events = Event.query.join(EventVolunteer).filter(EventVolunteer.volunteer_id == username).all()
#     return volunteer_events

def get_student_details(username):
    # Query the Student table to get student details
    student = Student.query.filter_by(user_name=username).first()

    if student:
        # Fetch additional details from the Users table
        user = Users.query.filter_by(username=username).first()
        if user:
            name = student.name
            roll_number = student.roll_number
            department = student.department
            phone = student.phone_number
            email = student.email
            events_participated = get_participant_events(username)
            events_volunteered = get_volunteer_events(username)
            
            # Return a dictionary containing all the details
            return {
                'name': name,
                'username': username,
                'roll_number': roll_number,
                'department': department,
                'phone': phone,
                'email': email,
                'events_participated': events_participated,
                'events_volunteered': events_volunteered
            }
    
    return None

def get_participant_details(username):
    # Query the Participant table to get participant details
    participant = Participant.query.filter_by(user_name=username).first()

    if participant:
        # Fetch additional details from the Users table
        user = Users.query.filter_by(username=username).first()
        if user:
            name = participant.name
            college = participant.college_name
            phone = participant.phone_number
            email = participant.email
            
            # Fetch events participated by the participant
            events_participated = get_participant_events(username)
            
            # Return a dictionary containing all the details
            return {
                'username': username,
                'name': name,
                'college': college,
                'phone': phone,
                'email': email,
                'events_participated': events_participated
            }
    
    return None

def get_organizer_details(username):
    # Query the Organizer table to get organizer details
    organizer = Organizer.query.filter_by(user_name=username).first()

    if organizer:
        # Fetch additional details from the Users table
        user = Users.query.filter_by(username=username).first()
        if user:
            name = organizer.name
            phone = organizer.phone_number
            email = organizer.email
            
            # Get the events organized by the organizer
            events_organized = Event.query.filter_by(organizer_username=username).all()

            # Return a dictionary containing all the details
            return {
                'name': name,
                'username': username,
                'phone': phone,
                'email': email,
                'events_organized': events_organized
            }
    
    return None



def get_event_details(event_id):
    """
    Fetches event details based on the event ID.
    
    Parameters:
        event_id (int): The ID of the event.
        
    Returns:
        dict: A dictionary containing event details.
    """
    # Query the Event table to get event details
    event = Event.query.filter_by(id=event_id).first()

    if event:
        # Fetch additional details from the Venue table
        venue = Venue.query.filter_by(id=event.venueid).first()

        # Return a dictionary containing all the details
        return {
            'id': event.id,
            'name': event.name,
            'type': event.type,
            'date': event.date,
            'prize': event.prize,
            'venue': venue.name if venue else None,
            'description' : event.description,
            'organizer_username': event.organizer_username,
            'winner_username': event.winner_username,
            'organizer_name': get_name(event.organizer_username)
        }
    
    return None

def check_venue_date(venueid, date):
    venue = Venue.query.get(venueid)
    if venue.name.lower() == 'online':
        return True
    else:
        event = Event.query.filter_by(venueid=venueid, date=date).first()
        if event:
            return False
        else:
            return True
        
def get_name(username):
    result = db.session.query(username_name_view.c.name).filter(username_name_view.c.username == username).first()
    if result:
        name = result[0]
        return name
    else:
        return None


