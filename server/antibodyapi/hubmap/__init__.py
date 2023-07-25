from flask import abort, Blueprint, redirect, render_template, session, request, current_app, send_from_directory
import os
from antibodyapi.utils.elasticsearch import execute_query

hubmap_blueprint = Blueprint('hubmap', __name__, template_folder='templates')


def bad_request_error(err_msg):
    abort(400, description = err_msg)


@hubmap_blueprint.route('/upload')
def hubmap():
    #replace by the correct way to check token validity.
    authenticated = session.get('is_authenticated')
    if not authenticated:
        #return redirect(url_for('login.login'))
        redirect_url = current_app.config['FLASK_APP_BASE_URI'].rstrip('/') + '/login'
        return redirect(redirect_url)
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
        "target_symbol": "table-cell",
        "uniprot_accession_number": "table-cell",
        "clonality": "table-cell",
        "clone_id": "table-cell",
        "method": "table-cell",
        "tissue_preservation": "table-cell",
        "avr_pdf_filename": "table-cell",

        "host": "none",
        "cell_line": "none",
        "cell_line_ontology_id": "none",
        "rrid": "none",
        "catalog_number": "none",
        "lot_number": "none",
        "vendor_name": "none",
        "recombinant": "none",
        "organ": "none",
        "author_orcids": "none",
        "hgnc_id": "none",
        "isotype": "none",
        "concentration_value": "none",
        "dilution_factor": "none",
        "conjugate": "none",
        "cycle_number": "none",
        "fluorescent_reporter": "none",
        "manuscript_doi": "none",
        "protocol_doi": "none",
        "vendor_affiliation": "none",
        "organ_uberon_id": "none",
        "antigen_retrieval": "none",
        "omap_id": "none",
        "created_by_user_email": "none"
    }
    csv_column_order: list = [
        "target_symbol", "uniprot_accession_number", "clonality", "clone_id", "method", "tissue_preservation", "avr_pdf_filename",

        "host", "cell_line", "cell_line_ontoloty_id",
        "rrid", "catalog_number", "lot_number", "vendor_name",
        "recombinant", "organ", "author_orcids", "hgnc_id", "isotype",
        "concentration_value", "dilution_factor", "conjugate", "cycle_number",
        "fluorescent_reporter", "manuscript_doi", "protocol_doi",
        "vendor_affiliation", "organ_uberon_id", "antigen_retrieval", "omap_id",
        "created_by_user_email"
    ]
    return render_template(
        'search.html',
        assets_url=assets_url,
        display=display,
        csv_column_order=csv_column_order
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
