# capstone-project-1

Spontinerary is a web application used to generate random itineraries based on a user's input of what category of activity they would like. 

Check it out here: https://spontinerary.onrender.com

Users can create a personalized itineraries by specifying the location of their itinerary and how far they are willing to travel. The app uses the Google Maps API to help users select the location. Once the user creates an itinerary, they can add activities based on the categories they choose. The app uses Google Places API to fetch a random place based on the user's  preference and location. The user is able to store multiple itineraries with different activities, allowing multiple plans. The website is designed for users to try random places and activities that they would not have known about otherwise.

App features include:
-Multiple users, allowing personalized itineraries and easy access.
-Creating personalized itineraries, which the user enters the location they want their itinerary to be at and the radius they are willing to travel
-Adding activities to itineraries, which is done by selecting a category. A random place is picked from the Google Places API response and added as an activity to the itinerary. 
-The activity will give a description (if found from the Google API), link, and address of the location
-Viewing all user's activities
-Deletion of the user's itinerary and/or activities 

Resources:
-Bootstrap
-w3schools

APIs:
-Google Maps API
-Google Places API 

Technology:
-Python 3.12.3
-Flask-SQLAlchemy
-JavaScript
-CSS
-Postgres
-WTForms
-Supabase
-Render
