from datetime import datetime
from app.extensions import db


class ProductImage(db.Model):
    __tablename__ = 'product_image'

    image_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='图片编号')
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False, comment='商品编号')
    image_url = db.Column(db.String(500), nullable=False, comment='图片地址')
    sort_order = db.Column(db.Integer, nullable=False, default=0, comment='排序号')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<ProductImage {self.image_id} for product {self.product_id}>'
