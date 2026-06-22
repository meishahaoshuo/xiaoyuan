from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.blueprints.product import product_bp
from app.blueprints.product.forms import ProductForm
from app.models.product import Product
from app.models.category import Category
from app.services import product_service
from app.utils.pagination import paginate


@product_bp.route('/publish', methods=['GET', 'POST'])
@login_required
def publish():
    form = ProductForm()
    form.category_id.choices = [
        (c.category_id, c.category_name)
        for c in Category.enabled().order_by(Category.category_name).all()
    ]
    if form.validate_on_submit():
        images = request.files.getlist('images')
        submit = form.submit_publish.data
        success, message, product = product_service.create_product(
            seller_id=current_user.user_id,
            name=form.product_name.data,
            category_id=form.category_id.data,
            price=float(form.price.data),
            condition_level=form.condition_level.data,
            description=form.description.data,
            trade_location=form.trade_location.data,
            images=images if any(f and f.filename for f in images) else None,
            submit=bool(submit)
        )
        flash(message, 'success' if success else 'danger')
        if success:
            return redirect(url_for('product.my_products'))
    return render_template('product/publish.html', form=form, categories=form.category_id.choices)


@product_bp.route('/my')
@login_required
def my_products():
    status = request.args.get('status', '')
    products = product_service.get_my_products(current_user.user_id, status_filter=status or None)
    pagination = paginate(products)
    return render_template('product/my_products.html',
                         products=pagination.items, pagination=pagination,
                         current_filter=status)


@product_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    product = db.session.get(Product, id)
    if not product or product.deleted:
        flash('商品不存在。', 'danger')
        return redirect(url_for('product.my_products'))
    if product.seller_id != current_user.user_id:
        flash('无权编辑此商品。', 'danger')
        return redirect(url_for('product.my_products'))

    form = ProductForm(obj=product)
    form.category_id.choices = [
        (c.category_id, c.category_name)
        for c in Category.enabled().order_by(Category.category_name).all()
    ]
    if not form.is_submitted():
        form.category_id.data = product.category_id
        form.condition_level.data = product.condition_level

    if form.validate_on_submit():
        images = request.files.getlist('images')
        submit = form.submit_publish.data
        success, message = product_service.update_product(
            product=product,
            name=form.product_name.data,
            category_id=form.category_id.data,
            price=float(form.price.data),
            condition_level=form.condition_level.data,
            description=form.description.data,
            trade_location=form.trade_location.data,
            images=images if any(f and f.filename for f in images) else None,
            submit=bool(submit)
        )
        flash(message, 'success' if success else 'danger')
        if success:
            return redirect(url_for('product.my_products'))
    return render_template('product/edit.html', form=form, product=product)


@product_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    product = db.session.get(Product, id)
    if not product or product.deleted:
        flash('商品不存在。', 'danger')
        return redirect(url_for('product.my_products'))
    if product.seller_id != current_user.user_id:
        flash('无权操作。', 'danger')
        return redirect(url_for('product.my_products'))
    success, message = product_service.delete_product(product)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('product.my_products'))


@product_bp.route('/toggle/<int:id>', methods=['POST'])
@login_required
def toggle(id):
    product = db.session.get(Product, id)
    if not product or product.deleted:
        flash('商品不存在。', 'danger')
        return redirect(url_for('product.my_products'))
    if product.seller_id != current_user.user_id:
        flash('无权操作。', 'danger')
        return redirect(url_for('product.my_products'))
    success, message = product_service.toggle_product_status(product)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('product.my_products'))
