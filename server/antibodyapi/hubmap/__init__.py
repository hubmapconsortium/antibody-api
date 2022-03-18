from flask import abort, Blueprint, redirect, render_template, session, url_for, request, current_app, send_from_directory
import os
from antibodyapi.utils.elasticsearch import execute_query


def bad_request_error(err_msg):
    abort(400, description = err_msg)


hubmap_blueprint = Blueprint('hubmap', __name__, template_folder='templates')
@hubmap_blueprint.route('/upload')
def hubmap():
    #replace by the correct way to check token validity.
    authenticated = session.get('is_authenticated')
    if not authenticated:
        return redirect(url_for('login.login'))
    data_provider_groups = session.get('data_provider_groups')
    if data_provider_groups is not None and len(data_provider_groups) == 1:
        data_provider_groups = None
    return render_template(
        'base.html',
        token=session['tokens'],
        data_provider_groups=data_provider_groups
    )


@hubmap_blueprint.route('/')
def hubmap_search():
    #replace by the correct way to check token validity.
    # authenticated = session.get('is_authenticated')
    # if not authenticated:
    #     return redirect(url_for('login.login'))
    assets_url: str = current_app.config['ASSETS_URL']
    display: dict = {
        "antibody_name": "table-cell",
        "host_organism": "table-cell",
        "uniprot_accession_number": "table-cell",
        "target_name": "table-cell",
        "avr_filename": "table-cell",
        "rrid": "none",
        "clonality": "none",
        "catalog_number": "none",
        "lot_number": "none",
        "vendor": "none",
        "recombinant": "none",
        "organ_or_tissue": "none",
        "hubmap_platform": "none",
        "submitter_orcid": "none",
        "created_by_user_email": "none"
    }
    return render_template(
        'search.html',
        assets_url=assets_url,
        display=display
    )


# https://flask.palletsprojects.com/en/2.0.x/patterns/favicon/
@hubmap_blueprint.route('/static/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'hubmap', 'static'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@hubmap_blueprint.route('/css/app.css')
def css():
    return send_from_directory(os.path.join(current_app.root_path, 'hubmap', 'css'), 'app.css',
                               mimetype='text/css')


@hubmap_blueprint.route('/_search', methods = ['GET', 'POST'])
def search():
    #replace by the correct way to check token validity.
    # authenticated = session.get('is_authenticated')
    # if not authenticated:
    #     return redirect(url_for('login.login'))

    # # Always expect a json body
    # if not request.is_json:
    #     bad_request_error("A JSON body and appropriate Content-Type header are required")


    # Determine the target real index in Elasticsearch to be searched against
    # Use the app.config['DEFAULT_INDEX_WITHOUT_PREFIX'] since /search doesn't take any index
    # target_index = get_target_index(request, app.config['DEFAULT_INDEX_WITHOUT_PREFIX'])


    # Return the elasticsearch resulting json data as json string
    return execute_query(request.get_json())
