from flask import Flask
from flask_cors import CORS
from static.constants import api
from templates.resources.resources_RRHH import ns as ns_rrhh
from templates.resources.resources_SM import ns as ns_sm
from templates.resources.resources_Bitacora import ns as ns_bitacora
from templates.resources.resources_Almacen import ns as ns_almacen
from templates.resources.resources_Misc import ns as ns_misc
from templates.resources.resources_Admin_presales import ns as ns_admin_presales
from templates.resources.resources_Admin_DB import ns as ns_admin_db
from templates.resources.resources_Dashboards import ns as ns_dashboard
from templates.resources.resources_Common import ns as ns_common
from wtforms_json import init as init_wtforms_json

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.config["CORS_HEADERS"] = "Content-Type"
init_wtforms_json()


@app.route("/GUI/hello")
def hello_world():  # put application's code here
    return "Hello World! GUI"


api.init_app(app)
api.add_namespace(ns_rrhh)
api.add_namespace(ns_sm)
api.add_namespace(ns_bitacora)
api.add_namespace(ns_almacen)
api.add_namespace(ns_misc)
api.add_namespace(ns_admin_presales)
api.add_namespace(ns_admin_db)
api.add_namespace(ns_dashboard)
api.add_namespace(ns_common)


if __name__ == "__main__":
    app.run()
