from flask import Blueprint

order_bp = Blueprint('order', __name__, template_folder='../../templates/order')

from app.blueprints.order import routes
