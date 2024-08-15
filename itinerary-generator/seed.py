from app import app
from models import db, User, Activity, Itinerary

with app.app_context():
    db.drop_all()
    db.create_all()
    # add users
    p1 = User.register(
        username = "testUser1",
        password = "pw1234",
        email = "emailTest1@gmail.com",
        image_url = None,
    )

    p2 = User.register(
        username = "testUser2",
        password = "pw1234",
        email = "emailTest2@gmail.com",
        image_url = None,
    )
    db.session.commit()
    
    # add itineraries
    i1 = Itinerary(
        title="title1",
        location="Chicago",
        user_id = 1,
        notes = "note1",
        radius = 5
    )
    db.session.add(i1)
    db.session.commit()
    
    # add activities
    a1 = Activity(
        user_id = 1,
        title="Some Restaurant",
        category = "eats",
        activity_url = "test.com",
        address = "123 imaginary st"
    )
    
    a2 = Activity(
        user_id = 1,
        title="Some activity",
        category = "outdoor",
        activity_url = "test.com",
        address = "345 imaginary st"
    )
    
    a3 = Activity(
        user_id = 1,
        title="Sky Diving",
        category = "adventure",
        activity_url = "test.com",
        address = "657 imaginary st"
    )
    i1.add_activities([a1,a2,a3])
    db.session.commit()
    