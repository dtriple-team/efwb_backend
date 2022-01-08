#!/usr/bin/python
# -*- coding: utf-8 -*-
print ("module [manager] loaded")
import sys

from flask_migrate import MigrateCommand
from flask_script import Manager

from backend import app
from backend.db.database import DBManager


manager = Manager(app)
manager.add_command('db', MigrateCommand)

# python manage.py init_db
@manager.command
def init_db():
    if check_message('Are you sure to init database ? (Y/n)') == False:
        return
    """Initialize database."""
    with app.app_context():
        DBManager.init_db()

# python manage.py clear_db
@manager.command
def clear_db():
    if check_message('Are you sure to clear database ? (Y/n)') == False:
        return
    with app.app_context():
        DBManager.clear_db()

# python manage.py insert_data
@manager.command
def insert_data():
    if check_message('Are you sure to insert data ? (Y/n)') == False:
        return
    with app.app_context():
        DBManager.insert_dummy_data()

@manager.command
def add_server():
    if check_message('Are you sure to add_server ? (Y/n)') == False:
        return
    with app.app_context():
        DBManager.insert_dummy_server()

@manager.command
def add_walkrun():
    if check_message('Are you sure to walk run table ? (Y/n)') == False:
        return
    with app.app_context():
        DBManager.insert_dummy_walkrun()    
@manager.command
def example():
    if check_message('Are you sure to walk run table ? (Y/n)') == False:
        return
    with app.app_context():
        DBManager.insert_dummy_example()  
def check_message(message):
    inp = input(message)
    if inp == 'Y':
        return True
    return False

if __name__ == '__main__':
    manager.run()