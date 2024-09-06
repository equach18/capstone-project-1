"""Itinerary model tests."""

#    python3 -m unittest tests/test_itinerary_model.py

import os
from unittest import TestCase

from models import db, User, Activity, Itinerary

os.environ['DATABASE_URL'] = "postgresql:///spontinerary-test"


from app import app
app.app_context().push()

db.create_all()

class ItineraryModelTestCase(TestCase):
    """Tests the Itinerary model."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()
        
        # create user
        self.user1_id = 345345
        user1 = User.register(
            email="user1@test.com",
            username="user1",
            password="testpw1",
            image_url=None
        )
        user1.id = self.user1_id
        
        db.session.commit()
        
        self.user1 = User.query.get(self.user1_id)

        self.client = app.test_client()
    
    def tearDown(self):
        db.session.rollback()

    def test_itinerary_model(self):
        """Tests the itinerary basic model"""

        itinerary = Itinerary(
            title = "test itinerary",
            location = "some place",
            user_id = self.user1_id,
            radius = 20,
            notes = "to do in some place"
        )
        
        self.itinerary_id = 2453
        itinerary.id = self.itinerary_id
        
        db.session.add(itinerary)
        db.session.commit()

        self.assertEqual(len(self.user1.itineraries), 1)
        self.assertEqual(self.user1.itineraries[0].title, "test itinerary")
        self.assertEqual(self.user1.itineraries[0].location, "some place")
        self.assertEqual(self.user1.itineraries[0].user_id, self.user1_id)
        self.assertEqual(self.user1.itineraries[0].radius, 20)
        self.assertEqual(self.user1.itineraries[0].notes, "to do in some place")
        
        
    def test_add_activities(self):
        """Tests add_activity"""
        
        itinerary = Itinerary(
            title = "test2 itinerary",
            location = "another place",
            user_id = self.user1_id,
            radius = 60,
            notes = "a note"
        )
        
        self.itinerary_id = 35
        itinerary.id = self.itinerary_id
        
        db.session.add(itinerary)
        db.session.commit()
        
        # create activities 
        a1 = Activity(
            user_id = self.user1_id,
            title = "Some Restaurant",
            category = "eats",
            activity_url = "test.com",
            address = "123 imaginary st",
            summary = "summary1"
        )
        
        a2 = Activity(
            user_id = self.user1_id,
            title = "Some activity",
            category = "outdoor",
            activity_url = "test.com",
            address = "345 imaginary st",
            summary = "summary2"
        )
        
        itinerary.add_activities([a1,a2])
        db.session.commit()

        self.assertEqual(len(self.user1.activities), 2)
        self.assertEqual(len(itinerary.activities), 2)
        # checks that the activities are associated with the correct itinerary
        self.assertEqual(a1.itinerary_id, itinerary.id)
        self.assertEqual(a2.itinerary_id, itinerary.id)
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
        
    def test_missing_title(self):
        """Tests the that the itinerary raises an exception when the title is not added."""
        itinerary = Itinerary(
            location = "some place",
            user_id = self.user1_id,
            radius = 20,
            notes = "a note"
        )
        itinerary.id = 88
        db.session.add(itinerary)
        with self.assertRaises(Exception):
            db.session.commit()
        db.session.commit()
    
    def test_missing_title(self):
        """Tests that the itinerary raises an exception when the title is not added."""
        itinerary = Itinerary(
            location = "some place",
            user_id = self.user1_id,
            radius = 20,
            notes = "a note"
        )
        itinerary.id = 88
        db.session.add(itinerary)
        with self.assertRaises(Exception):
            db.session.commit()
            
    def test_missing_location(self):
        """Tests that the itinerary raises an exception when the location is not added."""
        itinerary = Itinerary(
            title = "test title",
            user_id = self.user1_id,
            radius = 20,
            notes = "a note"
        )
        itinerary.id = 903
        db.session.add(itinerary)
        with self.assertRaises(Exception):
            db.session.commit()
            
    def test_missing_radius(self):
        """Tests that the itinerary raises an exception when the radius is not added."""
        itinerary = Itinerary(
            title = "test title",
            location = "some place",
            user_id = self.user1_id,
            notes = "a note"
        )
        itinerary.id = 993
        db.session.add(itinerary)
        with self.assertRaises(Exception):
            db.session.commit()
            
    def test_missing_user(self):
        """Tests that the itinerary raises an exception when the radius is not added."""
        itinerary = Itinerary(
            title = "test title",
            location = "some place",
            radius = 20,
            notes = "a note"
        )
        itinerary.id = 555
        db.session.add(itinerary)
        with self.assertRaises(Exception):
            db.session.commit()
        
    def test_invalid_user(self):
        """Tests that the itinerary raises an exception when an invalid user id is used"""
        itinerary = Itinerary(
            title = "test title",
            location = "some place",
            user_id = 9323423,
            radius = 87,
            notes = "a note"
        )
        itinerary.id = 23
        db.session.add(itinerary)
        with self.assertRaises(Exception):
            db.session.commit()
        
    def test_repr(self):
        """Tests the repr method"""
        itinerary = Itinerary(
            title = "test itinerary",
            location = "place",
            user_id = self.user1_id,
            radius = 20,
            notes = "to do in some place"
        )
        
        self.itinerary_id = 43
        itinerary.id = self.itinerary_id
        
        db.session.add(itinerary)
        db.session.commit()
        
        
        repr_str = repr(itinerary)
        self.assertEqual(repr_str, f"Itinerary(id = {self.itinerary_id}, ownerId = {self.user1_id})")