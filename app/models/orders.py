from datetime import datetime
from app.extensions import db
from sqlalchemy import CheckConstraint


class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = (
        CheckConstraint('order_amount >= 0', name='chk_orders_amount'),
        CheckConstraint('buyer_id <> seller_id', name='chk_orders_users'),
    )

    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='订单编号')
    order_no = db.Column(db.String(50), unique=True, nullable=False, comment='订单业务编号')
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False, comment='商品编号')
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='买家编号')
    seller_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='卖家编号')
    order_amount = db.Column(db.Numeric(10, 2), nullable=False, comment='订单金额')
    trade_type = db.Column(db.String(20), nullable=False, comment='交易方式')
    buyer_message = db.Column(db.String(500), nullable=True, comment='买家留言')
    order_status = db.Column(db.String(30), nullable=False, default='PENDING', comment='订单状态')
    payment_status = db.Column(db.String(30), nullable=False, default='UNPAID', comment='支付状态')
    reject_reason = db.Column(db.String(500), nullable=True, comment='拒绝原因')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True, comment='支付时间')
    completed_at = db.Column(db.DateTime, nullable=True, comment='完成时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted = db.Column(db.Boolean, nullable=False, default=False, comment='逻辑删除标志')

    # Relationships
    reviews = db.relationship('Review', backref='order', lazy='dynamic')

    # Valid order status transitions
    VALID_TRANSITIONS = {
        'PENDING': ['CONFIRMED', 'REJECTED', 'CANCELLED'],
        'CONFIRMED': ['CANCELLED', 'PAID'],
        'PAID': ['COMPLETED'],
        'COMPLETED': [],
        'CANCELLED': [],
        'REJECTED': [],
    }

    STATUS_DISPLAY = {
        'PENDING': '待确认',
        'CONFIRMED': '已确认',
        'PAID': '已支付',
        'COMPLETED': '已完成',
        'CANCELLED': '已取消',
        'REJECTED': '已拒绝',
    }

    @classmethod
    def active(cls):
        return cls.query.filter_by(deleted=False)

    def can_transition_to(self, target_status):
        return target_status in self.VALID_TRANSITIONS.get(self.order_status, [])

    @property
    def status_display(self):
        return self.STATUS_DISPLAY.get(self.order_status, self.order_status)

    def __repr__(self):
        return f'<Order {self.order_no}>'
