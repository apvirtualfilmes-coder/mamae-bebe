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
    sexo_bebe = db.Column(db.String(20))
    cor_tema = db.Column(db.String(20), default='rosa')
    modo_noturno = db.Column(db.Boolean, default=False)
    data_nasc_bebe = db.Column(db.Date)
    hora_nasc_bebe = db.Column(db.Time)
    peso_bebe = db.Column(db.Float)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    registros = db.relationship('Registro', backref='usuario', lazy=True, cascade='all, delete-orphan')

class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    lado = db.Column(db.String(20))
    duracao = db.Column(db.String(10))
    cor_coco = db.Column(db.String(50))
    consistencia_coco = db.Column(db.String(50))
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    observacao = db.Column(db.Text)

class DicaCientifica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)