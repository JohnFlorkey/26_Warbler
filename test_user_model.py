"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
import sqlalchemy
from unittest import TestCase
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
os.environ['FLASK_ENV'] = "production"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test user model."""

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

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr(self):
        """Does the repr function work as expected"""

        user1_repr = repr(self.user1)

        self.assertIn(f'{self.user1.id}: user1, user1@nodomain.com', user1_repr)

    def test_is_following_true(self):
        """Does the is_following function correctly detect when user1 is following user2"""

        # create the user1 follows user2 relationship
        db.session.add(Follows(user_being_followed_id=self.user2.id, user_following_id=self.user1.id))
        db.session.commit()

        self.assertTrue(self.user1.is_following(self.user2))

    def test_is_following_false(self):
        """Does the is_following function correctly detect when user1 is not following user2"""

        # no additional data to stage
        self.assertFalse(self.user1.is_following(self.user2))

    def test_is_followed_by_true(self):
        """Does the is_followed_by function correctly detect when user1 is followed by user2"""

        # create the relationship where user 2 follows user 1
        db.session.add(Follows(user_being_followed_id=self.user1.id, user_following_id=self.user2.id))
        db.session.commit()

        self.assertTrue(self.user1.is_followed_by(self.user2))

    def test_is_followed_by_false(self):
        """Does the is_followed_by function correctly detect when yser1 us not followed by user2"""

        # no additional data to stage
        self.assertFalse(self.user1.is_followed_by(self.user2))

    def test_user_signup(self):
        """Does the signup class method create a user when given valid input"""

        new_user = User.signup(username="user3", email="user3@nodomain.com", password="password3", image_url="")
        db.session.commit()

        self.assertIsInstance(new_user, User)
        self.assertIs(type(new_user.id), int)

    def test_user_signup_duplicate_username(self):
        """Does the signup class method not create a user if the username already exists"""

        User.signup(username="user1", email="user3@nodomain.com", password="password3", image_url="")
        self.assertRaises(sqlalchemy.exc.IntegrityError, db.session.commit)

    def test_user_signup_duplicate_email(self):
        """Does the signup class method not create a user if the email already exists"""

        User.signup(username="user3", email="user1@nodomain.com", password="password3", image_url="")
        self.assertRaises(sqlalchemy.exc.IntegrityError, db.session.commit)

    def test_user_authenticate(self):
        """
        Does the authenticate class method return the user when passed valid credentials.
        Relies on the signup class method to create the user and hashed password.
        """

        new_user = User.signup(username="user3", email="user3@nodomain.com", password="password3", image_url="")
        db.session.commit()

        auth_user = User.authenticate(username="user3", password="password3")

        self.assertIsInstance(auth_user, User)
        self.assertEqual(new_user.id, auth_user.id)

    def test_user_authenticate_invalid_username(self):
        """Does the authenticate class method return false when passed an invalid username."""

        User.signup(username="user3", email="user3@nodomain.com", password="password3", image_url="")
        db.session.commit()

        auth_user = User.authenticate(username="notauser", password="password3")

        self.assertFalse(auth_user)

    def test_user_authenticate_invalid_password(self):
        """Does the authenticate class method return false when passed an invalid username."""

        User.signup(username="user3", email="user3@nodomain.com", password="password3", image_url="")
        db.session.commit()

        auth_user = User.authenticate(username="user3", password="wrong_password")

        self.assertFalse(auth_user)
