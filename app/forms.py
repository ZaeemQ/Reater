from wtforms import Form , TextField, TextAreaField, validators, StringField, SubmitField

class RestySearchForm(Form):
    name = TextField('Name:', validators=[validators.required()])

class RegisterForm( Form ):
    name = TextField('Name:', validators=[validators.required()])
    email = TextField('Email:',validators=[validators.required()])