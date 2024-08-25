"""User View tests."""

# FLASK_ENV=production python3 -m unittest tests/test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, User, Activity, Itinerary

os.environ['DATABASE_URL'] = "postgresql:///spontinerary-test"


from app import app, CURR_USER_KEY
app.app_context().push()

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.client = app.test_client()
      
        self.user1_id = 8456
        user1 = User.register(
            email="user1@test.com",
            username="user1",
            password="testpw1",
            image_url=None
        )
        user1.id = self.user1_id
        db.session.commit()
        
        self.user1 = User.query.get(self.user1_id)


    def tearDown(self):
        """Clean up any fouled transactions"""
        res = super().tearDown()
        db.session.rollback()
        return res
    
    def test_login_page(self):
        """Tests login page renders correctly upon a get request"""
        
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)
    
    def test_successful_login(self):
        """Tests login with valid credentials."""
        response = self.client.post('/login', data={
            'username': 'user1',
            'password': 'testpw1'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hello, user1!', response.data) 
        # logout button is only shown when the user is logged in
        self.assertIn(b'Logout', response.data)
        
    def test_unsuccessful_login(self):
        """Tests login with invalid credentials."""
        response = self.client.post('/login', data={
            'username': 'user1',
            'password': 'invalid_pw'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username and/or password', response.data)
        # checks that the login button is still there if login was unsuccessful
        self.assertIn(b'Login', response.data)
    
    def test_signup_page(self):
        """Tests signup page renders correctly upon a get request"""
        
        response = self.client.get('/signup')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign Up', response.data)
        
    def test_successful_signup(self):
        """Tests signing up with valid credentials"""
        
        response = self.client.post('/signup', data={
            'username': 'user',
            'email': 'user@test.com',
            'password': 'password',
            'image_url': None
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hello, user!', response.data)
        self.assertIn(b'Logout', response.data)
                
            
    def test_signup_duplicate_username(self):
        """Test signing up with a duplicate username."""
        # used the same username created in setup
        response = self.client.post('/signup', data={
            'username': 'user1',  
            'email': 'something@test.com',
            'password': 'password',
            'image_url': None
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # check that the user is not logged in with username that already exists in the db
        self.assertIn(b'Invalid Inputs', response.data) 
        self.assertIn(b'Sign Up', response.data)
        
    def test_signup_duplicate_email(self):
        """Test signing up with a duplicate email."""
        # used the same email created in setup
        response = self.client.post('/signup', data={
            'username': 'user',  
            'email': 'user1@test.com',
            'password': 'password',
            'image_url': None
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # check that the user is not signed up or logged in with dupicate email
        self.assertIn(b'Invalid Inputs', response.data) 
        self.assertIn(b'Sign Up', response.data)
            
    def test_logout(self):
        """Tests logging out the user."""

        with self.client as client:
            # log the user on 
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1_id
            # Log the user out and test routes 
            response = client.get('/logout', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'You have successfully logged out.', response.data) 
            self.assertIn(b'Login', response.data)
            
        # Verify that the user is no longer logged in
        with client.session_transaction() as sess:
            self.assertNotIn(CURR_USER_KEY, sess)
            
    def test_no_user_logout(self):
        """Tests that the user cannot log out without being logged in."""
        
        response = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'Login', response.data) 
        self.assertNotIn(b'You have successfully logged out.', response.data)