from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    nome_bebe = db.Column(db.String(100))
    data_nasc_bebe = db.Column(db.Date)
    hora_nasc_bebe = db.Column(db.Time)
    peso_bebe = db.Column(db.Float)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    registros = db.relationship('Registro', backref='usuario', lazy=True)

class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # Mamou, Coco, Xixi, Regurgito, Dormiu
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    duracao = db.Column(db.String(10))  # Para mamadas (MM:SS)
    observacao = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Registro {self.tipo} - {self.data_hora}>'