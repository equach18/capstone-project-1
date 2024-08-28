"""Itinerary view tests."""

# FLASK_ENV=production python3 -m unittest tests/test_itinerary_views.py


import os
from unittest import TestCase

from models import db, connect_db, User, Activity, Itinerary

os.environ['DATABASE_URL'] = "postgresql:///spontinerary-test"


from app import app, CURR_USER_KEY
app.app_context().push()

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class ItineraryViewTestCase(TestCase):
    """Test views for itinerary."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.client = app.test_client()
      
        user1 = User.register(
            email="user1@test.com",
            username="user1",
            password="testpw1",
            image_url=None
        )
        self.user1_id = 34576
        user1.id = self.user1_id
        db.session.commit()
        
        self.user1 = User.query.get(self.user1_id)
        
        i1 = Itinerary(
            title = "test itinerary",
            location = "some place",
            user_id = self.user1_id,
            radius = 20,
            notes = "to do in some place"
        )
        
        self.i1_id = 2453
        i1.id = self.i1_id
        
        db.session.add(i1)
        db.session.commit()
        
        self.i1 = Itinerary.query.get(self.i1_id)
        


    def tearDown(self):
        """Clean up any fouled transactions"""
        res = super().tearDown()
        db.session.rollback()
        return res
    
    def test_create_itinerary(self):
        """Tests creating a new itinerary with valid data"""
        with self.client as client:
            # log the user on 
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1_id
            
            response = self.client.post('/itinerary/new', data={
                'title': 'Test Itinerary',
                'location': 'Test Location',
                'radius': '10',
                'notes': 'Test note'
            }, follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Test Itinerary', response.data)  # Check that the itinerary title is in the response

            # retrieve the itinerary
            itinerary = Itinerary.query.filter_by(title='Test Itinerary').first()
            
            # Verify that the itinerary was added to the database
            self.assertIsNotNone(itinerary)
            self.assertEqual(itinerary.location, 'Test Location')
            self.assertEqual(itinerary.radius, 10000)  
            self.assertEqual(itinerary.notes, 'Test note')
            self.assertEqual(itinerary.user_id, self.user1_id)
        
    def test_create_itinerary_missing_title(self):
        """Test that creating an itinerary fails if the user doesnt add a title."""
        with self.client as client:
            # log the user on 
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1_id
            
            response = self.client.post('/itinerary/new', data={
                'title': '',
                'location': 'Test Location',
                'radius': '10',
                'notes': 'Test note'
            }, follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Please fill in the required fields', response.data) 

            # retrieve the itinerary
            itinerary = Itinerary.query.filter_by(title='Test Itinerary').first()
            
            # Verify that the itinerary was not added to the database
            self.assertIsNone(itinerary)
            
    def test_create_itinerary_no_user(self):
        """Test that an itinerary cannot be created if a user is not logged in."""
        with self.client as client:
            response = self.client.get('/itinerary/new', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Login', response.data)
            self.assertIn(b'Access unauthorized. Please log in to continue.', response.data)
            
    def test_show_itinerary(self):
        """Tests the itinerary page is being rendered correctly for a logged in user"""
        # add activities to i1
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
        
        self.i1.add_activities([a1,a2])
        db.session.commit()
        
        with self.client as client:
            # log the user on 
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1_id
            
            response = self.client.get(f"/itinerary/{self.i1_id}")

            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Add Activities!', response.data) 
            self.assertIn(self.i1.title.encode('utf-8'), response.data) 
            # check that the activities are rendered
            self.assertIn(a1.title.encode('utf-8'), response.data) 
            self.assertIn(a2.title.encode('utf-8'), response.data) 
            self.assertIn(a1.address.encode('utf-8'), response.data) 
            self.assertIn(a2.address.encode('utf-8'), response.data) 
            self.assertIn(a1.summary.encode('utf-8'), response.data) 
            self.assertIn(a2.summary.encode('utf-8'), response.data) 
            self.assertIn(a1.category.encode('utf-8'), response.data) 
            self.assertIn(a2.category.encode('utf-8'), response.data) 

            
    def test_delete_itinerary(self):
        """Tests that the itinerary is sucessfully deleted when the user is logged in"""
        
        itinerary = Itinerary(
            title = "itinerary34",
            location = "some place",
            user_id = self.user1_id,
            radius = 20,
            notes = "to do in some place"
        )
        db.session.add(itinerary)
        db.session.commit() 
        
        a1 = Activity(
            user_id = self.user1_id,
            title = "Some Restaurant",
            category = "eats",
            activity_url = "test.com",
            address = "123 imaginary st",
            summary = "summary1"
        )
        itinerary.add_activities([a1])
        
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
                
            resp = c.post(f"/itinerary/{itinerary.id}/delete", follow_redirects=True)
            
            self.assertEqual(resp.status_code, 200)
            itn = Itinerary.query.get(itinerary.id)
            self.assertIsNone(itn)
            
            # test the activities associated with the itinerary are also deleted from the db
            act = Activity.query.get(a1.id)
            self.assertIsNone(act)
            
    def test_delete_itinerary_no_user(self):
        """Tests that the itinerary cannot be deleted when no user is logged in"""
        
        itinerary = Itinerary(
            title = "itinerary34",
            location = "some place",
            user_id = self.user1_id,
            radius = 20,
            notes = "to do in some place"
        )
        db.session.add(itinerary)
        db.session.commit() 
        
        with self.client as c:
            resp = c.post(f"/itinerary/{itinerary.id}/delete", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            # Checks that the itinerary has not been deleted 
            itn = Itinerary.query.get(itinerary.id)
            self.assertIsNotNone(itn)
            # Checks that access unauthorized flash msg is shown
            self.assertIn(b'Access unauthorized.', resp.data)
            # Check that there are still two itineraries
            self.assertEqual(len(Itinerary.query.all()), 2)
            
    def test_delete_itinerary_invalid_user(self):
        """Tests that the itinerary cannot be deleted by another user"""
        # create a new user
        user2 = User.register(
            email="user2@test.com",
            username="user2",
            password="testpw2",
            image_url=None
        )
        db.session.commit()
        
        with self.client as c:
            with c.session_transaction() as sess:
                # login user2
                sess[CURR_USER_KEY] = user2.id
        
            resp = c.post(f"/itinerary/{self.i1_id}/delete", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            # Checks that the msg has not been deleted 
            itn = Itinerary.query.get(self.i1_id)
            self.assertIsNotNone(itn)
            # Checks that access unauthorized flash msg is shown
            self.assertIn(b'Access unauthorized.', resp.data)
            # Check that the itinerary is not deleted
            self.assertEqual(len(Itinerary.query.all()), 1)
            
            
            