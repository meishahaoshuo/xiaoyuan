from app.extensions import db
from app.models.user import User
from app.utils.helpers import save_upload


def update_profile(user, phone=None, introduction=None, avatar_file=None):
    if phone is not None:
        user.phone = phone
    if introduction is not None:
        user.introduction = introduction[:500] if introduction else None
    if avatar_file and avatar_file.filename:
        try:
            avatar_path = save_upload(avatar_file, 'avatars', f'user_{user.user_id}')
            if avatar_path:
                user.avatar = avatar_path
        except ValueError as e:
            return False, str(e)
    db.session.commit()
    return True, '个人资料更新成功！'


def get_user_stats(user):
    from app.models.product import Product
    from app.models.review import Review
    product_count = Product.active().filter_by(seller_id=user.user_id).count()
    sold_count = Product.active().filter_by(seller_id=user.user_id, product_status='SOLD').count()
    avg_rating = db.session.query(db.func.avg(Review.score)).filter(
        Review.reviewed_user_id == user.user_id, Review.deleted == False
    ).scalar()
    return {
        'product_count': product_count,
        'sold_count': sold_count,
        'avg_rating': round(float(avg_rating), 1) if avg_rating else None,
        'review_count': Review.active().filter_by(reviewed_user_id=user.user_id).count(),
    }
