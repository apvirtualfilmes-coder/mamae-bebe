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
    altura_bebe = db.Column(db.Float)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    registros = db.relationship('Registro', backref='usuario', lazy=True, cascade='all, delete-orphan')
    bichinho = db.relationship('BichinhoVirtual', backref='usuario', lazy=True, uselist=False)
    pesos = db.relationship('PesoRegistro', backref='usuario', lazy=True, cascade='all, delete-orphan')
    vacinas = db.relationship('Vacina', backref='usuario', lazy=True, cascade='all, delete-orphan')
    banhos = db.relationship('Banho', backref='usuario', lazy=True, cascade='all, delete-orphan')

class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    lado = db.Column(db.String(20))
    duracao = db.Column(db.String(10))
    cor_coco = db.Column(db.String(50))
    consistencia_coco = db.Column(db.String(50))
    temperatura = db.Column(db.Float)
    nariz_entupido = db.Column(db.Boolean, default=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    observacao = db.Column(db.Text)

class BichinhoVirtual(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    humor = db.Column(db.String(50), default='neutro')
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow)
    nivel_felicidade = db.Column(db.Integer, default=50)
    nivel_fome = db.Column(db.Integer, default=50)
    nivel_sono = db.Column(db.Integer, default=50)
    nivel_energia = db.Column(db.Integer, default=50)
    nivel_saude = db.Column(db.Integer, default=50)

class PesoRegistro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    peso = db.Column(db.Float, nullable=False)
    altura = db.Column(db.Float)
    data = db.Column(db.Date, default=datetime.utcnow().date)
    observacao = db.Column(db.Text)

class Vacina(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    data_aplicacao = db.Column(db.Date)
    proxima_dose = db.Column(db.Date)
    aplicada = db.Column(db.Boolean, default=False)
    observacao = db.Column(db.Text)

class Banho(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    duracao = db.Column(db.String(10))
    observacao = db.Column(db.Text)

class DicaCientifica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)