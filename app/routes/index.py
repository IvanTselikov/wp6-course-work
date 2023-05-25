from flask import request, render_template

from flask_login import current_user
from flask_breadcrumbs import register_breadcrumb

from app import app
from app.forms import FiltersForm, CreateAdForm, LoginForm, SignupForm

from .functions import get_filtered_ads, parse_int_or_skip


@app.route('/')
@app.route('/index')
@register_breadcrumb(app, '.', 'Главная')
def index():
    filters_form = FiltersForm()
    kwargs = { 'filters_form': filters_form }

    if current_user.is_authenticated:
        ad_form = CreateAdForm()
        kwargs.update({ 'ad_form': ad_form })
    else:
        login_form = LoginForm()
        signup_form = SignupForm()
        kwargs.update({'login_form': login_form, 'signup_form': signup_form})

    # подготовка параметров фильтрации
    filter_params = {
        'page': parse_int_or_skip(request.args.get('page', default=1)),
        'per_page': app.config['ADS_PER_PAGE_DEFAULT']
    }
    for key, value in request.cookies.items():
        filter_params.update({ key: parse_int_or_skip(value) })
    
    # фильтрация объявлений
    ads, result_header = get_filtered_ads(filter_params)
    
    kwargs.update({
        'ads': ads,
        'ads_section_header': result_header
    })

    return render_template('index.html', **kwargs)
