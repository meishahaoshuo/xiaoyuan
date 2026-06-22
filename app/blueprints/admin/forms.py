from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length


class AdminLoginForm(FlaskForm):
    username = StringField('管理员用户名', validators=[DataRequired('请输入用户名')])
    password = PasswordField('密码', validators=[DataRequired('请输入密码')])
    submit = SubmitField('管理员登录')


class RejectProductForm(FlaskForm):
    reason = TextAreaField('驳回原因', validators=[
        DataRequired('请输入驳回原因'),
        Length(min=2, max=500)
    ])
    submit = SubmitField('确认驳回')


class CategoryForm(FlaskForm):
    category_name = StringField('分类名称', validators=[
        DataRequired('请输入分类名称'),
        Length(min=2, max=100)
    ])
    description = TextAreaField('分类描述（选填）', validators=[Length(max=500)])
    submit = SubmitField('保存')


class HandleReportForm(FlaskForm):
    action = SelectField('处理方式', choices=[
        ('DISMISSED', '驳回举报'),
        ('TAKEDOWN', '下架商品/封禁用户'),
        ('DISABLED', '禁用用户'),
    ], validators=[DataRequired('请选择处理方式')])
    handle_result = TextAreaField('处理说明（选填）', validators=[Length(max=1000)])
    submit = SubmitField('确认处理')
