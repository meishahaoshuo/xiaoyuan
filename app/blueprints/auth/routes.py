from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import (
    LoginForm, RegisterForm, ForgotPasswordForm,
    ResetPasswordForm, ChangePasswordForm
)
from app.services import auth_service


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('browse.home'))
    form = LoginForm()
    if form.validate_on_submit():
        success, message, user = auth_service.authenticate_user(
            form.username.data, form.password.data
        )
        if success:
            login_user(user, remember=True)
            flash(message, 'success')
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('browse.home'))
        flash(message, 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('browse.home'))
    form = RegisterForm()
    if form.validate_on_submit():
        success, message, user = auth_service.register_user(
            form.username.data, form.password.data, form.phone.data
        )
        if success:
            login_user(user, remember=True)
            flash(message, 'success')
            return redirect(url_for('browse.home'))
        flash(message, 'danger')
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('您已退出登录。', 'info')
    return redirect(url_for('browse.home'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('browse.home'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        otp = auth_service.generate_otp(form.username.data)
        flash(f'验证码已生成（演示模式）：{otp}', 'info')
        session['reset_username'] = form.username.data
        return redirect(url_for('auth.reset_password'))
    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('browse.home'))
    username = session.get('reset_username', '')
    if not username:
        flash('请先输入用户名获取验证码。', 'warning')
        return redirect(url_for('auth.forgot_password'))
    form = ResetPasswordForm(username=username)
    if form.validate_on_submit():
        success, message = auth_service.verify_otp(username, form.otp.data)
        if success:
            success2, message2 = auth_service.reset_password(
                username, form.new_password.data
            )
            if success2:
                session.pop('reset_username', None)
                flash(message2, 'success')
                return redirect(url_for('auth.login'))
            flash(message2, 'danger')
        else:
            flash(message, 'danger')
    return render_template('auth/reset_password.html', form=form)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        success, message = auth_service.change_password(
            current_user, form.old_password.data, form.new_password.data
        )
        flash(message, 'success' if success else 'danger')
        if success:
            return redirect(url_for('user.profile'))
    return render_template('auth/change_password.html', form=form)
