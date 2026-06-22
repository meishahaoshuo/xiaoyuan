from flask import Blueprint

notification_bp = Blueprint('notification', __name__, template_folder='../../templates/notification')

from app.blueprints.notification import routes
