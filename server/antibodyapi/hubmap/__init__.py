from flask import Blueprint, redirect, render_template, session, url_for

hubmap_blueprint = Blueprint('hubmap', __name__, template_folder='templates')
@hubmap_blueprint.route('/upload')
def hubmap():
    #replace by the correct way to check token validity.
    authenticated = session.get('is_authenticated')
    if not authenticated:
        return redirect(url_for('login.login'))
    return render_template('base.html')


@hubmap_blueprint.route('/')
def hubmap_search():
    #replace by the correct way to check token validity.
    # authenticated = session.get('is_authenticated')
    # if not authenticated:
    #     return redirect(url_for('login.login'))
    return render_template('search.html')
