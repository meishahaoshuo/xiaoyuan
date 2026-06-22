from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Optional


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired('请输入用户名')])
    password = PasswordField('密码', validators=[DataRequired('请输入密码')])
    submit = SubmitField('登录')


class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[
        DataRequired('请输入用户名'),
        Length(min=2, max=50, message='用户名长度2~50个字符')
    ])
    password = PasswordField('密码', validators=[
        DataRequired('请输入密码'),
        Length(min=6, max=128, message='密码至少6个字符')
    ])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired('请确认密码'),
        EqualTo('password', message='两次密码不一致')
    ])
    phone = StringField('手机号（选填）', validators=[Optional(), Length(max=30)])
    submit = SubmitField('注册')


class ForgotPasswordForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired('请输入用户名')])
    submit = SubmitField('获取验证码')


class ResetPasswordForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    otp = StringField('验证码', validators=[DataRequired('请输入验证码'), Length(min=6, max=6)])
    new_password = PasswordField('新密码', validators=[
        DataRequired('请输入新密码'),
        Length(min=6, max=128, message='密码至少6个字符')
    ])
    submit = SubmitField('重置密码')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('旧密码', validators=[DataRequired('请输入旧密码')])
    new_password = PasswordField('新密码', validators=[
        DataRequired('请输入新密码'),
        Length(min=6, max=128, message='新密码至少6个字符')
    ])
    confirm_password = PasswordField('确认新密码', validators=[
        DataRequired('请确认新密码'),
        EqualTo('new_password', message='两次密码不一致')
    ])
    submit = SubmitField('修改密码')
