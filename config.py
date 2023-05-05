import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or '123b2$E$hv*(df&*3b$biub3'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:@localhost/bulletin_board'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOADS_FOLDER = os.path.join('app', 'static', 'uploads')
    PROFILE_PHOTO_FILENAME = 'profile'
    PHOTO_SMALL_PREFIX = '.small'
    PHOTO_TINY_PREFIX = '.tiny'

