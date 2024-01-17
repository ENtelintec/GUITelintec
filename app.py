from flask import Flask
from flask_cors import CORS
from static.extensions import api
from templates.resources.resources_login import ns as ns_login
from templates.resources.resources_RRHH import ns as ns_rrhh

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route('/GUI/hello')
def hello_world():  # put application's code here
    return 'Hello World!'


api.init_app(app)
api.add_namespace(ns_login)
api.add_namespace(ns_rrhh)

if __name__ == '__main__':
    app.run()
