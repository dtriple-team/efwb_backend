#!/usr/bin/python
# -*- coding: utf-8 -*-


class DevelopmentConfig():
    BIND_PORT = 8081
    WEB_URL = "http://127.0.0.1"
    SQLALCHEMY_DATABASE_URI = 'mysql://dbadmin:p@ssw0rd@127.0.0.1/efwb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig():
    BIND_PORT = 8081
    WEB_URL = "http://127.0.0.1"
    SQLALCHEMY_DATABASE_URI = 'mysql://dbadmin:p@ssw0rd@127.0.0.1/efwb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False




