from flask import Flask, render_template
from app.config import config
from app.extensions import db, login_manager, migrate


def create_app(config_name='default'):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Health check (no DB needed)
    @app.route('/ping')
    def ping():
        return 'pong'

    @app.route('/db-test')
    def db_test():
        try:
            from app.models.category import Category
            count = Category.query.count()
            return f'DB OK: {count} categories'
        except Exception as e:
            return f'DB Error: {str(e)}'

    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.user import user_bp
    from app.blueprints.product import product_bp
    from app.blueprints.browse import browse_bp
    from app.blueprints.order import order_bp
    from app.blueprints.social import social_bp
    from app.blueprints.notification import notification_bp
    from app.blueprints.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(product_bp, url_prefix='/product')
    app.register_blueprint(browse_bp)
    app.register_blueprint(order_bp, url_prefix='/order')
    app.register_blueprint(social_bp, url_prefix='/social')
    app.register_blueprint(notification_bp, url_prefix='/notifications')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # User loader for Flask-Login
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(413)
    def too_large(e):
        from flask import flash, redirect, request
        flash('上传文件过大，单个文件最大 5MB。', 'danger')
        return redirect(request.url)

    # Context processors
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        ctx = {'current_user': current_user}
        try:
            from app.models.category import Category
            ctx['get_categories'] = lambda: Category.enabled().order_by(Category.category_name).all()
        except Exception:
            ctx['get_categories'] = lambda: []
        if current_user.is_authenticated:
            try:
                from app.models.notification import Notification
                unread = Notification.query.filter_by(
                    receiver_id=current_user.user_id, read_status=0, deleted=0
                ).count()
                ctx['unread_notification_count'] = unread
            except Exception:
                ctx['unread_notification_count'] = 0
        else:
            ctx['unread_notification_count'] = 0
        return ctx

    return app
