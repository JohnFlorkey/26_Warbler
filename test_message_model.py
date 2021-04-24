"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from datetime import datetime

import sqlalchemy
from unittest import TestCase

from sqlalchemy import func

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


class TestMessageModel(TestCase):
    """Test message model."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        # create a user
        user1 = User(username="user1", password="password1", email="user1@nodomain.com")
        db.session.add(user1)
        db.session.commit()

        self.user1 = user1

        # create a message for user1
        message_user1 = Message(text="User1 warble.", timestamp=None, user_id=self.user1.id)
        db.session.add(message_user1)
        db.session.commit()

        self.message_user1 = message_user1

        self.client = app.test_client()

    def tearDown(self):
        """Rollback any open transactions"""

        db.session.rollback()

    def test_create_message(self):
        """Is a message successfully created given valid input"""

        new_message = Message(text="This is a test warble.", timestamp=None, user_id=self.user1.id)
        db.session.add(new_message)
        db.session.commit()
        self.assertIsInstance(new_message, Message)
        self.assertIs(type(new_message.id), int)
        self.assertIs(type(new_message.timestamp), datetime)

    def test_create_message_invalid_user(self):
        """Does a message fail to create when given an invalid user_id"""

        max_user = db.session.query(func.max(User.id)).scalar()
        new_message = Message(text="This is a warble.", timestamp=None, user_id=max_user+1)
        db.session.add(new_message)
        self.assertRaises(sqlalchemy.exc.IntegrityError, db.session.commit)

    def test_message_cascade_delete(self):
        """Are all messages authored by a user deleted when the user is deleted."""

        # get user1.id
        user1_id = self.user1.id

        # delete user1
        db.session.delete(self.user1)

        # get user1 messages, should be empty
        user1_messages = Message.query.filter_by(user_id=user1_id).all()

        self.assertFalse(user1_messages)