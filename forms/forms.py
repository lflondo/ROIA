from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FileField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Regexp
from models.modeluser import ModelUser
import re

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')

def password_check(form, field):
    password = field.data
    if not re.search(r"[A-Z]", password):
        raise ValidationError("La contraseña debe contener al menos una letra mayúscula.")
class RegisterForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Contraseña', validators=[
        DataRequired(), 
        Length(min=8, max=16),
        password_check])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(), 
        EqualTo('password', message='Las contraseñas deben coincidir.')])
    fullname = StringField('Nombre completo', validators=[DataRequired(), Length(min=4, max=50)])
    rol = SelectField('Rol', choices=[('', 'Seleccionar rol'),('usuario', 'Usuario'), ('administrador', 'Administrador')], validators=[DataRequired()])
    submit = SubmitField('Registrar')

class RutaForm(FlaskForm):
    pedido = StringField('Número Pedido', validators=[
        DataRequired(), 
        Length(max=50), 
        Regexp('^[A-Za-z0-9 ]{1,50}$', message="Solo letras, números y espacios. Máximo 50 caracteres.")
    ])
    cliente = StringField('Nombre Cliente', validators=[
        DataRequired(), 
        Length(max=150), 
        Regexp('^[A-Za-z0-9 ]{1,150}$', message="Solo letras, números y espacios. Máximo 150 caracteres.")
    ])
    direccion = StringField('Dirección', validators=[
        DataRequired(), 
        Length(max=100), 
        Regexp('^[A-Za-z0-9 ,.#-]{1,100}$', message="Solo letras, números, espacios y caracteres especiales (,.#-). Máximo 100 caracteres.")
    ])
    telefono = StringField('Teléfono', validators=[
        DataRequired(), 
        Length(min=7, max=15), 
        Regexp('^[0-9]{7,15}$', message="Solo números. Entre 7 y 15 dígitos.")
    ])
    barrio = StringField('Barrio', validators=[
        DataRequired(), 
        Length(max=50), 
        Regexp('^[A-Za-z0-9 ]{1,50}$', message="Solo letras, números, espacios. Máximo 50 caracteres.")
    ])
    ciudad = StringField('Ciudad', validators=[
        DataRequired(), 
        Length(max=50), 
        Regexp('^[A-Za-z ]{1,50}$', message="Solo letras y espacios. Máximo 50 caracteres.")
    ])
    departamento = StringField('Departamento', validators=[
        DataRequired(), 
        Length(max=50), 
        Regexp('^[A-Za-z ]{1,50}$', message="Solo letras y espacios. Máximo 50 caracteres.")
    ])
    pais = StringField('País', default='COLOMBIA', validators=[
        DataRequired(), 
        Length(max=50), 
        Regexp('^[A-Za-z ]{1,50}$', message="Solo letras y espacios. Máximo 50 caracteres.")
    ])
    submit = SubmitField('Guardar')

class EditarRutaForm(FlaskForm):
    nuevo_numero_pedido = StringField('Nuevo Número Pedido', validators=[DataRequired(), 
                                                                        Length(max=50), 
                                                                        Regexp('^[A-Za-z0-9 ]{1,50}$', message="Solo letras, números y espacios. Máximo 50 caracteres.")])
    cliente = StringField('Nombre Cliente', validators=[DataRequired(), 
                                                        Length(max=150), 
                                                        Regexp('^[A-Za-z0-9 ]{1,150}$', message="Solo letras, números y espacios. Máximo 150 caracteres.")])
    telefono = StringField('Teléfono', validators=[DataRequired(), 
                                                   Length(min=10, max=10),
                                                   Regexp('^[0-9]{10}$', message="Solo números. 10 dígitos.")])
    barrio = StringField('Barrio', validators=[DataRequired(), 
                                               Length(max=50),
                                               Regexp('^[A-Za-z0-9 ]{1,50}$', message="Solo letras, números, espacios. Máximo 50 caracteres.")])
    direccion = StringField('Dirección', validators=[DataRequired(),
                                                     Length(max=100),
                                                     Regexp('^[A-Za-z0-9 ,.#-]{1,100}$', message="Solo letras, números, espacios y caracteres especiales (,.#-). Máximo 100 caracteres.")])
    ciudad = StringField('Ciudad', validators=[DataRequired(), 
                                               Length(max=50),
                                               Regexp('^[A-Za-z ]{1,50}$', message="Solo letras y espacios. Máximo 50 caracteres.")])
    departamento = StringField('Departamento', validators=[DataRequired(), 
                                                           Length(max=50),
                                                           Regexp('^[A-Za-z ]{1,50}$', message="Solo letras y espacios. Máximo 50 caracteres.")])
    pais = StringField('País', default='COLOMBIA', validators=[DataRequired(), 
                                                               Length(max=50),
                                                               Regexp('^[A-Za-z ]{1,50}$', message="Solo letras y espacios. Máximo 50 caracteres.")])
    submit = SubmitField('Actualizar')

class CSVUploadForm(FlaskForm):
    file = FileField('Archivo CSV', validators=[DataRequired()])
    submit = SubmitField('Procesar')

class DeleteRutaForm(FlaskForm):
    numero_pedido = StringField('Número Pedido', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Eliminar')