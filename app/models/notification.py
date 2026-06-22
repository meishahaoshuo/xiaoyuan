from datetime import datetime
from app.extensions import db


class Notification(db.Model):
    __tablename__ = 'notification'

    notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='通知编号')
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, comment='接收者编号')
    notification_type = db.Column(db.String(30), nullable=False, comment='通知类型')
    title = db.Column(db.String(200), nullable=False, comment='通知标题')
    content = db.Column(db.Text, nullable=False, comment='通知内容')
    related_id = db.Column(db.Integer, nullable=True, comment='关联业务编号')
    read_status = db.Column(db.Boolean, nullable=False, default=False, comment='阅读状态')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    deleted = db.Column(db.Boolean, nullable=False, default=False, comment='逻辑删除标志')

    TYPE_DISPLAY = {
        'SYSTEM': '系统通知',
        'ORDER': '订单通知',
        'REPORT': '举报通知',
    }

    @classmethod
    def active(cls):
        return cls.query.filter_by(deleted=False)

    @property
    def type_display(self):
        return self.TYPE_DISPLAY.get(self.notification_type, self.notification_type)

    def __repr__(self):
        return f'<Notification {self.notification_id} type={self.notification_type}>'
