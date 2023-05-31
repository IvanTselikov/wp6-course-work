from flask import render_template
from flask_login import current_user

from app import app
from app.forms import FiltersForm, CreateAdForm, LoginForm, SignupForm


@app.route('/errors/<int:code>')
def errors(code):
    filters_form = FiltersForm()
    kwargs = { 'filters_form': filters_form }

    if current_user.is_authenticated:
        ad_form = CreateAdForm()
        kwargs.update({ 'ad_form': ad_form })
    else:
        login_form = LoginForm()
        signup_form = SignupForm()
        kwargs.update({'login_form': login_form, 'signup_form': signup_form})
    
    if code == 404:
        return render_template('errors/404.html', **kwargs)
