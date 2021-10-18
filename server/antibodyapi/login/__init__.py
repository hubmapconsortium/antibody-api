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

login_blueprint = Blueprint('login', __name__)
@login_blueprint.route('/login')
def login():
    app = current_app
    redirect_uri = url_for('login.login', _external=True)
    client = globus_sdk.ConfidentialAppAuthClient(
        app.config['APP_CLIENT_ID'],
        app.config['APP_CLIENT_SECRET']
    )
    client.oauth2_start_flow(redirect_uri)

    if 'code' not in request.args: # pylint: disable=no-else-return
        auth_uri = client.oauth2_get_authorize_url(query_params={"scope": "openid profile email urn:globus:auth:scope:transfer.api.globus.org:all urn:globus:auth:scope:auth.globus.org:view_identities urn:globus:auth:scope:nexus.api.globus.org:groups" }) # pylint: disable=line-too-long
        return redirect(auth_uri)
    else:
        code = request.args.get('code')
        tokens = client.oauth2_exchange_code_for_tokens(code)
        user_info = get_user_info(tokens)
        session.update(
            name=user_info['name'],
            email=user_info['email'],
            sub=user_info['sub'],
            tokens=tokens.by_resource_server,
            is_authenticated=True
        )
        return redirect(url_for('hubmap.hubmap'))
