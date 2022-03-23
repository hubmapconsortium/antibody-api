import globus_sdk
from flask import Blueprint, current_app, redirect, request, session, url_for
from antibodyapi.utils import get_data_provider_groups, get_user_info
import logging

logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

login_blueprint = Blueprint('login', __name__)


@login_blueprint.route('/login')
def login():
    app = current_app
    redirect_uri: str = app.config['FLASK_APP_BASE_URI'].rstrip('/') + '/login'
    # redirect_uri: str =  url_for('login.login', _external=True)
    logger.info(f"login():redirect_uri: {redirect_uri}")
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
        session.update(
            data_provider_groups=get_data_provider_groups(app.config['INGEST_API_URL'])
        )
        logger.info(f"url_for('hubmap.hubmap'): {url_for('hubmap.hubmap')}")
        #return redirect(url_for('hubmap.hubmap'))
        target_url: str = app.config['FLASK_APP_BASE_URI'].rstrip('/') + '/upload'
        logger.info(f"target_url: {target_url}")
        return redirect(target_url)
