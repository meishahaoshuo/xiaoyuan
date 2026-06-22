from datetime import datetime
from app.extensions import db


class Favorite(db.Model):
    __tablename__ = 'favorite'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='uk_favorite_user_product'),
    )

    favorite_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='收藏编号')
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='用户编号')
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False, comment='商品编号')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Favorite user={self.user_id} product={self.product_id}>'
