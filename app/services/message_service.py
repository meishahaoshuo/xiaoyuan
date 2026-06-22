from app.extensions import db
from app.models.message import Message
from app.models.product import Product
from app.models.user import User


def send_message(sender_id, receiver_id, product_id, content):
    if sender_id == receiver_id:
        return False, '不能给自己发消息。', None
    if not content or not content.strip():
        return False, '消息内容不能为空。', None
    product = db.session.get(Product, product_id)
    if not product or product.deleted:
        return False, '关联商品不存在。', None
    msg = Message(
        sender_id=sender_id, receiver_id=receiver_id,
        product_id=product_id, message_content=content.strip()
    )
    db.session.add(msg)
    db.session.commit()
    return True, '消息发送成功。', msg


def get_conversations(user_id):
    """Get conversation list with other_user, product, last_message, unread_count."""
    sent = db.session.query(
        Message.receiver_id.label('other_id'), Message.product_id,
        db.func.max(Message.created_at).label('last_time')
    ).filter(Message.sender_id == user_id, Message.deleted == False).group_by(
        Message.receiver_id, Message.product_id)

    received = db.session.query(
        Message.sender_id.label('other_id'), Message.product_id,
        db.func.max(Message.created_at).label('last_time')
    ).filter(Message.receiver_id == user_id, Message.deleted == False).group_by(
        Message.sender_id, Message.product_id)

    conversations = {}
    def add_conv(other_id, product_id, last_time):
        key = (other_id, product_id)
        if key not in conversations or last_time > conversations[key]['last_time']:
            conversations[key] = {'other_id': other_id, 'product_id': product_id, 'last_time': last_time}

    for row in sent.all():
        add_conv(row.other_id, row.product_id, row.last_time)
    for row in received.all():
        add_conv(row.other_id, row.product_id, row.last_time)

    result = []
    for (other_id, product_id), data in conversations.items():
        other_user = db.session.get(User, other_id)
        product = db.session.get(Product, product_id)
        if not other_user or not product:
            continue

        last_msg = Message.active().filter(
            db.or_(
                db.and_(Message.sender_id == user_id, Message.receiver_id == other_id),
                db.and_(Message.sender_id == other_id, Message.receiver_id == user_id)
            ), Message.product_id == product_id
        ).order_by(Message.created_at.desc()).first()

        unread = Message.active().filter(
            Message.sender_id == other_id, Message.receiver_id == user_id,
            Message.product_id == product_id, Message.read_status == False
        ).count()

        result.append({
            'other_user': other_user, 'product': product,
            'last_message': last_msg, 'last_time': data['last_time'],
            'unread_count': unread,
        })

    result.sort(key=lambda x: x['last_time'], reverse=True)
    return result


def get_chat_messages(user_id, other_user_id, product_id):
    return Message.active().filter(
        db.or_(
            db.and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
            db.and_(Message.sender_id == other_user_id, Message.receiver_id == user_id)
        ), Message.product_id == product_id
    ).order_by(Message.created_at.asc()).all()


def mark_messages_read(user_id, other_user_id, product_id):
    Message.active().filter(
        Message.sender_id == other_user_id, Message.receiver_id == user_id,
        Message.product_id == product_id, Message.read_status == False
    ).update({'read_status': True}, synchronize_session='fetch')
    db.session.commit()


def get_unread_count(user_id):
    return Message.active().filter(
        Message.receiver_id == user_id, Message.read_status == False
    ).count()
