from app import app

from flask import jsonify, request
from app.models import *

from PIL import Image
from datetime import datetime as dt

from werkzeug.utils import secure_filename

import os
from glob import glob


EARLIEST_RELEASE_YEAR = 1900


def upload_photo(file_storage, path_origin, path_small=None, path_tiny=None):
    # сохранение оригинального размера
    file_storage.save(path_origin)

    # сохранение уменьшенного изображения
    if path_small:
        im = Image.open(path_origin)
        im.thumbnail((500,500), Image.Resampling.LANCZOS)
        im.save(path_small)

    # сохранение маленького изображения
    if path_tiny:
        im = Image.open(path_origin)
        im.thumbnail((50,50), Image.Resampling.LANCZOS)
        im.save(path_tiny)

def get_current_year():
    return dt.now().year

def update_params(request, **kwargs):
    return request.args.to_dict() | kwargs
app.jinja_env.globals.update(update_params=update_params)


def parse_int_or_skip(s, default=None):
    try:
        return int(s)
    except:
        return default or s


def view_ad_dlc(*args, **kwargs):
    ad_id = request.view_args['ad_id']
    ad = Ad.query.get(ad_id)
    return [
        {
            'text': '{} {}, {}'.format(
                ad.car.serie.generation.model.mark.name,
                ad.car.serie.generation.model.name,
                ad.release_year
            ),
            'url': ''
        }
    ]

def remove_ad_photo(ad, photo_number):
    photo_filenames = glob(os.path.join(
        app.config['UPLOADS_FOLDER'],
        ad.seller.login,
        str(ad.id),
        '{}.*'.format(photo_number)
    ))

    for filename in photo_filenames:
        os.remove(filename)
