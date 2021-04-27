"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows, Likes

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

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_add_message_post_logged_in(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_message_get_not_logged_in(self):
        """A user who is not logged in should be redirected to the root route"""

        with self.client as c:
            resp = c.get('/messages/new')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

    def test_add_message_get_logged_in(self):
        """A user who is logged in should get the create message form on a successful get request"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/messages/new')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('placeholder="What', html)

    def test_add_message_post_not_logged_in(self):
        """A user who is not logged in should be redirected to the root route."""

        with self.client as c:
            resp = c.post('/messages/new')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

    def test_message_show(self):
        """show specific message"""

        message = Message(text='Test message.', user_id=self.testuser.id)
        db.session.add(message)
        db.session.commit()

        with self.client as c:
            resp = c.get(f'/messages/{message.id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Test message.', html)

    def test_message_destroy_logged_in(self):
        """A logged in user should be able to delete their own message."""

        message = Message(text='Test message.', user_id=self.testuser.id)
        db.session.add(message)
        db.session.commit()

        message_id = message.id
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f'/messages/{message_id}/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('Test message.', html)

    def test_message_destroy_not_logged_in(self):
        """A user who is not logged in should not be able to delete a message."""

        message = Message(text='Test message.', user_id=self.testuser.id)
        db.session.add(message)
        db.session.commit()

        message_id = message.id
        with self.client as c:

            resp = c.post(f'/messages/{message_id}/delete')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

    def test_message_like_logged_in(self):
        """A logged in user should be able to like a message."""

        user1 = User(username="user1", password="password1", email="user1@nodomain.com")
        db.session.add(user1)
        db.session.commit()

        message = Message(text='Like me.', user_id=user1.id)
        db.session.add(message)
        db.session.commit()

        follow = Follows(user_being_followed_id=user1.id, user_following_id=self.testuser.id)
        db.session.add(follow)
        db.session.commit()

        message_id = message.id
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f'/users/add_like/{message_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('btn-primary', html)

    def test_message_like_logged_in_already_liked(self):
        """A logged in user should be able to stop liking a message."""

        user1 = User(username="user1", password="password1", email="user1@nodomain.com")
        db.session.add(user1)
        db.session.commit()

        message = Message(text='Like me.', user_id=user1.id)
        db.session.add(message)
        db.session.commit()

        follow = Follows(user_being_followed_id=user1.id, user_following_id=self.testuser.id)
        db.session.add(follow)
        db.session.commit()

        like = Likes(user_id=self.testuser.id, message_id=message.id)
        db.session.add(like)
        db.session.commit()

        message_id = message.id
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f'/users/add_like/{message_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('btn-primary', html)

    def test_message_like_logged_in_authored(self):
        """A logged in user cannot like a message they authored."""

        message = Message(text='Like me.', user_id=self.testuser.id)
        db.session.add(message)
        db.session.commit()

        message_id = message.id
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f'/users/add_like/{message_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('btn-primary', html)

    def test_message_like_not_logged_in(self):
        """A user who is not logged in cannot like a message."""

        message = Message(text='Like me.', user_id=self.testuser.id)
        db.session.add(message)
        db.session.commit()

        message_id = message.id
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f'/users/add_like/{message_id}')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

    def test_homepage_logged_in(self):
        """A logged in user should see messages they authored and users they follow author."""

        user1 = User(username="user1", password="password1", email="user1@nodomain.com")
        db.session.add(user1)
        db.session.commit()

        message = Message(text='Like me.', user_id=user1.id)
        db.session.add(message)
        db.session.commit()

        follow = Follows(user_being_followed_id=user1.id, user_following_id=self.testuser.id)
        db.session.add(follow)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Like me.', html)

    def test_homepage_not_logged_in(self):
        """A user who is not logged in should see the signup/login screen."""

        with self.client as c:
            resp = c.get('/')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>', html)
