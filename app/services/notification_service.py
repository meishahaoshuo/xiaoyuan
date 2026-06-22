from app.extensions import db
from app.models.notification import Notification


def create_notification(receiver_id, ntype, title, content, related_id=None):
    notif = Notification(
        receiver_id=receiver_id, notification_type=ntype,
        title=title, content=content, related_id=related_id
    )
    db.session.add(notif)
    return notif


def get_user_notifications(user_id, type_filter=None, page=1, per_page=20):
    q = Notification.active().filter_by(receiver_id=user_id)
    if type_filter:
        q = q.filter_by(notification_type=type_filter)
    return q.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)


def mark_all_read(user_id):
    Notification.active().filter_by(
        receiver_id=user_id, read_status=False
    ).update({'read_status': True}, synchronize_session='fetch')
    db.session.commit()


def mark_read(notification_id, user_id):
    notif = Notification.active().filter_by(
        notification_id=notification_id, receiver_id=user_id).first()
    if notif:
        notif.read_status = True
        db.session.commit()
