# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 14:21:53 2019

@author: Felipe Dale Figeman

"""

#example from https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world
import profile
import sqlite3
import json
import os #for supressing https warnings
import urllib.request
from werkzeug.utils import secure_filename

from flask import Flask, request, redirect, url_for, render_template, session, flash
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

from oauthlib.oauth2 import WebApplicationClient
import requests

from typing import List
from db import init_db_command
from user import User, trip

#https://stackoverflow.com/questions/22947905/flask-example-with-post
app = Flask(__name__)
UPLOAD_FOLDER = 'Static/uploads/'
app.secret_key = 'super-duper-secret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
set_up = False #if server has been initalized

yall : List[User] = []
all_trips : List[trip] = []
conn=sqlite3.connect('BUcleantech.db',check_same_thread=False)
curs=conn.cursor()
curs.execute("""
CREATE TABLE IF NOT EXISTS user (
  user_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  emissions_avoided int,
  email TEXT UNIQUE NOT NULL,
  venmo TEXT UNIQUE,
  classof INTEGER,
  bio TEXT
);
""")
curs.execute("""
CREATE TABLE IF NOT EXISTS trips (
	trip_id INT PRIMARY KEY,
	user_id TEXT NOT NULL,
	starting_place TEXT NOT NULL,
	destination TEXT NOT NULL,
	stops int,
	date DATE,
    time TIME,
	passanger1 TEXT,
	passanger2 TEXT,
	passanger3 TEXT,
	passanger4 TEXT,
	passanger5 TEXT,
	passanger6 TEXT,
	passanger7 TEXT,
	passanger8 TEXT,
    seats_avail INTEGER NOT NULL,
	vehicle TEXT NOT NULL,
	comments TEXT NOT NULL,
    active INTEGER NOT NULL,
	FOREIGN KEY(user_id) REFERENCES user(user_id)
);
""")
curs.execute("""
CREATE TABLE IF NOT EXISTS trip_requests (
	request_id int4,
	driver TEXT,
	rider TEXT,
	trip int4,
	PRIMARY KEY(request_id),
	FOREIGN KEY(trip) REFERENCES trips(trip_id)
);
""")
curs.execute("""
CREATE TABLE IF NOT EXISTS car (
    name TEXT PRIMARY KEY,
    capacity int4,
    fuel_efficiency TEXT NOT NULL
);
""")

curs.execute("""
CREATE TABLE IF NOT EXISTS user_profile (
    user_id TEXT PRIMARY KEY,
	profile_url TEXT NOT NULL
);  
""")

client_id = ''
client_secret = ''
discovery_url = 'https://accounts.google.com/.well-known/openid-configuration'
def get_google_config():
    #error check the request returns right
    return requests.get(discovery_url).json()

#if you say this isn't secure enough
#it was secure enough for my internship at a cyber security company
#def custom_id_getter(withreturn=False):
#    id_file = open('whomst.txt', 'r')
#    whomst = id_file.read()
#    id_file.close()
#    global client_id
#    client_id = whomst
#    if (withreturn):
#        return client_id
#    else:
#        return

#def custom_secret_getter(withreturn=False):
 #   secret_file = open('notouch.txt', 'r')
 #   secret = secret_file.read()
 #   secret_file.close()
 #   global client_secret
 #   client_secret = secret
 #   if (withreturn):
 #       return client_secret
 #   else:
 #       return

def custom_id_getter(withreturn=False):
    whomst = os.environ.get("GOOGLE_CLIENT_ID", None)
    global client_id
    client_id = whomst
    if (withreturn):
        return client_id
    else:
        return 

def custom_secret_getter(withreturn=False):
    secret = os.environ.get("GOOGLE_CLIENT_SECRET", None)
    global client_secret
    client_secret = secret
    if (withreturn):
        return client_secret
    else:
        return


#################################################


def get_logged_in_user(user_id, index=False):
    global yall
    uid = int(user_id)
    loc = -1
    for i in range(len(yall)):
        if (int(yall[i].user_id) == uid):
            loc = i
            break
    curs.execute("""
    SELECT user_id 
    FROM user
    """)
    if (loc >= 0):
        usr = yall[loc]
        return loc if (index) else usr
    else:
        print('No user found')
        return False

login_manager = LoginManager()
login_manager.init_app(app)


#Not sure why it's not in its own function
@login_manager.unauthorized_handler
def unauthorized():
    return ('You must be logged in to access this content.', 403)

# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

# OAuth 2 client setup
client = WebApplicationClient(client_id) if (set_up) else WebApplicationClient(custom_id_getter(True))
# Don't want to needlessly open files
############################################


# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)




def fix_location(l1): #fixes GPS coordinates as stored on DB
    l1 = l1.replace('D', ', ')
    return l1

def load_trip_print(usr):
    retstr = ''
    tripcount = 1
    for i in usr.my_trips:
        #breaks here if recently added trip because was added without trip id
        retstr += ('<p>Trip ' + str(i.trip_id) + ')\n'
                  + 'Driver: ' + i.owner + ' From: ' + fix_location(i.starting_place)
                  + ' To: ' + fix_location(i.destination) + ' Stops: ' + str(i.total_stops)
                  + ' When?: ' + i.date + ' Vehicle: ' + i.vehicle + '\n'
                  + 'Notes: ' + i.comments)
        invites = usr.load_invites(i.trip_id)
        if (invites):
            retstr += ' Requests: ' + str(invites)
        retstr += '</p>'
        tripcount = tripcount + 1
    return retstr
        

def save_trip_request(trp, usr):
    #im tired and don't now SQL leave me alone
    if (current_user.is_authenticated):
        yusr = get_logged_in_user(usr)
        if(yusr.apply_to_trip(trp, usr)):
            return('Trip applied to')
        else:
            return('Something broke')
    
    return 0

def to_unix_time(month, day, year, time):
    #TODO find library that does thiçs
    return (time + 'on ' + str(month) + '/' + str(day) + '/' + str(year))

@app.route('/about/')
@login_required
def about():
    return render_template('cleantech_about.html')

@app.route('/example/')
@login_required
def example():
    return render_template('example_trip.html')

@app.route('/enteratrip/',methods=['GET', 'POST'])
def enteratrip():
    substring = "@bu.edu"
    if (current_user.is_authenticated) and substring in current_user.email:
        if request.method=='POST':
            cursor=conn.cursor()
            start=request.form.get("citystart")
            dest=request.form.get("city")
            date=request.form.get("date")
            time=request.form.get("time")
            model=request.form.get("model")
            uid=current_user.user_id
            seats_avail=request.form.get("seats")
            cursor.execute("SELECT max(trip_id) FROM trips")
            tid=cursor.fetchall()[0][0]
            if tid is None:
                tid=1
            else:
                tid=tid+1
            cursor.execute("INSERT INTO trips (trip_id,user_id,starting_place,destination,date,vehicle,comments,active,time,seats_avail) VALUES ('{0}','{1}','{2}','{3}','{4}','{5}','{6}','{7}','{8}','{9}')".format(tid,uid,start,dest,date,model,'NONE',1,time,seats_avail))
            conn.commit()
            return render_template('Enter_a_trip_cleantech.html')   #Naomi- changed 'enter_a_trip_cleantech.html' to 'Enter_a_trip_cleantech.html'
        else:
            return render_template('Enter_a_trip_cleantech.html')   #Naomi- changed 'enter_a_trip_cleantech.html' to 'Enter_a_trip_cleantech.html'
    else:
        return redirect('http://127.0.0.1:5000/nobu', code=302)

@app.route('/login2/')
def login2():
    return render_template('login2.html')

@app.route('/cleantech/trip/<trip_id>/requestspot', methods = ['GET', 'POST'])
@login_required
def trip_request(trip_id): #to keep this simple we could make it unclickable if there's no empty seats
    if (current_user.is_authenticated):
        tid = int(trip_id)
        uid = current_user.get_id()
        if (save_trip_request(tid, uid)):
            return('Trip saved')
        else:
            return('Saving failed')
        


@app.route('/cleantech/trip/', methods = ['GET', 'POST'])
@login_required
def view_trips():
    #TODO:
    #Page that shows all open trips
    if (request.method == 'GET'):

        if (len(all_trips) > 0):
            print('Trips: ' + str(len(all_trips)))
            for i in range(len(all_trips)):
                if ((all_trips[i].trip_id != None) and (all_trips[i].trip_id != 0)):
                    print(all_trips[i].trip_id)
                    return render_template('homepage_cleantech.html', place=all_trips[i].trip_id, starting=all_trips[i].starting_place, ending=all_trips[i].destination, date=all_trips[i].date, driver=all_trips[i].owner)
                else:
                    print(all_trips[i].date + all_trips[i].vehicle + str(all_trips[i].trip_id))
        return 'Not possible'
    if (request.method == 'POST'):
        print("post")
        print(request.form)
        print(request.form['place'])
        return('Applied')

@app.route('/cleantech/user/<usr_id>', methods = ['GET', 'POST', 'DELETE'])
@login_required
def showstuff(usr_id):
    if (request.method == 'GET'):
        if (current_user.is_authenticated):
    #        print('CU:',current_user.get_id(),'done',sep='\n') #debug
            uid = int(usr_id)
            usr = get_logged_in_user(uid) #shouldnt fail
            if (not usr):
                return redirect('http://127.0.0.1:5000/logout', code=302)
            if (not (usr.my_trips)):
                print('No trips found on DB for this user')
                return render_template('no_sensor.html')
            
            trps = load_trip_print(usr)
            return (trps)
    if (request.method == 'POST'):
        text = request.form['text']

        rstr = 'http://127.0.0.1:5000/cleantech/' + usr_id + '/add_trip/' + text + '/'
        return redirect(rstr, code=302)
#
    else:
        return "I have no idea what you're trying to do"

@app.route('/cleantech/user/')
@login_required
def reroutetouser():
    if (current_user.is_authenticated):        
        uid = current_user.get_id()
        whereto = 'http://127.0.0.1:5000/cleantech/user/' + uid
        return redirect(whereto, code=302)


@app.route('/cleantech/add_trip/')
@login_required
def reroutetoaddtrip():
    if (current_user.is_authenticated):        
        uid = current_user.get_id()
        whereto = 'http://127.0.0.1:5000/cleantech/user/' + uid + '/add_trip/nocomment/'
        return redirect(whereto, code=302)



@app.route('/cleantech/user/<usr_id>/add_trip/<comments>/', methods = ['GET', 'POST'])
@login_required #rename to make_trip
def make_trip(usr_id, comments):
    if (current_user.is_authenticated):        
        if request.method == 'GET':
            print(comments)
            
            #magic frontend that gets details from user goes here
            #usr.save_trip(usr.user_id, usr, date, stops, passangers, vehicle, starting_location, ending_location, comments)
            #trp = trip('Never', 'Tesla' '42.348097D-71.105963', '40.748298D-73.984827', 2, comments) #never instantiate a trip in this ever
            #usr.my_trips.append(trp)
            return render_template('Enter_a_trip_cleantech.html')
            
            whereto = 'http://127.0.0.1:5000/cleantech/user/'+str(usr.id)
            return redirect(whereto, code=302)
    	
        if request.method == 'POST':
            print('madeit')
            uid = int(usr_id)
            usr = get_logged_in_user(uid)
            time = to_unix_time(request.form['month'], request.form['day'], request.form['year'], request.form['time']) #not implemented
            #### Input validation #####
            print('checking form')
            if (request.form['state'] and request.form['seats'] and request.form['model'] and request.form['Make'] and request.form['City']):
                print('Nice input')
                
                trp = usr.save_trip(usr.user_id, time, 2, request.form['seats'], request.form['Make']+request.form['model'], 'Boston,MA', (str(request.form['City'])+','+request.form['State']), 'No Drugs or alcohol')
                print('saved trip')
                trp.owner = usr_id
                trps = usr.load_trips(uid)
                if (trps): usr.my_trips = trps
                if (usr.my_trips): usr.my_trips.append(trp)
                print(request.form)
                whereto = 'http://127.0.0.1:5000/cleantech/'
                return redirect(whereto, code=302)
                
                
            whereto = 'http://127.0.0.1:5000/cleantech/'
            return redirect(whereto, code=302)
                   

@app.route('/cleantech')
@login_required
def rut():
    if (current_user.is_authenticated):
        uid = current_user.get_id()
        whereto = 'http://127.0.0.1:5000/cleantech/user/' + uid
        return redirect(whereto, code=302)
    else: 
        return redirect('http://127.0.0.1:5000/login', code=302)

@app.route("/login")
def login():
    global set_up
    if (not (set_up)):
        custom_id_getter()
        custom_secret_getter()
    if (current_user.is_authenticated):
        uid = current_user.get_id()
        whereto = 'http://127.0.0.1:5000/'
        #this was in the original code - not sure if I can take out or not so I'm just commenting it: whereto = 'http://127.0.0.1:5000/cleantech/users/' + uid
        return redirect(whereto, code=302)

    google_config = get_google_config()
    authorization_endpoint = google_config["authorization_endpoint"]
    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/success",
        scope=["openid", "email", "profile"],
    )

    print('Redirected after login')
    return redirect(request_uri)


@app.route("/login/success")
def success():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    google_config = get_google_config()
    token_endpoint = google_config["token_endpoint"]

    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )

    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(client_id, client_secret)
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_config["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"] # todo: from exaple breaks without.
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in your db with the information provided
    # by Google
    user = User(
        user_id=unique_id, name=users_name, email=users_email)
    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email)

    print(user.user_id)
    maybetrip = None
    try:
        maybetrip = user.load_trips(user.user_id) #load trips from DB so they are there when it is appended to yall
    except sqlite3.OperationalError:
        pass
    if (maybetrip): 
        user.my_trips = maybetrip #never ever delete this line
    else:
        user.my_trips = []
    # Begin user session by logging the user in
    login_user(user)
    latrips = False #loadalltrips
    global yall
    if (len(yall) == 0 and (maybetrip != None)):
        
        latrips = user.load_all_trips()
        if (latrips):
            global all_trips
            all_trips = latrips
    
    yall.append(user)
    user.loaded = True
    #print(user)
    # Send user back to homepage
    #this was in the original code - not sure if I can take out or not so I'm just commenting it: whereto = 'http://127.0.0.1:5000/cleantech/user/'+str(user.id)
    whereto = 'http://127.0.0.1:5000/'
    return redirect(whereto, code=302)

@app.route('/setup/')
def setup():
    global set_up #flag for initialization
    if (not (set_up)):
        custom_id_getter()
        custom_secret_getter()
        set_up = True
    return redirect('http://127.0.0.1:5000/', code=302)

@app.route('/tripinfo', methods=['GET', 'POST'])
def trip_info():
    substring = "@bu.edu"
    if (current_user.is_authenticated) and substring in current_user.email:
        userid=current_user.user_id
        cursor=conn.cursor()
        if request.method=='POST':
            tripid=request.args.get("tripid")
            cursor.execute("SELECT starting_place, destination, date, time, seats_avail, user_id FROM trips WHERE trip_id='{0}'".format(tripid))
            information=cursor.fetchone()
            cursor.execute("SELECT passanger1, passanger2, passanger3,passanger4,passanger5,passanger6,passanger7,passanger8 FROM trips WHERE trip_id='{0}'".format(tripid))
            passengerinfo=cursor.fetchone()
            if information[5]==userid:
                if request.form.get("edit"):
                    start=request.form.get("from")
                    finish=request.form.get("to")
                    begindate=request.form.get("leaves")
                    begintime=request.form.get("at")
                    seatsavail=request.form.get("seatsavail")
                    cursor.execute("UPDATE trips SET starting_place='{0}', destination='{1}', date='{2}', time='{3}', seats_avail='{4}' WHERE trip_id='{5}'".format(start,finish,begindate,begintime,seatsavail,tripid))
                    conn.commit()
                    cursor.execute("SELECT starting_place,destination,date,time,user.name,seats_avail,trip_id, user.user_id FROM trips JOIN user ON user.user_id=trips.user_id WHERE trips.active=1")
                    trips=cursor.fetchall()
                    return render_template('homepage_cleantech.html', trips=trips, testcode="SUCCESSFULLY Updated")
                else:
                    cursor.execute("DELETE FROM trips WHERE trip_id='{0}'".format(tripid))
                    cursor.execute("SELECT starting_place,destination,date,time,user.name,seats_avail, trip_id, user.user_id FROM trips JOIN user ON user.user_id=trips.user_id WHERE trips.active=1")
                    trips=cursor.fetchall()
                    conn.commit()
                    return render_template('homepage_cleantech.html', trips=trips, testcode="SUCCESSFULLY Deleted")
            elif userid in passengerinfo:
                if passengerinfo[0] == userid:
                    cursor.execute("UPDATE trips SET passanger1=NULL WHERE trip_id='{0}'".format(tripid))
                elif passengerinfo[1]==userid:
                    cursor.execute("UPDATE trips SET passanger2=NULL WHERE trip_id='{0}'".format(tripid))
                elif passengerinfo[2]==userid:
                    cursor.execute("UPDATE trips SET passanger3=NULL WHERE trip_id='{0}'".format(tripid))
                elif passengerinfo[3]==userid:
                    cursor.execute("UPDATE trips SET passanger4=NULL WHERE trip_id='{0}'".format(tripid))
                elif passengerinfo[4]==userid:
                    cursor.execute("UPDATE trips SET passanger5=NULL WHERE trip_id='{0}'".format(tripid))
                elif passengerinfo[5]==userid:
                    cursor.execute("UPDATE trips SET passanger6=NULL WHERE trip_id='{0}'".format(tripid))
                elif passengerinfo[6]==userid:
                    cursor.execute("UPDATE trips SET passanger7=NULL WHERE trip_id='{0}'".format(tripid))
                else:
                    cursor.execute("UPDATE trips SET passanger8=NULL WHERE trip_id='{0}'".format(tripid))
                cursor.execute("UPDATE trips SET seats_avail=seats_avail+1 WHERE trip_id='{0}'".format(tripid))
                conn.commit()
                cursor.execute("SELECT starting_place,destination,date,time,user.name,seats_avail, trip_id, user.user_id FROM trips JOIN user ON user.user_id=trips.user_id WHERE trips.active=1")
                trips=cursor.fetchall()
                return render_template('homepage_cleantech.html', trips=trips, testcode="Successfully Canceled Reservation")

            else:
                if information[4]==0:
                    cursor.execute("SELECT starting_place,destination,date,time,user.name,seats_avail, trip_id, user.user_id FROM trips JOIN user ON user.user_id=trips.user_id WHERE trips.active=1")
                    trips=cursor.fetchall()
                    return render_template('homepage_cleantech.html', trips=trips, testcode="NO SEATS AVAILABLE")
                else:
                    if passengerinfo[0] is None:
                        cursor.execute("UPDATE trips SET passanger1='{0}' WHERE trip_id='{1}'".format(userid,tripid))
                    elif passengerinfo[1] is None:
                        cursor.execute("UPDATE trips SET passanger2='{0}' WHERE trip_id='{1}'".format(userid,tripid))
                    elif passengerinfo[2] is None:
                        cursor.execute("UPDATE trips SET passanger3='{0}' WHERE trip_id='{1}'".format(userid,tripid))
                    elif passengerinfo[3] is None:
                        cursor.execute("UPDATE trips SET passanger4='{0}' WHERE trip_id='{1}'".format(userid,tripid))
                    elif passengerinfo[4] is None:
                        cursor.execute("UPDATE trips SET passanger5='{0}' WHERE trip_id='{1}'".format(userid,tripid))
                    elif passengerinfo[5] is None:
                        cursor.execute("UPDATE trips SET passanger6='{0}' WHERE trip_id='{1}'".format(userid,tripid))
                    elif passengerinfo[6] is None:
                        cursor.execute("UPDATE trips SET passanger7='{0}' WHERE trip_id='{1}'".format(userid,tripid))
                    else:
                        cursor.execute("UPDATE trips SET passanger8='{0}' WHERE trip_id='{1}'".format(userid,tripid))
                    cursor.execute("UPDATE trips SET seats_avail=seats_avail-1 WHERE trip_id='{0}'".format(tripid))
                    conn.commit()
                    cursor.execute("SELECT starting_place,destination,date,time,user.name,seats_avail, trip_id, user.user_id FROM trips JOIN user ON user.user_id=trips.user_id WHERE trips.active=1")
                    trips=cursor.fetchall()
                    return render_template('homepage_cleantech.html', trips=trips, testcode="Successfully Signed Up")
        else:
            tripid=request.args.get("tripid")
            cursor.execute("SELECT starting_place, destination, date, time, seats_avail, user_id FROM trips WHERE trip_id='{0}'".format(tripid))
            information=cursor.fetchone()
            cursor.execute("SELECT passanger1, passanger2, passanger3,passanger4,passanger5,passanger6,passanger7,passanger8 FROM trips WHERE trip_id='{0}'".format(tripid))
            passengerinfo=cursor.fetchone()
            passengeridlist = [];
            passengernamelist = [];
            for passenger in passengerinfo:
                if passenger != None:
                    passengeridlist.append(passenger);
            if len(passengeridlist) != 0:
                for passenger in passengeridlist:
                    cursor.execute("SELECT name FROM user WHERE user_id='{0}'".format(passenger))
                    passengername = cursor.fetchone()[0]
                    passengernamelist.append(passengername)
            if information[5]==userid:   
                return render_template("trip_info.html", info=information, passengerinfo=passengernamelist, trip=True)
            else:
                if userid in passengerinfo:
                    return render_template("trip_info.html", info=information, text="Cancel Reservation")
                return render_template("trip_info.html", info=information, text="Reserve Seat")
    else:

        return redirect('http://127.0.0.1:5000/login2', code=302)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/viewprofile', methods=['GET', 'POST'])
def viewprofile():
    cursor=conn.cursor()
    uid=current_user.user_id
    cursor.execute("SELECT user_id FROM user_profile WHERE user_id='{0}'".format(uid))
    count = cursor.fetchone()
    if count[0]:
        print("ok")
    else:
        default_url = 'default-profile-pic.jpg'
        cursor.execute("INSERT INTO user_profile (user_id, profile_url) VALUES ('{0}', '{1}')".format(uid, default_url))
    cursor.execute("SELECT name, classof, email, bio FROM user WHERE user_id='{0}'".format(uid))
    information=cursor.fetchone()
    cursor.execute("SELECT starting_place,destination,date,time, user.name, seats_avail, trip_id FROM trips JOIN user ON user.user_id=trips.user_id WHERE user.user_id ='{0}' OR trips.passanger1 ='{0}' OR trips.passanger2 ='{0}' OR trips.passanger3 ='{0}' OR trips.passanger4 ='{0}' OR trips.passanger5 ='{0}' OR trips.passanger6 ='{0}' OR trips.passanger7 ='{0}' OR trips.passanger8 ='{0}'".format(uid))
    trips=cursor.fetchall()
    cursor.execute("SELECT profile_url FROM user_profile WHERE user_id='{0}'".format(uid))
    profilepic = cursor.fetchone()
    print(profilepic)
    if request.method=='POST':
        filename = ""
        file = request.files["file"]
        if file.filename == '':
            print('No image selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename): 
           filename = secure_filename(file.filename)
           file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        classyear=request.form.get("year")
        bio=request.form.get("bio")
        cursor.execute("UPDATE user SET classof='{0}', bio='{1}' WHERE user_id='{2}'".format(classyear, bio, uid))
        cursor.execute("UPDATE user_profile SET profile_url='{0}' WHERE user_id='{1}'".format(filename, uid))
        conn.commit()
        cursor.execute("SELECT starting_place,destination,date,time,user.name,seats_avail, trip_id, user.user_id FROM trips JOIN user ON user.user_id=trips.user_id WHERE trips.active=1")
        trips=cursor.fetchall()
        return render_template('homepage_cleantech.html', trips=trips)
    else:
        return render_template('user_profile.html', info=information, trips = trips, profile = profilepic)


@app.route('/display/<filename>')
def display_image(filename):
    return redirect(url_for('static', filename = 'uploads/' + filename), code = 301)

@app.route('/viewotherprofile', methods=['GET'])
def viewotherprofile():
    cursor=conn.cursor()
    uid=current_user.user_id
    getuserid=request.args.get("uid")
    cursor.execute("SELECT name, classof, email, bio FROM user WHERE user_id='{0}'".format(getuserid))
    information=cursor.fetchone()
    if uid==getuserid:
        return render_template('user_profile.html', info=information)
    else:
        return render_template('other_profile.html', info=information)



#http://127.0.0.1:5000/
@app.route('/')
def begin():
   # global set_up
   # if (not set_up):
      #  return redirect('http://127.0.0.1:5000/setup/', code=302)
        #redirects to setup page
    substring = "@bu.edu"
    if (current_user.is_authenticated) and substring in current_user.email:
        cursor=conn.cursor()
        cursor.execute("SELECT email FROM user WHERE email='{0}'".format(current_user.email))
        list1=cursor.fetchone()
        if list1 is None:
            cursor.execute("INSERT INTO User (user_id,name, email) VALUES ('{0}','{1}','{2}')".format(current_user.user_id,current_user.name,current_user.email))
        cursor.execute("SELECT user_id FROM user WHERE user_id=1")
        list2=cursor.fetchone()
        if list2 is None:
            cursor.execute("INSERT INTO user (user_id, name, email) VALUES ('{0}', '{1}', '{2}')".format(1,"test","test@bu.edu"))
            conn.commit()
            cursor.execute("INSERT INTO trips (trip_id, user_id, starting_place, destination, seats_avail,vehicle, comments, active) VALUES ('{0}','{1}','{2}','{3}','{4}','{5}','{6}','{7}')".format(0,1,"Miami","Boston",8,"Honda","No new comments",1))
        conn.commit()
        cursor.execute("SELECT starting_place,destination,date,time,user.name,seats_avail, trip_id, user.user_id FROM trips JOIN user ON user.user_id=trips.user_id WHERE trips.active=1")
        trips=cursor.fetchall()
        return render_template('homepage_cleantech.html',trips=trips) #redirect('http://127.0.0.1:5000/cleantech/', code=302)
    elif (current_user.is_authenticated):
        return redirect('http://127.0.0.1:5000/nobu', code=302)
    else:
        return redirect('http://127.0.0.1:5000/login2', code=302)
    #redirects to setup page
@app.route("/nobu")
@login_required
def nobu():
    return render_template('nobu.html')

@app.route("/logout")
@login_required
def logout():
    if (current_user.is_authenticated):
        global yall
        if get_logged_in_user(current_user.get_id(), True) : yall.pop(get_logged_in_user(current_user.get_id(), True)) #This is why OOP is bad
        logout_user()
        print('User logged out')
    return redirect('http://127.0.0.1:5000/', code=302)

@app.route("/weather/", methods=['GET', 'POST'])
@login_required
def textbox():
    return render_template('search.html')

# to avoid issues iwth insecure transport over http
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

#redirects learnt from https://stackoverflow.com/questions/14343812/redirecting-to-url-in-flask


if __name__=='__main__':
    app.run(debug="true")
