from flask import g, Flask

from antibodyapi.hubmap import hubmap_blueprint
from antibodyapi.import_antibodies import import_antibodies_blueprint
from antibodyapi.list_antibodies import list_antibodies_blueprint
from antibodyapi.login import login_blueprint
from antibodyapi.logout import logout_blueprint
from antibodyapi.save_antibody import save_antibody_blueprint

from . import default_config

def create_app(testing=False):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(default_config.DefaultConfig)
    app.config['UPLOAD_FOLDER'] = '/tmp'
    if testing:
        app.config['TESTING'] = True
    else:
        # We should not load the gitignored app.conf during tests.
        app.config.from_pyfile('app.conf')

    app.register_blueprint(hubmap_blueprint)
    app.register_blueprint(import_antibodies_blueprint)
    app.register_blueprint(list_antibodies_blueprint)
    app.register_blueprint(login_blueprint)
    app.register_blueprint(logout_blueprint)
    app.register_blueprint(save_antibody_blueprint)

    @app.teardown_appcontext
    def close_db(error): # pylint: disable=unused-argument
        if 'connection' in g:
            g.connection.close()

    return app
