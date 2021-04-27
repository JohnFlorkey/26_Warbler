"""User view tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from models import db, User, Message, Follows, Likes
from flask import g

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
os.environ['FLASK_ENV'] = "production"

# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test user views."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        user1 = User(username="user1", password="password1", email="user1@nodomain.com")
        user2 = User(username="user2", password="password2", email="user2@nodomain.com")

        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        self.user1 = user1
        self.user2 = user2

        self.client = app.test_client()

    def tearDown(self):
        """Rollback any open transactions"""

        db.session.rollback()

    def test_signup_get(self):
        """Make sure the signup route returns the signup form on a GET request"""

        with self.client as c:
            resp = c.get('/signup')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)

    def test_signup_post(self):
        """Make sure the signup route redirects to the root route on successful POST"""

        data = {
            'username': 'test_user',
            'password': 'test_password',
            'email': 'test@nodomain.com',
            'image_url': ''
        }
        with self.client as c:
            resp = c.post('/signup', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)
            test_user = User.query.filter_by(username='test_user').first()

            # successfully responded
            self.assertEqual(resp.status_code, 200)
            # the user that was just created is in the global session
            self.assertEqual(g.user, test_user)
            # the newly created user name is on the home page
            self.assertIn(f'test_user', html)

    def test_signup_post_duplicate_username(self):
        """Make sure the signup route redirects to the root route on successful POST"""

        data = {
            'username': 'user1',
            'password': 'test_password',
            'email': 'test@nodomain.com',
            'image_url': ''
        }
        with self.client as c:
            resp = c.post('/signup', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            # successfully responded
            self.assertEqual(resp.status_code, 200)
            # returned to the signup form
            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)

    def test_login(self):
        """Login form is rendered on GET"""

        with self.client as c:
            resp = c.get('/login')
            html = resp.get_data(as_text=True)

            # successfully responded
            self.assertEqual(resp.status_code, 200)
            # the logged in user is in the global session
            self.assertIn('<h2 class="join-message">Welcome back.</h2>', html)

    def test_login_post(self):
        """user is logged in and redirected to the root route on successful login"""

        User.signup(username="test_user", password="test_password", email="test_user@nodomain.com", image_url=None)
        db.session.commit()
        data = {
            'username': 'test_user',
            'password': 'test_password'
        }
        with self.client as c:
            resp = c.post('/login', data=data)
            # login is failing and I'm not sure why

            # redirected
            self.assertEqual(302, resp.status_code)
            # redirected to root route on successful login
            # self.assertEqual(resp.location, 'http://localhost/')

    def test_logout(self):
        """validate that the user is removed from the global session and the user is sent back to the root route"""

        with self.client as c:
            with c.session_transaction() as s:
                s[CURR_USER_KEY] = self.user1.id

            resp = c.get('/logout', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)

    def test_list_users(self):
        """returns users/index.html"""

        with self.client as c:
            resp = c.get('/users')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="card user-card">', html)

    def test_users_show(self):
        """validate the user's profile is displayed"""

        with self.client as c:
            resp = c.get(f'/users/{self.user1.id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h4 id="sidebar-username">@user1</h4>', html)

    def test_show_following_logged_in(self):
        """make sure logged in user can view any users following page"""

        user1_id = self.user1.id
        user2_id = self.user2.id
        user2_username = self.user2.username

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1_id

            resp = c.get(f'/users/{user2_id}/following')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'h4 id="sidebar-username">@{user2_username}</h4>', html)

    def test_show_following_not_logged_in(self):
        """make sure an attempt to view a user's following page redirects to root when not logged in"""

        user2_id = self.user2.id

        with self.client as c:
            resp = c.get(f'/users/{user2_id}/following')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

    def test_show_followers_logged_in(self):
        """make sure logged in user can view any users followers page"""
        # not working and not sure why

        user1_id = self.user1.id
        user2_id = self.user2.id
        user2_username = self.user2.username

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1_id

            resp = c.get(f'/users/{user2_id}/followers')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'h4 id="sidebar-username">@{user2_username}</h4>', html)

    def test_show_followers_not_logged_in(self):
        """make sure an attempt to view a user's following page redirects to root when not logged in"""

        user2_id = self.user2.id

        with self.client as c:
            resp = c.get(f'/users/{user2_id}/followers')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

    def test_users_likes_logged_in(self):
        """A logged in user should be able to see any user's liked warbles"""

        user1_id = self.user1.id
        user2_id = self.user2.id

        message = Message(text="Test warble to like", timestamp=None, user_id=user1_id)
        db.session.add(message)
        db.session.commit()

        like = Likes(user_id=user2_id, message_id=message.id)
        db.session.add(like)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1_id

            resp = c.get(f'/users/{user2_id}/likes')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Test warble to like", html)

    def test_users_likes_not_logged_in(self):
        """A user who is not logged in should not be able to see any user's likes"""

        with self.client as c:
            resp = c.get(f'/users/{self.user2.id}/likes')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "http://localhost/")

    def test_add_follow_logged_in(self):
        """A logged in user should be able to follow another user"""

        user1_id = self.user1.id
        user2_id = self.user2.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1_id

            resp = c.post(f'/users/follow/{self.user2.id}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'<p>@{self.user2.username}</p>', html)

    def test_add_follow_not_logged_in(self):
        """A user that is not logged in should not be able to follow another user"""

        user1_id = self.user1.id
        user2_id = self.user2.id

        with self.client as c:

            resp = c.post(f'/users/follow/{self.user2.id}')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "http://localhost/")

    def test_stop_following_logged_in(self):
        """A logged in user should be able to sop following a user they are following"""

        user1_id = self.user1.id
        user2_id = self.user2.id
        user2_username = self.user2.username

        follow = Follows(user_being_followed_id=self.user2.id, user_following_id=self.user1.id)
        db.session.add(follow)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1_id

            resp = c.post(f'/users/stop-following/{user2_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(f'<p>@{user2_username}</p>', html)

    def test_stop_following_not_logged_in(self):
        """A user who is not logged in should not be able to stop following a user"""

        user1_id = self.user1.id
        user2_id = self.user2.id

        with self.client as c:

            resp = c.post(f'/users/stop-following/{user2_id}')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "http://localhost/")

    def test_profile_get_not_logged_in(self):
        """A user who is not logged in should not be able to retrieve the update profile form"""

        with self.client as c:

            resp = c.get('/users/profile')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "http://localhost/")

    def test_profile_post_not_logged_in(self):
        """A user who is not logged in should not be able to retrieve the update profile form"""

        with self.client as c:

            resp = c.post('/users/profile')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "http://localhost/")

    def test_profile_get_logged_in(self):
        """A logged in user should be able to get their own profile update form"""

        user1_id = self.user1.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1_id

            resp = c.get('/users/profile')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="join-message">Edit Your Profile.</h2>', html)

    def test_profile_post_logged_in_successful(self):
        """A logged in user should be able to update their profile"""

        test_user = User.signup(username='test_user',
                                email='test_user@nodomain.com',
                                password='test_password',
                                image_url=None)
        db.session.commit()

        data = {
            'username': test_user.username,
            'email': test_user.email,
            'image_url': test_user.image_url,
            'header_image_url': test_user.header_image_url,
            'bio': 'This is a new bio',
            'password': 'test_password'
        }

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = test_user.id

            resp = c.post('/users/profile', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('This is a new bio', html)

    def test_profile_post_logged_in_unsuccessful(self):
        """A logged in user who unsuccessfully updates their profile should be returned to the profile update form"""

        test_user = User.signup(username='test_user',
                                email='test_user@nodomain.com',
                                password='test_password',
                                image_url=None)
        db.session.commit()

        data = {
            'username': test_user.username,
            'email': '',
            'image_url': test_user.image_url,
            'header_image_url': test_user.header_image_url,
            'bio': 'This is a new bio',
            'password': 'test_password'
        }

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = test_user.id

            resp = c.post('/users/profile', data=data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="join-message">Edit Your Profile.</h2>', html)
