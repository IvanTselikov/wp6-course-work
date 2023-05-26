from app import app

from flask import jsonify, request
from app.models import *

from PIL import Image
from datetime import datetime as dt
import time

from werkzeug.utils import secure_filename

import os
from glob import glob

import locale


def update_params(request, **kwargs):
    return request.args.to_dict() | kwargs
app.jinja_env.globals.update(update_params=update_params)
