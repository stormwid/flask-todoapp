from datetime import datetime
from sqlalchemy import Date
from hashlib import md5
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import base64
from datetime import timedelta
import os

# Bis auf Verbindung zu task_lists und shared_task_lists von Microblog uebernommen und nicht benoetigtes (Follow, Post Funktionen) entfernt
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    task_list = db.relationship('TaskList', backref='user', uselist=False)
    shared_task_lists = db.relationship('SharedTaskList', backref='shared_with', lazy='dynamic')
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    # Der aktuelle API-Token in der Datenbank
    token = db.Column(db.String(32), index=True, unique=True) 
    # Das Ablaufdatum des Token in der Datenbank
    token_expiration = db.Column(db.DateTime) 

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)
    
    # Token erzeugen, speichern und zurückgeben
    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
        # Token existiert und ist noch nicht abgelaufen
            return self.token
        # Falls der Token nicht existiert oder abgelaufen ist, wird
        # ein zufälliger String erzeugt und base64-kodiert
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token
    
    # Token ungültig machen
    def revoke_token(self):
        # Ablaufdatum auf aktuelle Zeit - 1 sek. setzen
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    # Token prüfen
    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None # Token nicht gefunden oder abgelaufen
        return user # Token ist gültig

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

# Klasse fuer Taskliste, Beziehungen zu besitzendem Benutzer, zugehoerigen Tasks und zu SharedTaskList
class TaskList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tasks = db.relationship('Task', backref='task_list', lazy='dynamic')
    shared_task_lists = db.relationship('SharedTaskList', backref='task_list', lazy='dynamic')

# Klasse für Tasks mit benoetigten Informationen, Beziehungen zur dazugehoerigen Taskliste
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140))
    description = db.Column(db.String(1000))
    status = db.Column(db.String(64)) 
    creation_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, index=True, nullable=True)
    task_list_id = db.Column(db.Integer, db.ForeignKey('task_list.id'))

    # Erstellt ein dictionary mit Informationen zu einem Task. Wir fuer die API Abfrage benoetigt
    def to_dict(self):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.strftime('%d/%m/%Y'),
            'status': self.status
        }
        return data

# Klasse um die Beziehung abzubilden, welche entsteht wenn ein Benutzer einem anderen Benutzer seine Taskliste teilt. 
class SharedTaskList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_list_id = db.Column(db.Integer, db.ForeignKey('task_list.id'))
    shared_with_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # Wird stand jetzt nicht verwendet. Koennte fuer eine Erweiterung benutzt werden bei der mit einem geteilte Tasklisten nicht nur Read Only sind.
    read_only = db.Column(db.Boolean, default=True)