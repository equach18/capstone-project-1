"""User model tests."""

#    python3 -m unittest tests/test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Activity, Itinerary, bcrypt

os.environ['DATABASE_URL'] = "postgresql:///spontinerary-test"


from app import app
app.app_context().push()

db.create_all()


class UserModelTestCase(TestCase):
    """Test the User model."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()
        
        # create user1 and 2
        self.user1_id = 345345
        user1 = User.register(
            email="user1@test.com",
            username="user1",
            password="testpw1",
            image_url=None
        )
        user1.id = self.user1_id
        
        self.user2_id = 2233
        user2 = User.register(
            email="user2@test.com",
            username="user2",
            password="testpw2",
            image_url=None
        )
        user2.id = self.user2_id
        
        db.session.commit()
        
        self.user1 = User.query.get(self.user1_id)
        self.user2 = User.query.get(self.user2_id)

        self.client = app.test_client()
    
    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        """Tests the User basic model"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url=None
        )

        db.session.add(u)
        db.session.commit()

        # The new user should have no itineraries nor activities
        self.assertEqual(len(u.itineraries), 0)
        self.assertEqual(len(u.activities), 0)
        
        
    def test_relationships(self):
        """Tests the activity relationship between users"""
        # Create an itinerary for user1
        i1 = Itinerary(
            title="title1",
            location="Chicago",
            user_id = self.user1_id,
            notes = "note1",
            radius = 15
        )
        db.session.add(i1)
        db.session.commit()
        
        # Add activities to the itinerary
        a1 = Activity(
            user_id = self.user1_id,
            title="Some Restaurant",
            category = "eats",
            activity_url = "test.com",
            address = "123 imaginary st"
        )
        
        a2 = Activity(
            user_id = self.user1_id,
            title="Some activity",
            category = "outdoor",
            activity_url = "test.com",
            address = "345 imaginary st"
        )
        
        i1.add_activities([a1,a2])
        db.session.commit()
        
        # checks that the itinerary is only owner by user1
        self.assertEqual(len(self.user1.itineraries), 1)
        self.assertEqual(len(self.user2.itineraries), 0)
        
        # checks that the number of activities for the user is correct.
        self.assertEqual(len(self.user1.activities), 2)
        self.assertEqual(len(self.user2.activities), 0)
        
    
    def test_signup(self):
        """Tests the signup method of User model"""
        
        # create a valid user
        signup_user = User.register(
                username = "signup_tester",
                password = "sign_up_test_pw",
                email="signup_test@test.com",
                image_url=None
        )
        db.session.commit()

        # Retrieve the user from the database
        signup_user = User.query.filter(User.username =="signup_tester").first()
        # checks that all the valid user is created and fields match
        self.assertIsNotNone(signup_user)
        self.assertEqual(signup_user.username, "signup_tester")
        self.assertEqual(signup_user.email, "signup_test@test.com")
        self.assertTrue(bcrypt.check_password_hash(signup_user.password, "sign_up_test_pw"))
    
    def test_signup_missing_username(self):
        """Test signup with missing fields"""
        User.register(
            username=None,
            password="password",
            email="test@test.com",
            image_url="test.png"
        )
        
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
            
    def test_signup_missing_email(self):
        """Test signup with missing email"""
        User.register(
            username="invalid user",
            password="password",
            email=None,
            image_url="test.png"
        )
        
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
            
    def test_signup_duplicate_email(self):
        """Test signup with existing email"""
        User.register(
            username="invalid user",
            password="password",
            email="user1@test.com",
            image_url="test.png"
        )
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
        
    
    def test_authenticate_valid_user(self):
        """Tests that user will be returned when a user is successfully authenticated"""
        authenticated_user = User.authenticate("gooduser", "password1")
        self.assertIsNotNone(authenticated_user)
    
    def test_authenticate_invalid_username(self):
        """Tests that an invalid username will not be authenticated"""
        invalid_user = User.authenticate("invalid_username", "password1")
        self.assertFalse(invalid_user)
        
    def test_authenticate_invalid_password(self):
        """Tests that an invalid password will not be authenticated"""
        invalid_user = User.authenticate("user1", "badpassword")
        self.assertFalse(invalid_user)
        
    def test_repr(self):
        """Tests the repr method"""
        repr_str = repr(self.user1)
        self.assertEqual(repr_str, f"<User #{self.user1.id}: {self.user1.username}>")

    
        
