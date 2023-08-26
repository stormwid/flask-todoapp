from app import app, db
from app.models import User, Task, TaskList, SharedTaskList
#Von microblog uebernommen und an Modell angepasst

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Task': Task, 'TaskList': TaskList, 'SharedTaskList': SharedTaskList}
