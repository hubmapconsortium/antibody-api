import globus_sdk
from flask import Blueprint, current_app, redirect, request, session, url_for, render_template
from antibodyapi.utils import get_data_provider_groups, get_user_info
import logging

logger = logging.getLogger(__name__)

login_blueprint = Blueprint('login', __name__)


@login_blueprint.route('/login')
def login():
    app = current_app
    redirect_uri: str = app.config['FLASK_APP_BASE_URI'].rstrip('/') + '/login'
    # redirect_uri: str =  url_for('login.login', _external=True)
    logger.info(f"login(): redirect_uri: {redirect_uri}")
    globus_auth_client = globus_sdk.ConfidentialAppAuthClient(
        app.config['APP_CLIENT_ID'],
        app.config['APP_CLIENT_SECRET']
    )
    globus_auth_client.oauth2_start_flow(redirect_uri, refresh_tokens=True)

    # If there's no "code" query string parameter, we're in this route
    # starting a Globus Auth login flow.
    # Redirect out to Globus Auth
    if 'code' not in request.args: # pylint: disable=no-else-return
        auth_uri = globus_auth_client.oauth2_get_authorize_url(query_params={
            "scope": "openid profile email urn:globus:auth:scope:transfer.api.globus.org:all urn:globus:auth:scope:auth.globus.org:view_identities urn:globus:auth:scope:nexus.api.globus.org:groups urn:globus:auth:scope:groups.api.globus.org:all"
        }) # pylint: disable=line-too-long
        return redirect(auth_uri)
    else:
        code = request.args.get('code')
        tokens = globus_auth_client.oauth2_exchange_code_for_tokens(code)
        user_info = get_user_info(tokens)
        logger.info(f"login user_info: {user_info}")
        groups_access_token = tokens.by_resource_server['groups.api.globus.org']['access_token']

        # https://globus-sdk-python.readthedocs.io/en/stable/examples/group_listing.html
        globus_groups_client = globus_sdk.GroupsClient(
            authorizer=globus_sdk.AccessTokenAuthorizer(groups_access_token)
        )
        my_groups = globus_groups_client.get_my_groups()
        #logger.info(f"login(): my_groups: {my_groups}")
        my_group_ids = [g['id'] for g in my_groups]
        is_authorized = False
        hubmap_avr_uploaders_group_id: str = current_app.config['HUBMAP_AVR_UPLOADERS_GROUP_ID']
        if hubmap_avr_uploaders_group_id in my_group_ids:
            is_authorized = True
        logger.info(f"login(): groups: {my_group_ids}; "
                    f"uploader_group: {hubmap_avr_uploaders_group_id}; "
                    f"is_authorized: {is_authorized}")

        session.update(
            name=user_info['name'],
            email=user_info['email'],
            sub=user_info['sub'],
            tokens=tokens.by_resource_server,
            groups_access_token=groups_access_token,
            is_authenticated=True,
            is_authorized=is_authorized
        )
        session.update(
            data_provider_groups=get_data_provider_groups(app.config['INGEST_API_URL'])
        )

        if not is_authorized:
            logger.info("User is not authorized.")
            return render_template(
                'unauthorized.html',
                hubmap_avr_uploaders_group_id=hubmap_avr_uploaders_group_id
            )

        logger.info(f"url_for('hubmap.hubmap'): {url_for('hubmap.hubmap')}")
        #return redirect(url_for('hubmap.hubmap'))
        upload_url: str = app.config['FLASK_APP_BASE_URI'].rstrip('/') + '/upload'
        logger.info(f"Redirecting to: {upload_url}")
        return redirect(upload_url)
