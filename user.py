from flask_login import UserMixin

from db import get_db

from dataclasses import dataclass
from typing import List



@dataclass
class car:
    name: str #Toyota Corola
    capacity: int #How many ppl
    fuel_efficiency: float #m/G? #printf to save in DB cause is text
    
    def __init__(self, name):
        self.name = name

@dataclass
class trip:
    owner: str
    starting_place: str
    destination: str
    stops: List[str]
    total_stops: int
    date: str
    passangers: List[str]
    vehicle: car 
    comments: str
    applications: List[int] #requests to join
    trip_id: int
    
    # make sure to have all details loaded before initiating
    #make user select trip by date before viewing details
    def __init__(self, date, vehicle, starting_location, ending_location, stops, comments): 
        self.date = date
        self.vehicle = vehicle
        self.starting_place = starting_location
        self.destination = ending_location
        self.total_stops = stops
        self.comments = comments
    
    @staticmethod
    def load_vehicle(name):
        db = get_db()
        vrum = db.execute(
            'SELECT * FROM car WHERE name = ?', (name,)
        ).fetchone()
        if not vrum:
            return None
        
        if (not (vrum[0])): print('How do we have a car in a database with no name?!')
        vroom = car(name = vrum[0])
        if (vrum[1]): vroom.capacity = vrum[1] #may not have
        if (vrum[2]): vroom.fuel_efficiency = vrum[2] #may also not have
        return vroom




@dataclass
class User(UserMixin):
    user_id: int
    id_: int
    name: str
    emissions_avoided: int
    email: str
    venmo: str
    upcoming_trip: trip
    my_trips: List[trip]
    loaded: bool
    #add in nickname 
    #add in preferred payment method
    
    def __init__(self, user_id, name, email):
        self.user_id = user_id
        self.id = user_id #needed to login user
        self.name = name
        self.email = email
        self.my_trips = []
        self.loaded = False
        
    @staticmethod
    def get(user_id):
        db = get_db()
        user = db.execute(
            "SELECT * FROM user WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not user:
            return None

        user = User(
            user_id=user[0], name=user[1], email=user[3]
            #where is the user array?
            #It is in schema.sql?
        )
        return user

    @staticmethod
    def create(user_id, name, email): #just creating only need those
        db = get_db()
        db.execute(
            "INSERT INTO user (user_id, name, email) "
            "VALUES (?, ?, ?)",
            (user_id, name, email),
        )
        db.commit()

    @staticmethod
    def save_trip(usr, date, stops, passangers, vehicle, starting_location, ending_location, comments): #temp and humidity are simulated so don't need to be saved
        db = get_db()
        print('got db')
        db.execute(
            'INSERT INTO trips (user_id, starting_place, destination, stops, date, vehicle, comments) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (usr, starting_location, ending_location, stops, date, vehicle, comments),
        )
        #this is gonna be gross but im tired
        
        #TODO:
        #not actually sure if this appends to the same trip actually
        print('inserted')
        if (len(passangers) == 1):
            db.execute(
                'INSERT INTO trips (passanger1) '
                'VALUES (?)',
                (passangers[0])
        )
        if (len(passangers) == 2):
            db.execute(
                'INSERT INTO trips (passanger1, passanger2) '
                'VALUES (?, ?)',
                (passangers[0], passangers[1])
        )
        if (len(passangers) == 3):
            db.execute(
                'INSERT INTO trips (passanger1) '
                'VALUES (?, ?, ?)',
                (passangers[0], passangers[1], passangers[2])
        )
            
        trp = trip(date, vehicle, starting_location, ending_location, stops, comments)
        trp.ower = usr
        db.commit()
        return trp
    
    @staticmethod
    def apply_to_trip(trip_id, pasngr):
        db = get_db()
        trp = db.execute(
            'SELECT * FROM trips WHERE trip_id = ?', (trip_id,)
        ).fetchone()
        if not trp: return False
        #laded trip were applying to
        voyage = {'driver': trp[1], 'drivee': pasngr, 'id': trip_id}
        print(voyage)
        db.execute(
                'INSERT INTO trip_requests (driver, rider, trip) '
                'VALUES (?, ?, ?)',
                (voyage['driver'], pasngr, trip_id)
        )
        db.commit()
        return True
    
    @staticmethod
    def load_invites(tripid):
        db = get_db()
        invites = db.execute(
                'SELECT * FROM trip_requests WHERE trip = ?', (tripid,)
        ).fetchall()
        if not invites: return False
        invite_ct = len(invites)
        return invite_ct
    
    @staticmethod
    def load_trips(user_id):
        db = get_db()
        trps = db.execute(
            'SELECT * FROM trips WHERE user_id = ?', (user_id,)
        ).fetchall() #returns all as list of tuples
        if not trps:
            print('DB did not find sensors')
            return None
        returned_trips : List[trip] = []
        for i in trps:
            trp = trip(
                    date=i[5], vehicle=i[14], starting_location=i[2] , ending_location=i[3], stops=i[4], comments=i[15])
#            print('Found: ',sens, sep=' ')
            trp.owner = user_id
            print(i[0])
            trp.trip_id = i[0]
            returned_trips.append(trp)

        print('User had ' + str(len(returned_trips))+ ' trips')
        return returned_trips #returns because not sure about accessing pvt data on staticmethod

    @staticmethod
    def load_all_trips():
        db = get_db()
        trps = db.execute('SELECT * FROM trips').fetchall()
        if not trps:
            print('DB could not access trips')
            return None
        returned_trips : List[trip] = []
        for i in trps:
            trp = trip(
                    date=i[5], vehicle=i[14], starting_location=i[2] , ending_location=i[3], stops=i[4], comments=i[15])
            trp.owner = i[1]
            trp.trip_id = i[0]
            returned_trips.append(trp)
        return returned_trips
        

