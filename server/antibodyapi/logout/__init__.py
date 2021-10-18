import globus_sdk
from flask import (
    abort, Blueprint, current_app, jsonify, make_response,
    redirect, render_template, request, session, url_for
)
from antibodyapi.utils import (
    allowed_file, base_antibody_query, find_or_create_vendor, get_cursor,
    get_file_uuid, get_hubmap_uuid, get_user_info, insert_query,
    insert_query_with_avr_file_and_uuid, json_error
)

logout_blueprint = Blueprint('logout', __name__)
@logout_blueprint.route('/logout')
def logout():
    """
    - Revoke the tokens with Globus Auth.
    - Destroy the session state.
    - Redirect the user to the Globus Auth logout page.
    """
    app = current_app
    client = globus_sdk.ConfidentialAppAuthClient(
        app.config['APP_CLIENT_ID'],
        app.config['APP_CLIENT_SECRET']
    )

    # Revoke the tokens with Globus Auth
    if 'tokens' in session:
        for token in (token_info['access_token']
            for token_info in session['tokens'].values()):
            client.oauth2_revoke_token(token)

    # Destroy the session state
    session.clear()

    # build the logout URI with query params
    # there is no tool to help build this (yet!)
    redirect_uri = url_for('login.login', _external=True)

    globus_logout_url = (
        'https://auth.globus.org/v2/web/logout' +
        '?client={}'.format(app.config['APP_CLIENT_ID']) +
        '&redirect_uri={}'.format(redirect_uri) +
        '&redirect_name={}'.format('hubmap')
    )

    # Redirect the user to the Globus Auth logout page
    return redirect(globus_logout_url)
