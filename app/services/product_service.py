from app.extensions import db
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.orders import Order
from app.utils.helpers import save_upload


def create_product(seller_id, name, category_id, price, condition_level,
                   description, trade_location, images=None, submit=False):
    if not name or len(name.strip()) < 1:
        return False, '商品名称不能为空。', None
    if len(name) > 150:
        return False, '商品名称不能超过150个字符。', None
    if price < 0.01 or price > 99999.99:
        return False, '价格必须在0.01~99999.99之间。', None
    if len(description) < 10 or len(description) > 1000:
        return False, '商品描述需要10~1000个字符。', None

    status = 'PENDING_REVIEW' if submit else 'DRAFT'
    product = Product(
        seller_id=seller_id, category_id=category_id,
        product_name=name.strip(), price=price,
        condition_level=condition_level, description=description.strip(),
        trade_location=trade_location.strip(), product_status=status
    )
    db.session.add(product)
    db.session.flush()

    if images:
        valid, msg = validate_images(images)
        if not valid:
            db.session.rollback()
            return False, msg, None
        save_product_images(product.product_id, images)

    db.session.commit()
    return True, '商品发布成功！' if submit else '草稿保存成功！', product


def validate_images(images):
    if not images or all(not f or not f.filename for f in images):
        return True, ''
    valid_images = [f for f in images if f and f.filename]
    if len(valid_images) > 6:
        return False, '最多只能上传6张图片。'
    for f in valid_images:
        ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
        if ext not in {'jpg', 'jpeg', 'png', 'webp'}:
            return False, f'不支持的图片格式: .{ext}，仅支持 JPG/PNG/WebP。'
        f.seek(0, 2)
        size = f.tell()
        f.seek(0)
        if size > 5 * 1024 * 1024:
            return False, f'图片 {f.filename} 超过5MB限制。'
    return True, ''


def save_product_images(product_id, images):
    valid_images = [f for f in images if f and f.filename]
    for idx, f in enumerate(valid_images):
        try:
            path = save_upload(f, 'products', f'product_{product_id}')
            if path:
                img = ProductImage(product_id=product_id, image_url=path, sort_order=idx)
                db.session.add(img)
        except ValueError:
            continue


def update_product(product, name, category_id, price, condition_level,
                   description, trade_location, images=None, submit=False):
    if product.product_status in ('SOLD',):
        return False, '已售出的商品无法修改。'
    if not name or len(name.strip()) < 1:
        return False, '商品名称不能为空。'
    if price < 0.01 or price > 99999.99:
        return False, '价格必须在0.01~99999.99之间。'
    if len(description) < 10 or len(description) > 1000:
        return False, '商品描述需要10~1000个字符。'

    product.product_name = name.strip()
    product.category_id = category_id
    product.price = price
    product.condition_level = condition_level
    product.description = description.strip()
    product.trade_location = trade_location.strip()

    if product.product_status in ('APPROVED', 'ON_SALE', 'OFF_SHELF'):
        product.product_status = 'PENDING_REVIEW' if submit else 'DRAFT'
    elif submit:
        product.product_status = 'PENDING_REVIEW'

    if images and any(f and f.filename for f in images):
        valid, msg = validate_images(images)
        if not valid:
            return False, msg
        old_images = ProductImage.query.filter_by(product_id=product.product_id).all()
        for old in old_images:
            db.session.delete(old)
        save_product_images(product.product_id, images)

    db.session.commit()
    return True, '商品更新成功！'


def delete_product(product):
    if product.product_status == 'SOLD':
        return False, '已售出的商品无法删除。'
    active_order = Order.active().filter(
        Order.product_id == product.product_id,
        Order.order_status.in_(['PENDING', 'CONFIRMED', 'PAID'])
    ).first()
    if active_order:
        return False, '该商品存在进行中的订单，无法删除。'
    product.deleted = True
    if product.product_status == 'ON_SALE':
        product.product_status = 'OFF_SHELF'
    db.session.commit()
    return True, '商品已删除。'


def toggle_product_status(product, target_status=None):
    if product.product_status == 'DRAFT':
        product.product_status = 'PENDING_REVIEW'
        db.session.commit()
        return True, '商品已提交审核。'
    elif product.product_status == 'ON_SALE':
        product.product_status = 'OFF_SHELF'
        db.session.commit()
        return True, '商品已下架。'
    elif product.product_status == 'OFF_SHELF':
        product.product_status = 'ON_SALE'
        db.session.commit()
        return True, '商品已上架。'
    elif product.product_status == 'PENDING_REVIEW':
        return False, '商品正在审核中，请耐心等待。'
    elif product.product_status == 'REJECTED':
        product.product_status = 'PENDING_REVIEW'
        db.session.commit()
        return True, '商品已重新提交审核。'
    else:
        return False, '当前状态无法变更。'


def get_my_products(user_id, status_filter=None):
    q = Product.active().filter_by(seller_id=user_id)
    if status_filter:
        q = q.filter_by(product_status=status_filter)
    return q.order_by(Product.created_at.desc())
