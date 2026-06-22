from datetime import datetime
from app.extensions import db


class Category(db.Model):
    __tablename__ = 'category'

    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='分类编号')
    category_name = db.Column(db.String(100), unique=True, nullable=False, comment='分类名称')
    description = db.Column(db.String(500), nullable=True, comment='分类描述')
    status = db.Column(db.String(20), nullable=False, default='ENABLED', comment='分类状态')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    products = db.relationship('Product', backref='category', lazy='dynamic')

    @classmethod
    def enabled(cls):
        return cls.query.filter_by(status='ENABLED')

    @property
    def product_count(self):
        from app.models.product import Product
        return Product.active().filter(
            Product.category_id == self.category_id,
            Product.product_status.in_(['ON_SALE', 'PENDING_REVIEW'])
        ).count()

    def __repr__(self):
        return f'<Category {self.category_name}>'
