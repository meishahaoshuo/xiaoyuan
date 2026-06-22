from datetime import datetime, timedelta
from app.extensions import db
from app.models.user import User
from app.models.product import Product
from app.models.orders import Order
from app.models.category import Category
from app.models.report import Report
from app.models.notification import Notification


def get_dashboard_stats(start_date=None, end_date=None):
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    total_users = User.active().count()
    active_users = User.active().filter_by(status='ACTIVE').count()
    total_products = Product.active().count()
    on_sale_products = Product.on_sale().count()

    total_orders = Order.active().filter(
        Order.created_at >= start_date, Order.created_at <= end_date).count()
    completed_orders = Order.active().filter(
        Order.order_status == 'COMPLETED',
        Order.created_at >= start_date, Order.created_at <= end_date).count()
    completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0

    return {
        'total_users': total_users, 'active_users': active_users,
        'disabled_users': total_users - active_users,
        'total_products': total_products, 'on_sale_products': on_sale_products,
        'total_orders': total_orders, 'completed_orders': completed_orders,
        'completion_rate': round(completion_rate, 1),
        'pending_reports': Report.query.filter_by(report_status='PENDING').count(),
        'pending_products': Product.active().filter_by(product_status='PENDING_REVIEW').count(),
    }


def get_category_distribution():
    results = db.session.query(
        Category.category_name,
        db.func.count(Product.product_id)
    ).outerjoin(Product, db.and_(
        Product.category_id == Category.category_id, Product.deleted == False)
    ).group_by(Category.category_id).all()
    return [{'name': name, 'count': count} for name, count in results]


def toggle_user_status(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return False, '用户不存在。'
    if user.role == 'ADMIN':
        return False, '不能禁用管理员账号。'
    if user.status == 'ACTIVE':
        user.status = 'DISABLED'
        Product.active().filter_by(seller_id=user_id).update(
            {'product_status': 'OFF_SHELF'}, synchronize_session='fetch')
        db.session.commit()
        return True, f'用户 {user.username} 已被禁用。'
    else:
        user.status = 'ACTIVE'
        db.session.commit()
        return True, f'用户 {user.username} 已启用。'


def review_product(product_id, action, reason=None):
    product = db.session.get(Product, product_id)
    if not product:
        return False, '商品不存在。'
    if product.product_status != 'PENDING_REVIEW':
        return False, '该商品不在待审核状态。'

    if action == 'approve':
        product.product_status = 'ON_SALE'
        notif = Notification(
            receiver_id=product.seller_id, notification_type='SYSTEM',
            title='商品审核通过',
            content=f'您的商品「{product.product_name}」已通过审核，已自动上架。',
            related_id=product.product_id)
        db.session.add(notif)
        db.session.commit()
        return True, '商品已通过审核并上架。'
    else:
        if not reason or len(reason.strip()) < 2:
            return False, '驳回原因至少需要2个字符。'
        product.product_status = 'REJECTED'
        notif = Notification(
            receiver_id=product.seller_id, notification_type='SYSTEM',
            title='商品审核未通过',
            content=f'您的商品「{product.product_name}」未通过审核。原因：{reason}',
            related_id=product.product_id)
        db.session.add(notif)
        db.session.commit()
        return True, '商品已驳回。'


def admin_takedown_product(product_id, permanent=False):
    product = db.session.get(Product, product_id)
    if not product:
        return False, '商品不存在。'
    if permanent:
        active_order = Order.active().filter(
            Order.product_id == product_id,
            Order.order_status.in_(['PENDING', 'CONFIRMED', 'PAID'])).first()
        if active_order:
            return False, '存在进行中的订单，无法永久删除。'
        product.deleted = True
        product.product_status = 'OFF_SHELF'
        db.session.commit()
        return True, '商品已永久删除。'
    else:
        product.product_status = 'OFF_SHELF'
        db.session.commit()
        return True, '商品已下架。'


def manage_category(action, category_id=None, name=None, description=None):
    if action == 'create':
        if not name or not name.strip():
            return False, '分类名称不能为空。'
        existing = Category.query.filter_by(category_name=name.strip()).first()
        if existing:
            return False, '分类名称已存在。'
        cat = Category(category_name=name.strip(), description=description)
        db.session.add(cat)
        db.session.commit()
        return True, f'分类「{name}」已创建。'

    cat = db.session.get(Category, category_id)
    if not cat:
        return False, '分类不存在。'

    if action == 'update':
        if name:
            cat.category_name = name.strip()
        if description is not None:
            cat.description = description
        db.session.commit()
        return True, '分类已更新。'
    elif action == 'toggle':
        cat.status = 'DISABLED' if cat.status == 'ENABLED' else 'ENABLED'
        db.session.commit()
        return True, f'分类已{"禁用" if cat.status == "DISABLED" else "启用"}。'
    elif action == 'delete':
        product_count = Product.active().filter_by(category_id=category_id).count()
        if product_count > 0:
            cat.status = 'DISABLED'
            db.session.commit()
            return False, f'该分类下有{product_count}个商品，已禁用而非删除。'
        db.session.delete(cat)
        db.session.commit()
        return True, '分类已删除。'

    return False, '无效操作。'
