# -*- coding: utf-8 -*-

import os
import sys
from os import path

deps_paths = [
    path.join(path.split(path.realpath(__file__))[0], 'deps'), 
    path.join(path.split(path.realpath(__file__))[0], 'mydeps'),
]

for deps_path in deps_paths:
    if deps_path not in sys.path:
        sys.path.insert(0, deps_path)

from app import create_app, db, get_appconfig
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask import send_from_directory

# bae, sae, production, local(default)
app = create_app(os.getenv('APP_CONFIG') or str(get_appconfig()) or 'default')

manager = Manager(app)
migrate = Migrate(app, db)

manager.add_command('db', MigrateCommand)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@manager.command
def deploy():
    """Run deployment tasks."""
    from flask.ext.migrate import upgrade
    from app.models import Role, User

    upgrade()
    #db.create_all()

    # create user roles
    Role.insert_roles()


if __name__ == '__main__':
    manager.run()
