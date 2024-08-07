import os

from flask import Flask, render_template, request, flash, redirect, session, g, url_for
from flask_debugtoolbar import DebugToolbarExtension
from functools import wraps
from sqlalchemy.exc import IntegrityError

from models import connect_db, db, User, Itinerary, Activity
from forms import UserAddForm, LoginForm, ItineraryAddForm

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
app.app_context().push()

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///spontinerary'))

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
    
    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect('/')
        else:
            flash("Invalid username and/or password", "danger")
    return render_template('users/login.html', form=form)

@app.route('/signup', methods=["POST","GET"])
def signup():
    """Signs the user up."""
    form = UserAddForm()
    if form.validate_on_submit():
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
        do_login(user)
        return redirect('users/show.html')

    return render_template('/', form=form)

@app.route('/new-itinerary', methods=["POST", "GET"])
def create_itinerary():
    """Creates a new itinerary for the user"""
    form = ItineraryAddForm()
    if form.validate_on_submit():
        itinerary = Itinerary(
            title = form.title.data,
            location = form.title.data,
            user_id = g.user.id,
            notes = form.notes.data,
        )
        db.session.add(itinerary)
        db.session.commit()
        
        return redirect('/')
    return render_template('itinerary/new.html', form=form)
    
