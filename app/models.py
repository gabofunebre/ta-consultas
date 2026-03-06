from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()

ESTADOS_CONSULTA = [
    'Nueva',
    'Atendido',
    'Presupuestado',
    'Seguimiento',
    'Ganada',
    'Perdida',
]


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='vendedor')
    activo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    consultas = db.relationship('Consulta', back_populates='responsable', lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Consulta(db.Model):
    __tablename__ = 'consultas'

    id = db.Column(db.Integer, primary_key=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    canal = db.Column(db.String(20), nullable=False)
    nombre_contacto = db.Column(db.String(120), nullable=False)
    telefono_o_email = db.Column(db.String(120), nullable=False)
    texto_consulta = db.Column(db.Text, nullable=False)
    estado_actual = db.Column(db.String(30), nullable=False, default='Nueva')
    responsable_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    observaciones_opcionales = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    responsable = db.relationship('User', back_populates='consultas')
    adjuntos = db.relationship('Adjunto', back_populates='consulta', cascade='all, delete-orphan', lazy=True)
    historial = db.relationship('HistorialActividad', back_populates='consulta', cascade='all, delete-orphan', lazy=True)


class Adjunto(db.Model):
    __tablename__ = 'adjuntos'

    id = db.Column(db.Integer, primary_key=True)
    consulta_id = db.Column(db.Integer, db.ForeignKey('consultas.id'), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    ruta_archivo = db.Column(db.String(500), nullable=False)
    tipo_mime = db.Column(db.String(120), nullable=False)
    fecha_subida = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    usuario_que_subio = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    consulta = db.relationship('Consulta', back_populates='adjuntos')


class HistorialActividad(db.Model):
    __tablename__ = 'historial_actividad'

    id = db.Column(db.Integer, primary_key=True)
    consulta_id = db.Column(db.Integer, db.ForeignKey('consultas.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tipo_evento = db.Column(db.String(80), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    consulta = db.relationship('Consulta', back_populates='historial')
