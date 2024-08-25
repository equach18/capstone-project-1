"""Activity model tests."""

#    python3 -m unittest tests/test_activity_model.py

import os
from unittest import TestCase
from sqlalchemy import exc


from models import db, User, Activity, Itinerary

os.environ['DATABASE_URL'] = "postgresql:///spontinerary-test"


from app import app
app.app_context().push()

db.create_all()

class ActivityModelTestCase(TestCase):
    """Tests the Activity model."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()
        
        # create user
        self.user_id = 3231
        user = User.register(
            email="user1@test.com",
            username="user1",
            password="testpw1",
            image_url=None
        )
        user.id = self.user_id
        db.session.commit()
        
        self.user = User.query.get(self.user_id)
        
        # create itineraries 
        i1 = Itinerary(
            title = "itinerary1",
            location = "some place",
            user_id = self.user_id,
            radius = 20,
            notes = "to do in some place"
        )
        self.i1_id = 343
        i1.id = self.i1_id
        
        
        i2 = Itinerary(
            title = "itinerary2",
            location = "anoter place",
            user_id = self.user_id,
            radius = 30,
            notes = "to do in another place"
        )
        self.i2_id = 9789
        i2.id = self.i2_id
        
        db.session.add_all([i1,i2])
        db.session.commit()
        
        self.i1 = Itinerary.query.get(self.i1_id)
        self.i2 = Itinerary.query.get(self.i2_id)
        
        
        self.client = app.test_client()
    
    def tearDown(self):
        db.session.rollback()
        
    def test_activity_model(self):
        """Tests the basic Activity model."""
        # create activities to add to the itineraries
        a1 = Activity(
            user_id = self.user_id,
            title = "Some Restaurant",
            category = "eats",
            activity_url = "test.com",
            address = "123 imaginary st",
            summary = "summary1"
        )
        
        a2 = Activity(
            user_id = self.user_id,
            title = "Some activity",
            category = "outdoor",
            activity_url = "test.com",
            address = "345 imaginary st",
            summary = "summary2"
        )
        
        self.i1.add_activities([a1,a2])
        db.session.commit()

        self.assertEqual(len(self.user.activities), 2)
        self.assertEqual(len(self.i1.activities), 2)
        # checks that the activities are associated with the correct itinerary
        self.assertEqual(a1.itinerary_id, self.i1_id)
        self.assertEqual(a2.itinerary_id, self.i1_id)
        # checks the data in each activity is correct
        self.assertEqual(a1.title, "Some Restaurant")
        self.assertEqual(a2.title, "Some activity")
        self.assertEqual(a1.category, "eats")
        self.assertEqual(a2.category, "outdoor")
        
        # checks that the activities are persisted in the database
        saved_a1 = Activity.query.get(a1.id)
        saved_a2 = Activity.query.get(a2.id)

        self.assertIsNotNone(saved_a1)
        self.assertIsNotNone(saved_a2)

def test_optional_fields(self):
    """Tests the optional fields of the model. Makes sure that data can be added without those fields"""
    activity = Activity(
        itinerary_id=self.i1_id,
        user_id=self.user_id,
        title='Another test',
        category='Tours',
        activity_url=None,
        address=None    
    )
    db.session.add(activity)
    db.session.commit()
    self.assertIsNotNone(activity.id)