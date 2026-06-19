from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from models import db, Usuario, Registro, DicaCientifica
import os
from dotenv import load_dotenv
<<<<<<< HEAD
=======
import json
>>>>>>> 5014e6570a2a085a24368cbedb0320496d845b24

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-12345')

# Configurar banco de dados
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///leag_baby.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Criar tabelas
with app.app_context():
    try:
        db.create_all()
        print("✅ Tabelas criadas com sucesso!")
        
        # Inserir dicas científicas se não existirem
        if DicaCientifica.query.count() == 0:
            dicas = [
                {
                    'titulo': 'Amamentação em livre demanda',
                    'descricao': 'Estudos da OMS mostram que amamentação em livre demanda nos primeiros 6 meses reduz em 40% o risco de infecções respiratórias.',
                    'categoria': 'amamentacao'
                },
                {
                    'titulo': 'Benefícios do contato pele a pele',
                    'descricao': 'Pesquisas da UNICEF indicam que o contato pele a pele na primeira hora de vida aumenta em 80% as chances de amamentação exclusiva.',
                    'categoria': 'contato'
                },
                {
                    'titulo': 'Sono do recém-nascido',
                    'descricao': 'Estudo da American Academy of Pediatrics mostra que recém-nascidos que dormem no mesmo quarto dos pais têm 50% menos risco de morte súbita.',
                    'categoria': 'sono'
                },
                {
                    'titulo': 'Cólica do bebê',
                    'descricao': 'Pesquisa da Universidade de Bristol indica que massagem na barriga reduz em 60% os episódios de cólica em bebês.',
                    'categoria': 'saude'
                },
                {
                    'titulo': 'Importância do leite materno',
                    'descricao': 'Estudo do Lancet mostrou que o aleitamento materno exclusivo até 6 meses reduz em 45% o risco de diarreia e infecções.',
                    'categoria': 'amamentacao'
                },
                {
                    'titulo': 'Desenvolvimento cerebral',
                    'descricao': 'Pesquisas da Harvard University indicam que o cérebro do bebê dobra de tamanho no primeiro ano, exigindo nutrientes essenciais do leite materno.',
                    'categoria': 'desenvolvimento'
                }
            ]
            
            for dica in dicas:
                nova_dica = DicaCientifica(
                    titulo=dica['titulo'],
                    descricao=dica['descricao'],
                    categoria=dica['categoria']
                )
                db.session.add(nova_dica)
            
            db.session.commit()
            print("✅ Dicas científicas inseridas!")
            
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")

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
        try:
            email = request.form.get('email')
            senha = request.form.get('senha')
            
            usuario = Usuario.query.filter_by(email=email).first()
            
            if usuario and check_password_hash(usuario.senha, senha):
                login_user(usuario)
                
                # Salvar preferências na sessão
                session['modo_noturno'] = usuario.modo_noturno
                session['cor_tema'] = usuario.cor_tema
                
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
            
            flash('Email ou senha incorretos.', 'danger')
        except Exception as e:
            flash(f'Erro ao fazer login: {str(e)}', 'danger')
    
    return render_template('login.html')

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            nome = request.form.get('nome')
            email = request.form.get('email')
            senha = request.form.get('senha')
            nome_bebe = request.form.get('nome_bebe')
            sexo_bebe = request.form.get('sexo_bebe')
            data_nasc = request.form.get('data_nasc')
            hora_nasc = request.form.get('hora_nasc')
            peso = request.form.get('peso')
            
            # Validar
            if not nome or not email or not senha:
                flash('Nome, email e senha são obrigatórios.', 'danger')
                return redirect(url_for('cadastrar'))
            
            if Usuario.query.filter_by(email=email).first():
                flash('Este email já está cadastrado.', 'danger')
                return redirect(url_for('cadastrar'))
            
            # Determinar cor do tema
            cor_tema = 'azul' if sexo_bebe == 'masculino' else 'rosa'
            
            usuario = Usuario(
                nome=nome,
                email=email,
                senha=generate_password_hash(senha),
                nome_bebe=nome_bebe if nome_bebe else None,
                sexo_bebe=sexo_bebe,
                cor_tema=cor_tema,
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
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar: {str(e)}', 'danger')
            return redirect(url_for('cadastrar'))
    
    return render_template('cadastrar.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Atualizar preferências na sessão
        session['modo_noturno'] = current_user.modo_noturno
        session['cor_tema'] = current_user.cor_tema
        
        hoje = datetime.now().date()
        registros_hoje = Registro.query.filter(
            db.func.date(Registro.data_hora) == hoje,
            Registro.usuario_id == current_user.id
        ).order_by(Registro.data_hora.desc()).all()
        
        # Calcular idade exata
        idade = calcular_idade_exata(current_user)
        
        # Estatísticas
        stats = {
            'mamadas': sum(1 for r in registros_hoje if r.tipo == 'Mamou'),
            'mamadas_direito': sum(1 for r in registros_hoje if r.tipo == 'Mamou' and r.lado == 'direito'),
            'mamadas_esquerdo': sum(1 for r in registros_hoje if r.tipo == 'Mamou' and r.lado == 'esquerdo'),
            'coco': sum(1 for r in registros_hoje if r.tipo == 'Coco'),
            'xixi': sum(1 for r in registros_hoje if r.tipo == 'Xixi'),
            'regurgito': sum(1 for r in registros_hoje if r.tipo == 'Regurgito'),
            'sono': sum(1 for r in registros_hoje if r.tipo == 'Dormiu')
        }
        
        # Análise de mamadas
        alerta_mamada = verificar_mamadas(stats['mamadas'])
        
        # Última mamada
        ultima_mamada = Registro.query.filter(
            Registro.tipo == 'Mamou',
            Registro.usuario_id == current_user.id
        ).order_by(Registro.data_hora.desc()).first()
        
        # Buscar dica científica relevante
        dica = buscar_dica_cientifica(stats)
        
        return render_template('dashboard.html', 
                             registros=registros_hoje[:10],
                             stats=stats,
                             ultima_mamada=ultima_mamada,
                             datetime=datetime,
                             idade=idade,
                             alerta_mamada=alerta_mamada,
                             dica=dica)
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {str(e)}', 'danger')
        return render_template('dashboard.html', registros=[], stats={}, ultima_mamada=None, datetime=datetime)

@app.route('/registrar', methods=['POST'])
@login_required
def registrar():
    try:
        tipo = request.form.get('tipo')
        lado = request.form.get('lado')
        duracao = request.form.get('duracao')
        cor_coco = request.form.get('cor_coco')
        consistencia_coco = request.form.get('consistencia_coco')
        observacao = request.form.get('observacao')
        
        registro = Registro(
            usuario_id=current_user.id,
            tipo=tipo,
            lado=lado if lado else None,
            duracao=duracao if duracao else None,
            cor_coco=cor_coco if cor_coco else None,
            consistencia_coco=consistencia_coco if consistencia_coco else None,
            observacao=observacao if observacao else None
        )
        
        db.session.add(registro)
        db.session.commit()
        
        flash(f'{tipo} registrado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao registrar: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/excluir_registro/<int:registro_id>', methods=['POST'])
@login_required
def excluir_registro(registro_id):
    try:
        registro = Registro.query.get(registro_id)
        if registro and registro.usuario_id == current_user.id:
            db.session.delete(registro)
            db.session.commit()
            flash('Registro excluído com sucesso!', 'success')
        else:
            flash('Registro não encontrado.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/toggle_modo', methods=['POST'])
@login_required
def toggle_modo():
    try:
        current_user.modo_noturno = not current_user.modo_noturno
        db.session.commit()
        session['modo_noturno'] = current_user.modo_noturno
        flash('Modo alterado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao alterar modo: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/relatorio')
@login_required
def relatorio():
    try:
        # Últimos 7 dias
        hoje = datetime.now().date()
        semana = [hoje - timedelta(days=i) for i in range(7)]
        semana.reverse()
        
        dados_semana = []
        for dia in semana:
            registros = Registro.query.filter(
                db.func.date(Registro.data_hora) == dia,
                Registro.usuario_id == current_user.id
            ).all()
            
            dados_semana.append({
                'data': dia.strftime('%d/%m'),
                'mamadas': sum(1 for r in registros if r.tipo == 'Mamou'),
                'coco': sum(1 for r in registros if r.tipo == 'Coco'),
                'xixi': sum(1 for r in registros if r.tipo == 'Xixi'),
                'sono': sum(1 for r in registros if r.tipo == 'Dormiu')
            })
        
        # Dados detalhados do dia
        registros_hoje = Registro.query.filter(
            db.func.date(Registro.data_hora) == hoje,
            Registro.usuario_id == current_user.id
        ).all()
        
        detalhes = []
        for r in registros_hoje:
            detalhes.append({
                'tipo': r.tipo,
                'hora': r.data_hora.strftime('%H:%M'),
                'lado': r.lado if r.lado else '-',
                'duracao': r.duracao if r.duracao else '-',
                'cor_coco': r.cor_coco if r.cor_coco else '-',
                'consistencia_coco': r.consistencia_coco if r.consistencia_coco else '-'
            })
        
        # Avaliação geral
        idade = calcular_idade_exata(current_user)
        avaliacao = gerar_avaliacao(dados_semana, current_user)
        
        return render_template('relatorio.html', 
                             dados=dados_semana,
                             detalhes=detalhes,
                             idade=idade,
                             avaliacao=avaliacao,
                             nome_bebe=current_user.nome_bebe or 'Bebê')
    except Exception as e:
        flash(f'Erro ao carregar relatório: {str(e)}', 'danger')
        return render_template('relatorio.html', dados=[], detalhes=[])

@app.route('/api/iniciar_mamada', methods=['POST'])
@login_required
def api_iniciar_mamada():
    try:
        lado = request.json.get('lado')
        session['mamada_inicio'] = datetime.now().isoformat()
        session['mamada_lado'] = lado
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/parar_mamada', methods=['POST'])
@login_required
def api_parar_mamada():
    try:
        inicio = datetime.fromisoformat(session.get('mamada_inicio'))
        fim = datetime.now()
        duracao = fim - inicio
        minutos = int(duracao.total_seconds() // 60)
        segundos = int(duracao.total_seconds() % 60)
        tempo_str = f'{minutos:02d}:{segundos:02d}'
        lado = session.get('mamada_lado')
        
        registro = Registro(
            usuario_id=current_user.id,
            tipo='Mamou',
            lado=lado,
            duracao=tempo_str
        )
        
        db.session.add(registro)
        db.session.commit()
        
        session.pop('mamada_inicio', None)
        session.pop('mamada_lado', None)
        
        return jsonify({'success': True, 'duracao': tempo_str})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== FUNÇÕES AUXILIARES ==========

def calcular_idade_exata(usuario):
    if not usuario.data_nasc_bebe or not usuario.hora_nasc_bebe:
        return "Idade não disponível"
    
    nasc = datetime.combine(usuario.data_nasc_bebe, usuario.hora_nasc_bebe)
    agora = datetime.now()
    diff = agora - nasc
    
    anos = diff.days // 365
    meses = (diff.days % 365) // 30
    dias = diff.days % 30
    horas = diff.seconds // 3600
    minutos = (diff.seconds % 3600) // 60
    
    if anos > 0:
        return f"{anos} ano(s), {meses} mes(es) e {dias} dia(s)"
    elif meses > 0:
        return f"{meses} mes(es) e {dias} dia(s)"
    elif dias > 0:
        return f"{dias} dia(s) e {horas} hora(s)"
    else:
        return f"{horas} hora(s) e {minutos} minuto(s)"

def verificar_mamadas(total):
    if total >= 12:
<<<<<<< HEAD
        return {'status': 'excesso', 'mensagem': '⚠️ O bebê está mamando muito! Mais de 12 mamadas em 24h pode indicar que não está mamando o suficiente em cada vez.'}
    elif total < 8:
        return {'status': 'falta', 'mensagem': '⚠️ O bebê está mamando pouco! Menos de 8 mamadas em 24h pode indicar que não está se alimentando o suficiente.'}
    else:
        return {'status': 'ideal', 'mensagem': '✅ Ótimo! O bebê está mamando na quantidade ideal (8-12 mamadas por dia).'}
=======
        return {'status': 'excesso', 'mensagem': 'O bebê está mamando muito! Mais de 12 mamadas em 24h pode indicar que não está mamando o suficiente em cada vez.'}
    elif total < 8:
        return {'status': 'falta', 'mensagem': 'O bebê está mamando pouco! Menos de 8 mamadas em 24h pode indicar que não está se alimentando o suficiente.'}
    else:
        return {'status': 'ideal', 'mensagem': 'Ótimo! O bebê está mamando na quantidade ideal (8-12 mamadas por dia).'}
>>>>>>> 5014e6570a2a085a24368cbedb0320496d845b24

def buscar_dica_cientifica(stats):
    dicas = DicaCientifica.query.all()
    
    if not dicas:
        return None
    
    # Escolher dica baseada nas estatísticas
    if stats['mamadas'] < 8:
        return dicas[0]  # Dica sobre amamentação
    elif stats['sono'] == 0:
        return dicas[2]  # Dica sobre sono
    elif stats['coco'] > 3:
        return dicas[3]  # Dica sobre cólica
    else:
        return dicas[4]  # Dica sobre desenvolvimento

def gerar_avaliacao(dados, usuario):
    total_mamadas = sum(d['mamadas'] for d in dados)
    media_mamadas = total_mamadas / 7 if dados else 0
    
    if media_mamadas >= 10:
<<<<<<< HEAD
        return "✅ Excelente! O bebê está mamando muito bem. Continue assim!"
    elif media_mamadas >= 7:
        return "✅ Bom! O bebê está mamando regularmente. Tente aumentar um pouco a frequência."
    else:
        return "⚠️ Atenção! O bebê está mamando pouco. Consulte um pediatra para avaliação."
=======
        return "Excelente! O bebê está mamando muito bem. Continue assim!"
    elif media_mamadas >= 7:
        return "Bom! O bebê está mamando regularmente. Tente aumentar um pouco a frequência."
    else:
        return "Atenção! O bebê está mamando pouco. Consulte um pediatra para avaliação."
>>>>>>> 5014e6570a2a085a24368cbedb0320496d845b24

# ========== INICIALIZAR ==========

if __name__ == '__main__':
    app.run(debug=True)