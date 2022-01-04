import globus_sdk
from flask import Blueprint, current_app, redirect, request, session, url_for
from antibodyapi.utils import get_user_info

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
        auth_uri = client.oauth2_get_authorize_url(query_params={"scope": "openid profile email urn:globus:auth:scope:transfer.api.globus.org:all urn:globus:auth:scope:auth.globus.org:view_identities urn:globus:auth:scope:nexus.api.globus.org:groups urn:globus:auth:scope:groups.api.globus.org:all" }) # pylint: disable=line-too-long
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
            groups_access_token=tokens.by_resource_server['groups.api.globus.org']['access_token'],
            is_authenticated=True
        )
        return redirect(url_for('hubmap.hubmap'))
