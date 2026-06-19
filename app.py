from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from models import db, Usuario, Registro
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-12345')

# Configurar banco de dados
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///mamae_bebe.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Configurar Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Faça login para acessar esta página.'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ========== ROTAS ==========

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Email ou senha incorretos.', 'danger')
    
    return render_template('login.html')

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        nome_bebe = request.form.get('nome_bebe')
        data_nasc = request.form.get('data_nasc')
        hora_nasc = request.form.get('hora_nasc')
        peso = request.form.get('peso')
        
        # Verificar se email já existe
        if Usuario.query.filter_by(email=email).first():
            flash('Este email já está cadastrado.', 'danger')
            return redirect(url_for('cadastrar'))
        
        # Criar usuário
        usuario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha),
            nome_bebe=nome_bebe,
            peso_bebe=float(peso) if peso else None
        )
        
        if data_nasc:
            try:
                usuario.data_nasc_bebe = datetime.strptime(data_nasc, '%Y-%m-%d').date()
            except:
                pass
        
        if hora_nasc:
            try:
                usuario.hora_nasc_bebe = datetime.strptime(hora_nasc, '%H:%M').time()
            except:
                pass
        
        db.session.add(usuario)
        db.session.commit()
        
        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('cadastrar.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Pegar registros de hoje
    hoje = datetime.now().date()
    registros_hoje = Registro.query.filter(
        db.func.date(Registro.data_hora) == hoje,
        Registro.usuario_id == current_user.id
    ).order_by(Registro.data_hora.desc()).all()
    
    # Estatísticas
    stats = {
        'mamadas': sum(1 for r in registros_hoje if r.tipo == 'Mamou'),
        'coco': sum(1 for r in registros_hoje if r.tipo == 'Coco'),
        'xixi': sum(1 for r in registros_hoje if r.tipo == 'Xixi'),
        'regurgito': sum(1 for r in registros_hoje if r.tipo == 'Regurgito'),
        'sono': sum(1 for r in registros_hoje if r.tipo == 'Dormiu')
    }
    
    # Última mamada
    ultima_mamada = Registro.query.filter(
        Registro.tipo == 'Mamou',
        Registro.usuario_id == current_user.id
    ).order_by(Registro.data_hora.desc()).first()
    
    return render_template('dashboard.html', 
                         registros=registros_hoje[:10],
                         stats=stats,
                         ultima_mamada=ultima_mamada)

@app.route('/registrar', methods=['POST'])
@login_required
def registrar():
    tipo = request.form.get('tipo')
    duracao = request.form.get('duracao')
    observacao = request.form.get('observacao')
    
    registro = Registro(
        usuario_id=current_user.id,
        tipo=tipo,
        duracao=duracao,
        observacao=observacao
    )
    
    db.session.add(registro)
    db.session.commit()
    
    flash(f'{tipo} registrado com sucesso!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/cronometro')
@login_required
def cronometro():
    return render_template('cronometro.html')

@app.route('/relatorio')
@login_required
def relatorio():
    # Últimos 7 dias
    hoje = datetime.now().date()
    semana = [hoje - timedelta(days=i) for i in range(7)]
    semana.reverse()
    
    dados = []
    for dia in semana:
        registros = Registro.query.filter(
            db.func.date(Registro.data_hora) == dia,
            Registro.usuario_id == current_user.id
        ).all()
        
        dados.append({
            'data': dia.strftime('%d/%m'),
            'mamadas': sum(1 for r in registros if r.tipo == 'Mamou'),
            'coco': sum(1 for r in registros if r.tipo == 'Coco'),
            'xixi': sum(1 for r in registros if r.tipo == 'Xixi'),
            'sono': sum(1 for r in registros if r.tipo == 'Dormiu')
        })
    
    return render_template('relatorio.html', dados=dados)

@app.route('/api/ultimo_registro')
@login_required
def api_ultimo_registro():
    ultimo = Registro.query.filter_by(usuario_id=current_user.id).order_by(Registro.data_hora.desc()).first()
    if ultimo:
        return jsonify({
            'tipo': ultimo.tipo,
            'data': ultimo.data_hora.strftime('%H:%M')
        })
    return jsonify({'tipo': 'Nenhum', 'data': '--'})

@app.route('/api/registrar_mamada', methods=['POST'])
@login_required
def api_registrar_mamada():
    tempo = request.json.get('tempo')
    duracao = request.json.get('duracao')
    
    registro = Registro(
        usuario_id=current_user.id,
        tipo='Mamou',
        duracao=duracao,
        observacao=f'Tempo total: {tempo}'
    )
    
    db.session.add(registro)
    db.session.commit()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)