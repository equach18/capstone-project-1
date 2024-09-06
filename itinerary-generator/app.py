from dotenv import load_dotenv
import os

load_dotenv()

from flask import Flask, render_template, request, flash, redirect, session, g, url_for, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from functools import wraps
from sqlalchemy.exc import IntegrityError
from googleplaces import GooglePlaces, types, lang
import random
import requests
from flask_cors import CORS

# the '.' was added to support the website launch on render. For testing or if running the app locally, please comment out the next two lines and uncomment the following two. 
from .models import connect_db, db, User, Itinerary, Activity
from .forms import UserAddForm, LoginForm
# from models import connect_db, db, User, Itinerary, Activity
# from forms import UserAddForm, LoginForm

CURR_USER_KEY = "curr_user"
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
google_places = GooglePlaces(GOOGLE_MAPS_API_KEY)

app = Flask(__name__)
app.app_context().push()

# comment out the next two lines for unit testing 
CORS(app, resources={r"/*": {"origins": "https://spontinerary.onrender.com"}})
app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('SUPABASE_DB_URL', 'postgresql:///spontinerary'))

# uncomment the next line for unit testing 
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///spontinerary'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
toolbar = DebugToolbarExtension(app)

connect_db(app)

@app.before_request
def add_user_to_g():
    """Add the curent user to Flask global if logging in."""
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None
        
