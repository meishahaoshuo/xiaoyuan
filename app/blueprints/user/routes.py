from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.blueprints.user import user_bp
from app.services import user_service


@user_bp.route('/profile')
@login_required
def profile():
    stats = user_service.get_user_stats(current_user)
    return render_template('user/profile.html', user=current_user, stats=stats)


@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        avatar = request.files.get('avatar')
        phone = request.form.get('phone', '')
        introduction = request.form.get('introduction', '')
        success, message = user_service.update_profile(
            current_user, phone=phone, introduction=introduction,
            avatar_file=avatar if avatar and avatar.filename else None
        )
        flash(message, 'success' if success else 'danger')
        if success:
            return redirect(url_for('user.profile'))
    return render_template('user/edit_profile.html', user=current_user)
