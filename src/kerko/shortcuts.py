from flask import current_app


def composer():
    return current_app.config['KERKO_COMPOSER']


def setting(key):
    return current_app.config[key]
