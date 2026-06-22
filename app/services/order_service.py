from datetime import datetime
from app.extensions import db
from app.models.orders import Order
from app.models.product import Product
from app.models.notification import Notification
from app.utils.helpers import generate_order_no, generate_transaction_no


def submit_order(buyer_id, product_id, trade_type, buyer_message=None):
    product = db.session.get(Product, product_id)
    if not product or product.deleted:
        return False, '商品不存在或已下架。', None
    if product.seller_id == buyer_id:
        return False, '不能购买自己的商品。', None
    if product.product_status != 'ON_SALE':
        return False, '该商品当前不可购买。', None
    existing = Order.active().filter(
        Order.product_id == product_id, Order.buyer_id == buyer_id,
        Order.order_status.in_(['PENDING', 'CONFIRMED', 'PAID'])
    ).first()
    if existing:
        return False, '您已有一个进行中的订单。', None

    order = Order(
        order_no=generate_order_no(), product_id=product_id,
        buyer_id=buyer_id, seller_id=product.seller_id,
        order_amount=product.price, trade_type=trade_type,
        buyer_message=buyer_message[:200] if buyer_message else None,
        order_status='PENDING', payment_status='UNPAID'
    )
    db.session.add(order)

    notify = Notification(
        receiver_id=product.seller_id, notification_type='ORDER',
        title='新的购买订单',
        content=f'您的商品「{product.product_name}」收到新的购买订单。',
        related_id=order.order_id
    )
    db.session.add(notify)
    db.session.commit()
    return True, '订单提交成功，等待卖家确认。', order


def seller_confirm_order(order, seller_id):
    if order.seller_id != seller_id:
        return False, '无权操作此订单。'
    if order.order_status != 'PENDING':
        return False, '订单当前状态无法确认。'
    if not order.can_transition_to('CONFIRMED'):
        return False, '订单状态转换无效。'

    order.order_status = 'CONFIRMED'
    other_orders = Order.active().filter(
        Order.product_id == order.product_id, Order.order_id != order.order_id,
        Order.order_status == 'PENDING'
    ).all()
    for o in other_orders:
        o.order_status = 'CANCELLED'

    notify = Notification(
        receiver_id=order.buyer_id, notification_type='ORDER',
        title='订单已确认', content=f'您的订单 {order.order_no} 已被卖家确认。',
        related_id=order.order_id
    )
    db.session.add(notify)
    db.session.commit()
    return True, '订单已确认。'


def seller_reject_order(order, seller_id, reason):
    if order.seller_id != seller_id:
        return False, '无权操作此订单。'
    if order.order_status != 'PENDING':
        return False, '订单当前状态无法拒绝。'
    if not reason or len(reason.strip()) < 2 or len(reason) > 100:
        return False, '拒绝原因需要2~100个字符。'
    order.order_status = 'REJECTED'
    order.reject_reason = reason.strip()

    notify = Notification(
        receiver_id=order.buyer_id, notification_type='ORDER',
        title='订单已被拒绝',
        content=f'您的订单 {order.order_no} 已被卖家拒绝。原因：{reason}',
        related_id=order.order_id
    )
    db.session.add(notify)
    db.session.commit()
    return True, '已拒绝该订单。'


def buyer_cancel_order(order, buyer_id):
    if order.buyer_id != buyer_id:
        return False, '无权操作此订单。'
    if order.order_status not in ('PENDING', 'CONFIRMED'):
        return False, '订单当前状态无法取消。'
    order.order_status = 'CANCELLED'

    notify = Notification(
        receiver_id=order.seller_id, notification_type='ORDER',
        title='订单已取消', content=f'订单 {order.order_no} 已被买家取消。',
        related_id=order.order_id
    )
    db.session.add(notify)
    db.session.commit()
    return True, '订单已取消。'


def simulate_payment(order, buyer_id):
    if order.buyer_id != buyer_id:
        return False, '无权操作此订单。'
    if order.payment_status == 'PAID':
        return True, '该订单已支付。'
    if order.order_status != 'CONFIRMED':
        return False, '订单状态不允许支付。'
    if order.trade_type != 'ONLINE':
        return False, '线下交易无需模拟支付。'

    transaction_no = generate_transaction_no()
    order.payment_status = 'PAID'
    order.paid_at = datetime.utcnow()
    order.order_status = 'PAID'

    notify_b = Notification(
        receiver_id=order.buyer_id, notification_type='ORDER',
        title='支付成功', content=f'订单 {order.order_no} 支付成功。交易编号：{transaction_no}',
        related_id=order.order_id
    )
    notify_s = Notification(
        receiver_id=order.seller_id, notification_type='ORDER',
        title='买家已支付', content=f'订单 {order.order_no} 买家已完成支付。',
        related_id=order.order_id
    )
    db.session.add(notify_b)
    db.session.add(notify_s)
    db.session.commit()
    return True, f'支付成功！交易编号：{transaction_no}'


def buyer_complete_order(order, buyer_id):
    if order.buyer_id != buyer_id:
        return False, '无权操作此订单。'
    if order.order_status == 'COMPLETED':
        return True, '订单已完成。'
    if order.trade_type == 'ONLINE' and order.order_status != 'PAID':
        return False, '请先完成支付。'
    if order.trade_type == 'OFFLINE' and order.order_status != 'CONFIRMED':
        return False, '请等待卖家确认。'

    order.order_status = 'COMPLETED'
    order.completed_at = datetime.utcnow()

    product = db.session.get(Product, order.product_id)
    if product:
        product.product_status = 'SOLD'

    notify = Notification(
        receiver_id=order.seller_id, notification_type='ORDER',
        title='交易完成', content=f'订单 {order.order_no} 买家已确认收货，交易完成。',
        related_id=order.order_id
    )
    db.session.add(notify)
    db.session.commit()
    return True, '交易完成！可以互相评价了。'


def get_buyer_orders(user_id, status_filter=None):
    q = Order.active().filter_by(buyer_id=user_id)
    if status_filter:
        q = q.filter_by(order_status=status_filter)
    return q.order_by(Order.created_at.desc())


def get_seller_orders(user_id, status_filter=None):
    q = Order.active().filter_by(seller_id=user_id)
    if status_filter:
        q = q.filter_by(order_status=status_filter)
    return q.order_by(
        db.case((Order.order_status == 'PENDING', 0), else_=1),
        Order.created_at.desc()
    )
