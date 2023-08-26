# app/api.py
from flask import jsonify, abort
from app import app, db
from app.models import User, Task, TaskList
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from app.errors import error_response
#Von Microblog uebernommen, ab Linie 38 neuer eigener Code
basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()

@app.route('/api/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
 token = basic_auth.current_user().get_token()
 db.session.commit()
 return jsonify({'token': token})

# Hilfs-Funktionen für HTTPAuth

@basic_auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return user

@basic_auth.error_handler
def basic_auth_error(status):
    return error_response(status)

@token_auth.verify_token
def verify_token(token):
    return User.check_token(token) if token else None

@token_auth.error_handler
def token_auth_error(status):
    return error_response(status)

# API-Endpunkt um user ID vom username zu bekommen, was fuer die anderen API Anfragen wichtig zu wissen ist.
@app.route('/api/getuserid/<string:username>', methods=['GET'])
@token_auth.login_required
def get_user_id(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify(error="User not found"), 404
    return jsonify(user_id=user.id)

# API-Endpunkt Route um offene Tasks des angemeldeten Benutzers abzufragen
@app.route('/api/users/<int:id>/tasks/open', methods=['GET'])
@token_auth.login_required
def get_open_tasks(id):
    user = User.query.get_or_404(id)
    
    # Ueberpruefen, dass der angemeldete Benutzer keine Daten von einem anderen Benutzer anfraegt
    if token_auth.current_user().id != id:
        abort(403)
    # Fragt Taskliste und Tasks des Benutzers mit Status open ab
    task_list = TaskList.query.filter_by(user_id=id).first()
    tasks = Task.query.filter_by(task_list_id=task_list.id, status='open').all()

    # Speichert Daten aus Abfrage in einem dictionary und beantwortet die Anfrage mit JSON
    data = [task.to_dict() for task in tasks]
    return jsonify(data)

# Macht das gleiche wie oben einfach fuer completed Tasks
@app.route('/api/users/<int:id>/tasks/completed', methods=['GET'])
@token_auth.login_required
def get_completed_tasks(id):
    user = User.query.get_or_404(id)
    
    if token_auth.current_user().id != id:
        abort(403)
    
    task_list = TaskList.query.filter_by(user_id=id).first()
    tasks = Task.query.filter_by(task_list_id=task_list.id, status='completed').all()
    
    data = [task.to_dict() for task in tasks]
    return jsonify(data)