from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.blueprints.notification import notification_bp
from app.services import notification_service


@notification_bp.route('/')
@login_required
def list():
    ntype = request.args.get('type', '')
    page = request.args.get('page', 1, type=int)
    notifications = notification_service.get_user_notifications(
        current_user.user_id, type_filter=ntype or None, page=page
    )
    return render_template('notification/list.html',
                         notifications=notifications.items,
                         pagination=notifications,
                         current_filter=ntype)


@notification_bp.route('/read-all', methods=['POST'])
@login_required
def read_all():
    notification_service.mark_all_read(current_user.user_id)
    flash('所有通知已标记为已读。', 'success')
    return redirect(url_for('notification.list'))
