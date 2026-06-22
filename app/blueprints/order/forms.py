from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, RadioField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class OrderForm(FlaskForm):
    trade_type = RadioField('交易方式', choices=[
        ('OFFLINE', '线下交易（当面验货）'),
        ('ONLINE', '线上交易（模拟支付）'),
    ], validators=[DataRequired('请选择交易方式')])
    buyer_message = TextAreaField('买家留言（选填）', validators=[
        Optional(), Length(max=200, message='留言不超过200个字符')
    ])
    submit = SubmitField('提交订单')


class RejectForm(FlaskForm):
    reason = TextAreaField('拒绝原因', validators=[
        DataRequired('请输入拒绝原因'),
        Length(min=2, max=100, message='拒绝原因2~100个字符')
    ])
    submit = SubmitField('确认拒绝')
