CREATE TABLE user (
  user_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  emissions_avoided int,
  email TEXT UNIQUE NOT NULL,
  venmo TEXT UNIQUE
);

CREATE TABLE trips (
	trip_id int4 NOT NULL AUTO_INCREMENT,
	user_id TEXT NOT NULL,
	starting_place TEXT NOT NULL,
	destination TEXT NOT NULL,
	stops int,
	date TEXT NOT NULL,
	passanger1 TEXT,
	passanger2 TEXT,
	passanger3 TEXT,
	passanger4 TEXT,
	passanger5 TEXT,
	passanger6 TEXT,
	passanger7 TEXT,
	passanger8 TEXT,
	vehicle TEXT NOT NULL,
	comments TEXT NOT NULL,
	PRIMARY KEY(trip_id),
	FOREIGN KEY(user_id) REFERENCES user(user_id)
);

CREATE TABLE trip_requests (
	request_id int4 AUTO_INCREMENT,
	driver TEXT,
	rider TEXT,
	trip int4,
	PRIMARY KEY(request_id),
	FOREIGN KEY(trip) REFERENCES trips(trip_id)
);


CREATE TABLE car (
    name TEXT PRIMARY KEY,
    capacity int4,
    fuel_efficiency TEXT NOT NULL,
);

CREATE TABLE user_profile (
	user_id TEXT PRIMARY KEY,
	profile_url TEXT NOT NULL 
)

CREATE TABLE trip_urls (
	trip_id INT PRIMARY KEY,
	trip_url TEXT
)
