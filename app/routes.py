from datetime import datetime
from flask import render_template, flash, redirect, url_for, session, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, \
    TaskForm, EditTaskForm, ShareTaskListForm
from app.models import User, Task, TaskList, SharedTaskList

# Vom Microblog sind die Routen fuer Login, Logout, Register, Userprofil, Userprofil bearbeiten uebernommen und wo noetig Follow und Post Funktionen entfernt worden
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

# index auf taskliste umleiten
@app.route('/')
def index():
    return redirect(url_for('taskliste'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        # Hizugefuegt damit User nach dem submit wieder auf sein Profil kommt
        return redirect(url_for('user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

# Funktionen fuer Hauptseite. Tasks hinzufügen und Abfragen
@app.route('/taskliste', methods=['GET', 'POST'])
@login_required
def taskliste():
    task_form = TaskForm()

    if task_form.validate_on_submit():
        # Pruefen, ob der Benutzer eine Aufgabenliste hat und eine erstellen wenn nicht
        task_list = current_user.task_list
        if task_list is None:
            print("Creating task list")
            task_list = TaskList(user=current_user)
            db.session.add(task_list)
            db.session.commit()
        
        task = Task(title=task_form.title.data,
                    description=task_form.description.data,
                    due_date=task_form.due_date.data,
                    status='open')

        # Hinzufuegen der Aufgabe zur Aufgabenliste
        task_list.tasks.append(task)
        # Die Aufgabe zur Datenbanksitzung hinzufuegen
        db.session.add(task)
        # Aenderungen bestaetigen
        db.session.commit()

        flash('Your task has been added!')
        return redirect(url_for('taskliste'))

    
    # Holt Tasks des Benutzers und checkt ob in der Session bereits eine Praeferenz fuer den Task Status besteht
    task_view = session.get('task_view', 'open')
    tasks = current_user.task_list.tasks.filter_by(status=task_view).all() if current_user.task_list else []
    

    return render_template('taskliste.html', title='Tasks', task_form=task_form, tasks=tasks)

# Bei einem Task den Status von open zu completed oder umgekehrt aendern
@app.route('/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get(task_id)
    if task and task.task_list.user == current_user:
        task.status = 'open' if session.get('task_view', 'open') == 'completed' else 'completed'
        db.session.commit()
        flash('Task completed successfully!')
    else:
        flash('Task not found or not authorized!')
    return redirect(url_for('taskliste'))

# Einen Task loeschen, checken ob der Task auch dem aktuellen Benutzer gehoert
@app.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task and task.task_list.user == current_user:
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted successfully!')
    else:
        flash('Task not found or not authorized!')
    return redirect(url_for('taskliste'))

# In der eigenen Taskliste aendern ob open oder completed Tasks angezeigt werden sollen
@app.route('/toggle_task_view', methods=['POST'])
@login_required
def toggle_task_view():
    current_view = session.get('task_view', 'open')
    session['task_view'] = 'completed' if session.get('task_view', 'open') == 'open' else 'open'
    return redirect(url_for('taskliste'))

# In der Ansicht von fremden mit einem geteilten Tasklisten aendern ob open oder completed Tasks angezeigt werden sollen
@app.route('/toggle_shared_task_view/<int:tasklist_id>', methods=['POST'])
@login_required
def toggle_shared_task_view(tasklist_id):
    session['shared_task_view'] = 'completed' if session.get('shared_task_view', 'open') == 'open' else 'open'
    return redirect(url_for('view_shared_tasklist', tasklist_id=tasklist_id))

# Um einen bestehenden Task zu bearbeiten
@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Ueberpruefen, ob der aktuelle Benutzer der Besitzer des Tasks ist.
    if task.task_list.user != current_user:
        flash('Not authorized to edit this task!')
        return redirect(url_for('taskliste'))
    
    edit_task_form = EditTaskForm(obj=task)
    if edit_task_form.validate_on_submit():
        task.title = edit_task_form.title.data
        task.description = edit_task_form.description.data
        task.due_date = edit_task_form.due_date.data
        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('taskliste'))
    return render_template('edit_task.html', title='Edit Task', edit_task_form=edit_task_form)

# Teilen / nicht mehr teilen von eigener Aufgabenliste ueber Benutzernamen. 
@app.route('/taskshare', methods=['GET', 'POST'])
@login_required
def taskshare():
    share_task_form = ShareTaskListForm()
    if share_task_form.validate_on_submit():
        user_to_share_with = User.query.filter_by(username=share_task_form.username.data).first()
        
        # Ueberpruefen ob Benutzer existiert und ob man nicht seinen eigenen Namen angegeben hat
        if not user_to_share_with:
            flash('User {} not found.'.format(share_task_form.username.data))
            return redirect(url_for('taskshare'))
        if user_to_share_with == current_user:
            flash('You cannot share tasks with yourself!')
            return redirect(url_for('taskshare'))
        
        # Ueberpruefen ob schon mit dem Benutzer geteilt wurde, damit nicht mehrere DB Eintraege fuer die gleiche Beziehung erstellt werden.
        existing_share = SharedTaskList.query.filter_by(task_list_id=current_user.task_list.id, shared_with_id=user_to_share_with.id).first()
        if existing_share:
            flash('Your task list has already been shared with {}!'.format(share_task_form.username.data))
            return redirect(url_for('taskshare'))
        
        # Wenn alles okay ein entsprechender SharedTaskList Eintrag auf der DB erstellen
        shared_tasklist = SharedTaskList(task_list_id=current_user.task_list.id, shared_with_id=user_to_share_with.id)
        db.session.add(shared_tasklist)
        db.session.commit()
        flash('Your task list has been shared with {}!'.format(share_task_form.username.data))
        return redirect(url_for('taskshare'))
    
    shared_by_me = SharedTaskList.query.filter_by(task_list_id=current_user.task_list.id).all()
    return render_template('taskshare.html', title='Share Task List', share_task_form=share_task_form, shared_by_me=shared_by_me)

# Nicht mehr teilen von eigener Aufgabenliste
@app.route('/unshare_tasklist/<int:user_id>', methods=['GET'])
@login_required
def unshare_tasklist(user_id):
    shared_tasklist = SharedTaskList.query.filter_by(task_list_id=current_user.task_list.id, shared_with_id=user_id).first()
    if shared_tasklist:
        db.session.delete(shared_tasklist)
        db.session.commit()
        flash('Task list unshared with ' + User.query.get(user_id).username)
    else:
        flash('Task list was not shared with this user')
    return redirect(url_for('taskshare'))

# Aufgabenliste abfragen welche mit einem geteilt wurden
@app.route('/shared_tasklists', methods=['GET'])
@login_required
def shared_tasklists():
    shared_with_me = SharedTaskList.query.filter_by(shared_with_id=current_user.id).all()
    return render_template('shared_tasklists.html', shared=shared_with_me)

# Mit einem geteilte Aufgabenliste in einem Read Only Modus anzeigen. Sehr aehnlich wie /taskliste
@app.route('/view_shared_tasklist/<int:tasklist_id>', methods=['GET'])
@login_required
def view_shared_tasklist(tasklist_id):
    tasklist = TaskList.query.get(tasklist_id)
    # Filtert abhaengig von der Session nur open oder completed Tasks
    if session.get('shared_task_view', 'open') == 'completed':
        tasklist.tasks = [task for task in tasklist.tasks if task.status == 'completed']
    else:
        tasklist.tasks = [task for task in tasklist.tasks if task.status == 'open']

    # Ueberprueft ob die Aufgabenliste existiert
    if not tasklist:
        flash('Tasklist not found.', 'danger')
        return redirect(url_for('shared_tasklists'))
    
    # Ueberprueft ob die Aufgabenliste auch mit dem aktuellen Benutzer geteilt wurde. Sonst koennte hier und bei den meisten anderen Funktionen einfach in der URL die ID vom Task oder Taskliste geaendert werden.
    shared_entry = SharedTaskList.query.filter_by(task_list_id=tasklist.id, shared_with_id=current_user.id).first()
    if not shared_entry:
        flash('You do not have permission to view this tasklist.', 'danger')
        return redirect(url_for('shared_tasklists'))
    
    return render_template('view_tasklist.html', tasklist=tasklist)

