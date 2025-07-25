from flask import (
    abort, Blueprint, redirect, render_template, session,
    request, current_app, send_from_directory
)
import os
from antibodyapi.utils.elasticsearch import execute_query
import logging
import html5lib

hubmap_blueprint = Blueprint('hubmap', __name__, template_folder='templates')
logger = logging.getLogger(__name__)


def bad_request_error(err_msg):
    abort(400, description=err_msg)


@hubmap_blueprint.route('/upload')
def hubmap():
    # replace by the correct way to check token validity.
    if not session.get('is_authenticated'):
        # return redirect(url_for('login.login'))
        redirect_url = current_app.config['FLASK_APP_BASE_URI'].rstrip('/') + '/login'
        return redirect(redirect_url)

    if not session.get('is_authorized'):
        logger.info("User is not authorized.")
        hubmap_avr_uploaders_group_id: str = current_app.config['HUBMAP_AVR_UPLOADERS_GROUP_ID']
        return render_template(
            'unauthorized.html',
            hubmap_avr_uploaders_group_id=hubmap_avr_uploaders_group_id
        )

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
    # replace by the correct way to check token validity.
    # authenticated = session.get('is_authenticated')
    # if not authenticated:
    #     return redirect(url_for('login.login'))
    assets_url: str = current_app.config['ASSETS_URL']
    display: dict = {
        "target_symbol": "table-cell",
        "uniprot_accession_number": "table-cell",
        "clonality": "table-cell",
        "method": "table-cell",
        "tissue_preservation": "table-cell",
        "avr_pdf_filename": "table-cell",
        "omap_id": "table-cell",
        "antibody_hubmap_id": "table-cell",
        "previous_version_id": "table-cell",

        "clone_id": "none",
        "host": "none",
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
        "created_by_user_email": "none"
    }
    csv_column_order: list = [
        "target_symbol", "uniprot_accession_number", "clonality", "clone_id", "method",
        "tissue_preservation", "avr_pdf_filename", "antibody_hubmap_id",

        "host",
        "rrid", "catalog_number", "lot_number", "vendor_name",
        "recombinant", "organ", "author_orcids", "hgnc_id", "isotype",
        "concentration_value", "dilution_factor", "conjugate", "cycle_number",
        "fluorescent_reporter", "manuscript_doi", "protocol_doi",
        "vendor_affiliation", "organ_uberon_id", "antigen_retrieval", "omap_id",
        "created_by_user_email", "previous_version_id", "next_version_id"
    ]
    # Link the individual OMAP entries to the (P)URLs defined mapped in
    # https://github.com/hubmapconsortium/antibody-api/files/13229463/HRA7threleasetoUBKG-June2024PurlsOMAPs.xlsx
    omap_id_linkage: dict = {
        "OMAP-1": "https://purl.humanatlas.io/omap/1-human-lymph-node-ibex",
        "OMAP-2": "https://purl.humanatlas.io/omap/2-intestine-codex",
        "OMAP-3": "https://purl.humanatlas.io/omap/3-kidney-codex",
        "OMAP-4": "https://purl.humanatlas.io/omap/4-skin-cell-dive",
        "OMAP-5": "https://purl.humanatlas.io/omap/5-liver-sims",
        "OMAP-6": "https://purl.humanatlas.io/omap/6-pancreas-codex",
        "OMAP-7": "https://purl.humanatlas.io/omap/7-lung-cell-dive",
        "OMAP-8": "https://purl.humanatlas.io/omap/8-placenta-full-term-imc",
        "OMAP-9": "https://purl.humanatlas.io/omap/9-kidney-codex",
        "OMAP-10": "https://purl.humanatlas.io/omap/10-palatine-tonsil-mics",
        "OMAP-11": "https://purl.humanatlas.io/omap/11-spleen-ibex",
        "OMAP-12": "https://purl.humanatlas.io/omap/12-eye-retina-ibex",
        "OMAP-13": "https://purl.humanatlas.io/omap/13-pancreas-codex",
        "OMAP-14": "https://purl.humanatlas.io/omap/14-kidney-cycif",
        "OMAP-15": "https://purl.humanatlas.io/omap/15-intestine-codex",
        "OMAP-16": "https://purl.humanatlas.io/omap/16-lung-codex",
        "OMAP-17": "https://purl.humanatlas.io/omap/17-thymus-ibex",
        "OMAP-18": "https://purl.humanatlas.io/omap/18-lymph-node-cell-dive-ibex",
        "OMAP-19": "https://purl.humanatlas.io/omap/19-palatine-tonsil-ibex",
        "OMAP-20": "https://purl.humanatlas.io/omap/20-kidney-ims-cycif",
        "OMAP-21": "https://purl.humanatlas.io/omap/21-palatine-tonsil-mics",
        "OMAP-22": "https://purl.humanatlas.io/omap/22-skin-cell-dive",
        "OMAP-23": "https://purl.humanatlas.io/omap/23-vermiform-appendix-mics",
        "OMAP-24": "https://purl.humanatlas.io/omap/24-pancreas-cycif",
        "OMAP-25": "https://purl.humanatlas.io/omap/25-lung-codex",
        "OMAP-26": "https://purl.humanatlas.io/omap/26-kidney-codex",
        "OMAP-27": "https://purl.humanatlas.io/omap/27-kidney-ims-codex",
        "OMAP-28": "https://purl.humanatlas.io/omap/28-heart-codex",
        "OMAP-29": "https://purl.humanatlas.io/omap/29-mouth-mucosa-codex",
        "OMAP-30": "https://purl.humanatlas.io/omap/30-salivary-gland-codex"
    }

    try:
        banner_message: str = current_app.config['BANNER_MESSAGE']
        try:
            html5lib.parseFragment(banner_message)
        except html5lib.html5parser.ParseError as pe:
            logger.error(f"ParseError found in app.conf:BANNER_MESSAGE: {pe}")
            exit(1)
    except KeyError:
        banner_message: str = ''

    return render_template(
        'search.html',
        assets_url=assets_url,
        display=display,
        csv_column_order=csv_column_order,
        omap_id_linkage=omap_id_linkage,
        banner_message=banner_message
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


@hubmap_blueprint.route('/_search', methods=['GET', 'POST'])
def search():
    # replace by the correct way to check token validity.
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
