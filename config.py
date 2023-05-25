import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or '123b2$E$hv*(df&*3b$biub3'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:@localhost/bulletin_board'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JSON_SORT_KEYS = False

    WTF_CSRF_ENABLED = False

    UPLOADS_FOLDER = os.path.join('app', 'static', 'uploads')
    PROFILE_PHOTO_FILENAME = 'profile'
    PHOTO_SMALL_PREFIX = '.small'
    PHOTO_TINY_PREFIX = '.tiny'

    PHOTO_FILE_EXTENTIONS = ['png', 'jpg', 'jpeg']

    MIN_CAR_RELEASE_YEAR = 1900
    ADS_PER_PAGE = [10, 50, 100]
    ADS_PER_PAGE_DEFAULT = 10
