from flask import Blueprint

product_bp = Blueprint('product', __name__, template_folder='../../templates/product')

from app.blueprints.product import routes
