from datetime import datetime
from app.extensions import db
from app.models.report import Report
from app.models.product import Product
from app.models.user import User


def submit_report(reporter_id, target_type, target_id, reason, description=None):
    if not reason or len(reason.strip()) < 2:
        return False, '举报原因至少需要2个字符。'
    existing = Report.query.filter_by(
        reporter_id=reporter_id, target_type=target_type,
        target_id=target_id, report_status='PENDING'
    ).first()
    if existing:
        return False, '您已有一个待处理的举报，请等待管理员处理。'

    report = Report(
        reporter_id=reporter_id, target_type=target_type, target_id=target_id,
        report_reason=reason.strip(),
        description=description.strip()[:1000] if description else None,
        report_status='PENDING'
    )
    db.session.add(report)
    db.session.commit()
    return True, '举报提交成功，管理员将尽快处理。'


def handle_report(report_id, handler_id, action, handle_result=None):
    report = db.session.get(Report, report_id)
    if not report:
        return False, '举报不存在。'
    if report.report_status != 'PENDING':
        return False, '该举报已被处理。'

    report.report_status = action
    report.handler_id = handler_id
    report.handled_at = datetime.utcnow()
    report.handle_result = handle_result

    if action == 'TAKEDOWN' and report.target_type == 'PRODUCT':
        product = db.session.get(Product, report.target_id)
        if product:
            product.product_status = 'OFF_SHELF'
    elif action == 'DISABLED' and report.target_type == 'USER':
        user = db.session.get(User, report.target_id)
        if user:
            user.status = 'DISABLED'
            Product.active().filter_by(seller_id=user.user_id).update(
                {'product_status': 'OFF_SHELF'}, synchronize_session='fetch')

    db.session.commit()
    return True, '举报已处理。'
