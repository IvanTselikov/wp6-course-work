from app import app

from PIL import Image
from datetime import datetime as dt


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


def parse_int_or_skip(s):
    try:
        return int(s)
    except:
        return s