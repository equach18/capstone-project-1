from dotenv import load_dotenv
import os

load_dotenv()

from flask import Flask, render_template, request, flash, redirect, session, g, url_for
from flask_debugtoolbar import DebugToolbarExtension
from functools import wraps
from sqlalchemy.exc import IntegrityError
from googleplaces import GooglePlaces, types, lang

from models import connect_db, db, User, Itinerary, Activity
from forms import UserAddForm, LoginForm

CURR_USER_KEY = "curr_user"
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
google_places = GooglePlaces(GOOGLE_MAPS_API_KEY)

app = Flask(__name__)
app.app_context().push()

app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', 'postgresql:///spontinerary'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
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
        

# routes
@app.route('/')
def root():
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
            flash("Invalid Inputs", 'danger')
            return render_template('users/signup.html', form=form)
        # When the user successfully registers, then log them in and redirect to their homepage.
        do_login(user)
        return redirect('/')
    # Upon a get request, render the signup form
    return render_template('users/signup.html', form=form)

@app.route('/new-itinerary', methods=["POST", "GET"])
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
        
        new_itinerary=Itinerary(
            title = title,
            location = location,
            notes = notes or None,
            radius=radius,
            user_id = g.user.id
        )
        db.session.add(new_itinerary)
        db.session.commit()
        return redirect(f"/itinerary/{new_itinerary.id}")

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
    itinerary = Itinerary.query.get(itinerary_id)
    
    # Renders the new activity form upon a get request
    return render_template('itinerary/activity.html', itinerary=itinerary)