def login_required(f):
    """Requires the user to login before continuing."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash("Access unauthorized. Please log in to continue.", "danger")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def do_login(user):
    """Log the user in."""
    session[CURR_USER_KEY] = user.id


def do_logout():
    """Log the user out."""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
        
def get_long_lat(address):
    """Returns the longitude and latitude of the given address"""
    response = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params={'address':address, 'key': GOOGLE_MAPS_API_KEY})
    data = response.json()
    
    if response.status_code == 200 and data['status'] == 'OK':
        # Get the latitude and longitude from the response
        location = data['results'][0]['geometry']['location']
        latitude = location['lat']
        longitude = location['lng']
        return latitude, longitude
    else:
        raise Exception(f"Error getting geocode: {data['status']}")
        
def process_activities(itinerary, categories):
    """Processes the categories given by the user to return random activities"""
    for category in categories:
    # Make a request to Google Places API
        location = get_long_lat(itinerary.location)
        location_str = f"{location[0]},{location[1]}"
        resp = requests.get('https://maps.googleapis.com/maps/api/place/nearbysearch/json', params={
            'location': location_str,  
            'radius': itinerary.radius,  
            'keyword': category, 
            'key': GOOGLE_MAPS_API_KEY
        })
        
        if resp.status_code != 200:
            raise Exception(f"Google Places API error: {resp.status_code}")
                            
        places = resp.json().get('results', [])
        if places:
            # Randomly select a place from the results
            selected_place = random.choice(places)
            # retrieve the details of the selected place
            details_resp = requests.get('https://maps.googleapis.com/maps/api/place/details/json', params={
                'place_id': selected_place['place_id'],
                'key': GOOGLE_MAPS_API_KEY
            })
            
            place_details = details_resp.json().get('result', {})
            
            # Create a new Activity object and save it to the database
            new_activity = Activity(
                title = selected_place['name'],
                itinerary_id=itinerary.id, # Associate with the current itinerary
                user_id=itinerary.user_id,
                category=category,
                address=selected_place['vicinity'],
                activity_url=place_details.get('url', None),
                summary=place_details.get('editorial_summary', {}).get('overview', None)
            )
            db.session.add(new_activity)
    
    # Commit the changes to save all activities
    db.session.commit()

# routes
@app.route('/')
def homepage():
    """Renders the homepage."""
    if g.user:
        return render_template('users/show.html', user=g.user)
    return render_template("home.html")

@app.route('/login', methods=["POST","GET"])
def login():
    """Logs the user in."""
    form = LoginForm()
    # Checks if a post request was made and the form is validated
    if form.validate_on_submit():
        # Logs the user in if authenticated. If not, user will be alerted.
        user = User.authenticate(form.username.data, form.password.data)
        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect('/')
        else:
            flash("Invalid username and/or password", "danger")
    # Renders the log in page if a get request was made
    return render_template('users/login.html', form=form)

@app.route('/signup', methods=["POST","GET"])
def signup():
    """Signs the user up."""
    form = UserAddForm()
    if form.validate_on_submit():
        # Attempt to register the user. If there is an error, then the user will be notified
        try:
            user = User.register(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                image_url=form.image_url.data or User.image_url.default.arg
            )
            db.session.commit()
        except IntegrityError:
            flash("This username or email already exists", 'danger')
            db.session.rollback()
            return render_template('users/signup.html', form=form)
        # When the user successfully registers, then log them in and redirect to their homepage.
        do_login(user)
        flash(f"Hello, {user.username}!", "success")
        return redirect('/')
    # Upon a get request, render the signup form
    return render_template('users/signup.html', form=form)

@app.route('/itinerary/new', methods=["POST", "GET"])
# Ensures that a user is logged in before creating an itinerary.
@login_required
def create_itinerary():
    """Creates a new itinerary for the user"""
    # Checks if post request
    if request.method == 'POST':
        # Retrieve the user inputs.
        title = request.form['title']
        location = request.form['location']
        radius = request.form['radius'] 
        notes = request.form.get('notes')
        
        # Make sure that all of the required inputs are filled out
        if not title or not location or not radius:
            flash("Please fill in the required fields", 'danger')
            return render_template('itinerary/new.html', api_key=GOOGLE_MAPS_API_KEY)
        
        try:
            new_itinerary=Itinerary(
                title = title,
                location = location,
                notes = notes or None,
                radius= int(radius) * 1000,
                user_id = g.user.id
            )
            db.session.add(new_itinerary)
            db.session.commit()
            return redirect(f"/itinerary/{new_itinerary.id}")
        except IntegrityError:
            db.session.rollback()
            flash("Invalid Inputs", 'danger')

    return render_template('itinerary/new.html', api_key=GOOGLE_MAPS_API_KEY)
    
    
@app.route('/itinerary/<int:itinerary_id>')
@login_required
def show_itinerary(itinerary_id):
    """Renders the itinerary page where it lists the activities if there are any"""
    # query the selected itinerary
    itinerary = Itinerary.query.get(itinerary_id)
    
    return render_template('itinerary/show.html', itinerary=itinerary)
    
    
@app.route('/itinerary/<int:itinerary_id>/new', methods=["POST", "GET"])
@login_required
def add_activities(itinerary_id):
    """Add activities to the itinerary"""
    itinerary = Itinerary.query.get_or_404(itinerary_id)
    
    # ensure that users cannot add activities to itineraries that is not theirs
    if itinerary.user_id != g.user.id:
        flash("Access unauthorized. You cannot add to another user's itinerary.", "danger")
        return redirect("/")
    
    if request.method == 'POST':
        #  make a list of all the categories from the user inputs 
        categories = request.json.get('categories', [])
        
        if not categories:
            return jsonify({"error": "Please select at least one activity category."}), 400
        
        process_activities(itinerary, categories)
        return jsonify({"message": "Activities added successfully", "redirect_url": f"/itinerary/{itinerary_id}"})
    
    # Renders the new activity form upon a get request
    return render_template('activity/new.html', itinerary=itinerary)

@app.route('/logout')
@login_required
def logout():
    """Logs the user out"""
    do_logout()
    flash("You have successfully logged out.")
    return redirect("/")


@app.route('/activity/<int:activity_id>/delete', methods=["POST"])
@login_required
def activity_delete(activity_id):
    """Deletes the activity"""
    activity = Activity.query.get_or_404(activity_id)
    itinerary_id = activity.itinerary_id
    
    # ensures that another user cannot delete another user's activity
    if activity.user_id != g.user.id:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    db.session.delete(activity)
    db.session.commit()
    flash("Activity removed.")
    return redirect(f"/itinerary/{itinerary_id}")

@app.route('/itinerary/<int:itinerary_id>/delete', methods=["POST"])
@login_required
def itinerary_delete(itinerary_id):
    """Deletes the itinerary"""
    itinerary = Itinerary.query.get_or_404(itinerary_id)
    
    # ensures that another user cannot delete another user's itinerary
    if itinerary.user_id != g.user.id:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    db.session.delete(itinerary)
    db.session.commit()
    return redirect("/")
    
    
@app.route('/activity/all', methods=['GET'])
@login_required
def show_activities():
    """Renders a list of all the current user's activities"""
    activities = Activity.query.filter(Activity.user_id==g.user.id)
    return render_template('/activity/show.html', activities=activities)