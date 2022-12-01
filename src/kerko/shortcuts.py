from flask import current_app


def composer():
    return current_app.config['KERKO_COMPOSER']


def config(key):
    return current_app.config[key]
