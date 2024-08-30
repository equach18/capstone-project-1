from app import db, app
from models import User, Itinerary, Activity

app.app_context().push()
db.drop_all()
db.create_all()