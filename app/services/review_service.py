from app.extensions import db
from app.models.review import Review
from app.models.orders import Order


def submit_review(order_id, reviewer_id, score, content=None):
    order = db.session.get(Order, order_id)
    if not order or order.deleted:
        return False, '订单不存在。'
    if order.order_status != 'COMPLETED':
        return False, '只能评价已完成的订单。'
    if reviewer_id not in (order.buyer_id, order.seller_id):
        return False, '无权评价此订单。'

    reviewed_user_id = order.seller_id if reviewer_id == order.buyer_id else order.buyer_id

    existing = Review.active().filter_by(order_id=order_id, reviewer_id=reviewer_id).first()
    if existing:
        return False, '您已经评价过此订单。'
    if score < 1 or score > 5:
        return False, '评分必须在1~5之间。'

    review = Review(
        order_id=order_id, reviewer_id=reviewer_id,
        reviewed_user_id=reviewed_user_id, score=score,
        review_content=content.strip()[:1000] if content else None
    )
    db.session.add(review)
    db.session.commit()
    return True, '评价提交成功！'


def get_user_reviews(user_id):
    return Review.active().filter_by(reviewed_user_id=user_id).order_by(
        Review.created_at.desc()).all()


def has_reviewed(order_id, reviewer_id):
    return Review.active().filter_by(
        order_id=order_id, reviewer_id=reviewer_id).first() is not None
