"""Activity view tests."""

# FLASK_ENV=production python3 -m unittest tests/test_activity_views.py


import os
from unittest import TestCase
from unittest.mock import patch
import requests

from models import db, connect_db, User, Activity, Itinerary
from app import get_long_lat, process_activities
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')


os.environ['DATABASE_URL'] = "postgresql:///spontinerary-test"


from app import app, CURR_USER_KEY
app.app_context().push()

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class ActivityViewTestCase(TestCase):
    """Test views for Activity."""

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
        self.user1_id = 980
        user1.id = self.user1_id
        db.session.commit()
        
        self.user1 = User.query.get(self.user1_id)
        
        i1 = Itinerary(
            title = "test itinerary",
            location = "600 E Grand Ave, Chicago, IL",
            user_id = self.user1_id,
            radius = 20,
            notes = "to do in some place"
        )
        
        self.i1_id = 23
        i1.id = self.i1_id
        
        db.session.add(i1)
        db.session.commit()
        
        self.i1 = Itinerary.query.get(self.i1_id)
        

    def tearDown(self):
        """Clean up any fouled transactions"""
        res = super().tearDown()
        db.session.rollback()
        return res
    
    @patch('app.requests.get')
    def test_get_long_lat(self, mock_get):
        """Tests get_long_lat successffully returns the longitude and latitude"""
        # create a mock resp data
        mock_resp_data = {
            'status': 'OK',
            'results': [{
                'geometry': {
                    'location': {
                        'lat': 41.892654,
                        'lng': -87.610168
                    }
                }
            }]
        }
        
        # configure mock to match normal returns
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_resp_data

        # check the longitude and latitude
        lat, long = get_long_lat("600 E Grand Ave, Chicago, IL")
        self.assertEqual(lat, 41.892654)
        self.assertEqual(long, -87.610168)

        # Assert that the request was made with the correct URL and parameters
        mock_get.assert_called_once_with(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={'address': "600 E Grand Ave, Chicago, IL", 'key': GOOGLE_MAPS_API_KEY}
        )
        
    @patch('app.requests.get')
    def test_unsuccessful_get_long_lat(self, mock_get):
        """Test that get_long_lat raises an exception when the API call fails."""

        # create a mock resp data and configure the mock
        mock_resp_data = {
            'status': 'ZERO_RESULTS',
            'results': []
        }

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_resp_data

        # Tests that an exception is raised with an invalid address
        with self.assertRaises(Exception) as context:
            get_long_lat("3856374 fake address")

        self.assertIn("Error getting geocode: ZERO_RESULTS", str(context.exception))

        # Assert that the request was made with the correct URL and parameters
        mock_get.assert_called_once_with(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={'address': "3856374 fake address", 'key': GOOGLE_MAPS_API_KEY}
        )
    
    def test_add_activities(self):
        """Tests that the activities are successfully added with the given categories"""
        with self.client as client:
            # log the user on 
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1_id

            categories = ['Food', 'Tours']

            response = client.post(
                f'/itinerary/{self.i1_id}/new',
                json={'categories': categories},
                follow_redirects=True
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['message'], "Activities added successfully")

            # Query the database to ensure activities were added
            user1_activities = Activity.query.filter_by(user_id=self.user1_id).all()
            i1_activities = Activity.query.filter_by(itinerary_id=self.i1.id).all()
            self.assertEqual(len(user1_activities), 2)
            self.assertEqual(len(i1_activities), 2)
        
    def test_add_activity_no_category(self):
        """Tests add_activitty with no category given"""
        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1_id
            
            categories = []
            response = client.post(
                f'/itinerary/{self.i1_id}/new',
                json={'categories': categories},
            )

            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json['error'], "Please select at least one activity category.")
            
            self.assertEqual(len(Activity.query.all()), 0)
            
    def test_add_activity_no_user(self):
        """Test that an activity cannot be added if a user is not logged in."""
        with self.client as client:
            categories = ['Food', 'Tours']

            response = client.post(
                f'/itinerary/{self.i1_id}/new',
                json={'categories': categories},
                follow_redirects=True
            )

            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Access unauthorized. Please log in to continue.", response.data)
            self.assertEqual(len(Activity.query.all()), 0)
            
    def test_add_activity_unauth_user(self):
        """Test that activity cannot be added to an itinerary that is not theirs."""
        # create a new user and log in
        unauthorized_user = User.register(
            email="baduser@test.com",
            username="baduser",
            password="somepw5464",
            image_url=None
        )
        db.session.commit()
        
        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = unauthorized_user.id
            
            categories = ['Food', 'Tours']
            response = client.post(
                f'/itinerary/{self.i1_id}/new',
                json={'categories': categories},
                follow_redirects=True
            )

            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Access unauthorized. You cannot add to another", response.data)
            
            self.assertEqual(len(Activity.query.all()), 0)
            

    def test_show_activities(self):
        """Tests the show activity page is being rendered correctly for a logged in user"""
        i2 = Itinerary(
            title = "test2 itinerary",
            location = "600 E Grand Ave, Chicago, IL",
            user_id = self.user1_id,
            radius = 28,
            notes = "to do in some place"
        )
        
        db.session.add(i2)
        db.session.commit()
        
        # add activities to i1 and i2
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
        
        self.i1.add_activities([a1])
        i2.add_activities([a2])
        db.session.commit()
        
        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1_id
            
            response = self.client.get(f"/activity/all")

            self.assertEqual(response.status_code, 200)
            # check that the activities are rendered
            self.assertIn(a1.title.encode('utf-8'), response.data) 
            self.assertIn(a2.title.encode('utf-8'), response.data) 
            self.assertIn(a1.address.encode('utf-8'), response.data) 
            self.assertIn(a2.address.encode('utf-8'), response.data) 
            self.assertIn(a1.category.encode('utf-8'), response.data) 
            self.assertIn(a2.category.encode('utf-8'), response.data) 
            self.assertIn(self.i1.title.encode('utf-8'), response.data) 
            self.assertIn(i2.title.encode('utf-8'), response.data) 

            
    def test_delete_activity(self):
        """Tests that the activity is sucessfully deleted when the user is logged in"""
        
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
        db.session.commit() 
        a1_id=a1.id
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
                
            resp = c.post(f"/activity/{a1_id}/delete", follow_redirects=True)
            
            self.assertEqual(resp.status_code, 200)
            a1 = Activity.query.get(a1_id)
            self.assertIsNone(a1)
            
            # test that the itineraries are not deleted
            self.assertEqual(len(Itinerary.query.all()), 2)
            
            
            user1_activities = Activity.query.filter_by(user_id=self.user1_id).all()
            i1_activities = Activity.query.filter_by(itinerary_id=self.i1.id).all()
            self.assertEqual(len(user1_activities), 0)
            self.assertEqual(len(i1_activities), 0)
            
            
    def test_delete_itinerary_no_user(self):
        """Tests that the activity cannot be deleted when no user is logged in"""
        
        a1 = Activity(
            user_id = self.user1_id,
            title = "Some Restaurant",
            category = "eats",
            activity_url = "test.com",
            address = "123 imaginary st",
            summary = "summary1"
        )
        a1.id=375634
        self.i1.add_activities([a1])
        db.session.commit() 
        
        with self.client as c:
            resp = c.post(f"/activity/{a1.id}/delete", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            # Checks that the activity has not been deleted 
            act = Activity.query.get(a1.id)
            self.assertIsNotNone(act)
            # Checks that access unauthorized flash msg is shown
            self.assertIn(b'Access unauthorized.', resp.data)
            # Check that the activity is still in the db
            self.assertEqual(len(Activity.query.all()), 1)
            
    def test_delete_itinerary_invalid_user(self):
        """Tests that the activity cannot be deleted by another user"""
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
            
            
            