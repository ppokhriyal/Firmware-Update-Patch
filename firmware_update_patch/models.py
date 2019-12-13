from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from firmware_update_patch import db, login_manager, app
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
        return User.query.get(int(user_id))


class User(db.Model,UserMixin):
        id = db.Column(db.Integer,primary_key=True)
        username = db.Column(db.String(20),unique=True,nullable=False)
        email = db.Column(db.String(120),unique=True,nullable=False)
        password = db.Column(db.String(60),nullable=False)
        patch = db.relationship('Patch',backref='author',lazy=True,cascade='all,delete-orphan')

        def __repr__(self):
                return f"User('{self.username}','{self.email}','{self.password}')"


class Patch(db.Model):
        id = db.Column(db.Integer,primary_key=True)
        patchgenid = db.Column(db.Integer,unique=True,nullable=False)
        patchname = db.Column(db.String(100),nullable=False)
        date_posted = db.Column(db.DateTime(),nullable=False,default=datetime.utcnow)
        discription = db.Column(db.Text,nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

        def __repr__(self):
                return f"Post('{self.patchgenid}','{self.patchname}','{self.discription}')"