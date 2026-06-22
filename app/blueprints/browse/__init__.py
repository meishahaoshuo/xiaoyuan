from flask import Blueprint

browse_bp = Blueprint('browse', __name__, template_folder='../../templates/browse')

from app.blueprints.browse import routes
