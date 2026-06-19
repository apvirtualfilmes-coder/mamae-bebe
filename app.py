from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from models import db, Usuario, Registro, DicaCientifica, BichinhoVirtual, PesoRegistro, Vacina, Banho
import os
from dotenv import load_dotenv
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

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

# Criar tabelas
with app.app_context():
    try:
        db.create_all()
        print("✅ Tabelas criadas com sucesso!")
        
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
            
            if not nome or not email or not senha:
                flash('Nome, email e senha são obrigatórios.', 'danger')
                return redirect(url_for('cadastrar'))
            
            if Usuario.query.filter_by(email=email).first():
                flash('Este email já está cadastrado.', 'danger')
                return redirect(url_for('cadastrar'))
            
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
            
            criar_bichinho_inicial(usuario.id)
            
            # Registrar peso inicial
            if peso:
                peso_reg = PesoRegistro(
                    usuario_id=usuario.id,
                    peso=float(peso),
                    data=datetime.now().date()
                )
                db.session.add(peso_reg)
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
        session['modo_noturno'] = current_user.modo_noturno
        session['cor_tema'] = current_user.cor_tema
        
        hoje = datetime.now().date()
        registros_hoje = Registro.query.filter(
            db.func.date(Registro.data_hora) == hoje,
            Registro.usuario_id == current_user.id
        ).order_by(Registro.data_hora.desc()).all()
        
        idade = calcular_idade_exata(current_user)
        
        stats = {
            'mamadas': sum(1 for r in registros_hoje if r.tipo == 'Mamou'),
            'mamadas_direito': sum(1 for r in registros_hoje if r.tipo == 'Mamou' and r.lado == 'direito'),
            'mamadas_esquerdo': sum(1 for r in registros_hoje if r.tipo == 'Mamou' and r.lado == 'esquerdo'),
            'coco': sum(1 for r in registros_hoje if r.tipo == 'Coco'),
            'xixi': sum(1 for r in registros_hoje if r.tipo == 'Xixi'),
            'regurgito': sum(1 for r in registros_hoje if r.tipo == 'Regurgito'),
            'sono': sum(1 for r in registros_hoje if r.tipo == 'Dormiu'),
            'banhos': sum(1 for r in registros_hoje if r.tipo == 'Banho'),
            'febre': sum(1 for r in registros_hoje if r.tipo == 'Febre'),
            'nariz': sum(1 for r in registros_hoje if r.tipo == 'Nariz Entupido')
        }
        
        alerta_mamada = verificar_mamadas(stats['mamadas'])
        verificar_lembrete_mamada()
        
        ultima_mamada = Registro.query.filter(
            Registro.tipo == 'Mamou',
            Registro.usuario_id == current_user.id
        ).order_by(Registro.data_hora.desc()).first()
        
        dica = buscar_dica_cientifica(stats)
        
        bichinho = BichinhoVirtual.query.filter_by(usuario_id=current_user.id).first()
        if bichinho:
            atualizar_niveis_bichinho(bichinho)
        
        # Lista de pesos para o gráfico
        pesos = PesoRegistro.query.filter_by(usuario_id=current_user.id).order_by(PesoRegistro.data).all()
        
        # Vacinas pendentes
        vacinas_pendentes = Vacina.query.filter(
            Vacina.usuario_id == current_user.id,
            Vacina.aplicada == False
        ).order_by(Vacina.proxima_dose).all()
        
        return render_template('dashboard.html', 
                             registros=registros_hoje[:10],
                             stats=stats,
                             ultima_mamada=ultima_mamada,
                             datetime=datetime,
                             idade=idade,
                             alerta_mamada=alerta_mamada,
                             dica=dica,
                             bichinho=bichinho,
                             pesos=pesos,
                             vacinas_pendentes=vacinas_pendentes[:3])
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
        temperatura = request.form.get('temperatura')
        observacao = request.form.get('observacao')
        
        registro = Registro(
            usuario_id=current_user.id,
            tipo=tipo,
            lado=lado if lado else None,
            duracao=duracao if duracao else None,
            cor_coco=cor_coco if cor_coco else None,
            consistencia_coco=consistencia_coco if consistencia_coco else None,
            temperatura=float(temperatura) if temperatura else None,
            observacao=observacao if observacao else None
        )
        
        db.session.add(registro)
        db.session.commit()
        
        # Atualizar bichinho
        bichinho = BichinhoVirtual.query.filter_by(usuario_id=current_user.id).first()
        if bichinho:
            atualizar_niveis_bichinho(bichinho)
        
        flash(f'{tipo} registrado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao registrar: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/registrar_peso', methods=['POST'])
@login_required
def registrar_peso():
    try:
        peso = request.form.get('peso')
        altura = request.form.get('altura')
        data = request.form.get('data')
        
        if not peso:
            flash('Peso é obrigatório.', 'danger')
            return redirect(url_for('dashboard'))
        
        peso_reg = PesoRegistro(
            usuario_id=current_user.id,
            peso=float(peso),
            altura=float(altura) if altura else None,
            data=datetime.strptime(data, '%Y-%m-%d').date() if data else datetime.now().date()
        )
        
        db.session.add(peso_reg)
        current_user.peso_bebe = float(peso)
        if altura:
            current_user.altura_bebe = float(altura)
        
        db.session.commit()
        flash('✅ Peso registrado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao registrar peso: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/registrar_vacina', methods=['POST'])
@login_required
def registrar_vacina():
    try:
        nome = request.form.get('nome')
        data_aplicacao = request.form.get('data_aplicacao')
        proxima_dose = request.form.get('proxima_dose')
        aplicada = request.form.get('aplicada') == 'on'
        
        vacina = Vacina(
            usuario_id=current_user.id,
            nome=nome,
            data_aplicacao=datetime.strptime(data_aplicacao, '%Y-%m-%d').date() if data_aplicacao else None,
            proxima_dose=datetime.strptime(proxima_dose, '%Y-%m-%d').date() if proxima_dose else None,
            aplicada=aplicada
        )
        
        db.session.add(vacina)
        db.session.commit()
        flash('💉 Vacina registrada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao registrar vacina: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/registrar_banho', methods=['POST'])
@login_required
def registrar_banho():
    try:
        data_hora = request.form.get('data_hora')
        duracao = request.form.get('duracao')
        observacao = request.form.get('observacao')
        
        banho = Banho(
            usuario_id=current_user.id,
            data_hora=datetime.strptime(data_hora, '%Y-%m-%dT%H:%M') if data_hora else datetime.now(),
            duracao=duracao,
            observacao=observacao
        )
        
        db.session.add(banho)
        
        # Registrar também como evento
        registro = Registro(
            usuario_id=current_user.id,
            tipo='Banho',
            observacao=observacao
        )
        db.session.add(registro)
        
        db.session.commit()
        flash('🛁 Banho registrado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao registrar banho: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/registrar_febre', methods=['POST'])
@login_required
def registrar_febre():
    try:
        temperatura = request.form.get('temperatura')
        observacao = request.form.get('observacao')
        
        registro = Registro(
            usuario_id=current_user.id,
            tipo='Febre',
            temperatura=float(temperatura) if temperatura else None,
            observacao=observacao
        )
        
        db.session.add(registro)
        db.session.commit()
        
        if temperatura and float(temperatura) >= 38.5:
            flash('⚠️ ATENÇÃO: Febre alta! Consulte o pediatra.', 'danger')
        else:
            flash('🌡️ Febre registrada.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao registrar febre: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/registrar_nariz', methods=['POST'])
@login_required
def registrar_nariz():
    try:
        observacao = request.form.get('observacao')
        
        registro = Registro(
            usuario_id=current_user.id,
            tipo='Nariz Entupido',
            observacao=observacao
        )
        
        db.session.add(registro)
        db.session.commit()
        flash('👃 Nariz entupido registrado.', 'success')
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
            
            bichinho = BichinhoVirtual.query.filter_by(usuario_id=current_user.id).first()
            if bichinho:
                atualizar_niveis_bichinho(bichinho)
            
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
                'consistencia_coco': r.consistencia_coco if r.consistencia_coco else '-',
                'temperatura': r.temperatura if r.temperatura else '-'
            })
        
        idade = calcular_idade_exata(current_user)
        avaliacao = gerar_avaliacao(dados_semana, current_user)
        
        pesos = PesoRegistro.query.filter_by(usuario_id=current_user.id).order_by(PesoRegistro.data).all()
        vacinas = Vacina.query.filter_by(usuario_id=current_user.id).order_by(Vacina.data_aplicacao).all()
        
        return render_template('relatorio.html', 
                             dados=dados_semana,
                             detalhes=detalhes,
                             idade=idade,
                             avaliacao=avaliacao,
                             nome_bebe=current_user.nome_bebe or 'Bebê',
                             pesos=pesos,
                             vacinas=vacinas)
    except Exception as e:
        flash(f'Erro ao carregar relatório: {str(e)}', 'danger')
        return render_template('relatorio.html', dados=[], detalhes=[])

@app.route('/bichinho')
@login_required
def bichinho():
    bichinho = BichinhoVirtual.query.filter_by(usuario_id=current_user.id).first()
    if not bichinho:
        criar_bichinho_inicial(current_user.id)
        bichinho = BichinhoVirtual.query.filter_by(usuario_id=current_user.id).first()
    
    return render_template('bichinho.html', bichinho=bichinho)

@app.route('/api/humor_bichinho')
@login_required
def api_humor_bichinho():
    try:
        bichinho = BichinhoVirtual.query.filter_by(usuario_id=current_user.id).first()
        if not bichinho:
            criar_bichinho_inicial(current_user.id)
            bichinho = BichinhoVirtual.query.filter_by(usuario_id=current_user.id).first()
        
        atualizar_niveis_bichinho(bichinho)
        
        return jsonify({
            'humor': bichinho.humor,
            'felicidade': bichinho.nivel_felicidade,
            'fome': bichinho.nivel_fome,
            'sono': bichinho.nivel_sono,
            'energia': bichinho.nivel_energia,
            'saude': bichinho.nivel_saude
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/interagir_bichinho', methods=['POST'])
@login_required
def api_interagir_bichinho():
    try:
        acao = request.json.get('acao')
        bichinho = BichinhoVirtual.query.filter_by(usuario_id=current_user.id).first()
        
        if not bichinho:
            return jsonify({'error': 'Bichinho não encontrado'}), 404
        
        if acao == 'carinho':
            bichinho.nivel_felicidade = min(100, bichinho.nivel_felicidade + 10)
        elif acao == 'alimentar':
            bichinho.nivel_fome = max(0, bichinho.nivel_fome - 20)
            bichinho.nivel_felicidade = min(100, bichinho.nivel_felicidade + 5)
        elif acao == 'dormir':
            bichinho.nivel_sono = max(0, bichinho.nivel_sono - 20)
            bichinho.nivel_energia = min(100, bichinho.nivel_energia + 10)
        elif acao == 'brincar':
            bichinho.nivel_felicidade = min(100, bichinho.nivel_felicidade + 15)
            bichinho.nivel_energia = max(0, bichinho.nivel_energia - 10)
        
        db.session.commit()
        atualizar_niveis_bichinho(bichinho)
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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
        
        bichinho = BichinhoVirtual.query.filter_by(usuario_id=current_user.id).first()
        if bichinho:
            atualizar_niveis_bichinho(bichinho)
        
        session.pop('mamada_inicio', None)
        session.pop('mamada_lado', None)
        
        return jsonify({'success': True, 'duracao': tempo_str})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/status_mamada')
@login_required
def api_status_mamada():
    try:
        if 'mamada_inicio' in session:
            inicio = datetime.fromisoformat(session['mamada_inicio'])
            diff = datetime.now() - inicio
            minutos = int(diff.total_seconds() // 60)
            segundos = int(diff.total_seconds() % 60)
            return jsonify({
                'ativa': True,
                'tempo': f'{minutos:02d}:{segundos:02d}',
                'lado': session.get('mamada_lado')
            })
        return jsonify({'ativa': False})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/iniciar_sono', methods=['POST'])
@login_required
def api_iniciar_sono():
    try:
        session['sono_inicio'] = datetime.now().isoformat()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/parar_sono', methods=['POST'])
@login_required
def api_parar_sono():
    try:
        inicio = datetime.fromisoformat(session.get('sono_inicio'))
        fim = datetime.now()
        duracao = fim - inicio
        horas = int(duracao.total_seconds() // 3600)
        minutos = int((duracao.total_seconds() % 3600) // 60)
        tempo_str = f"{horas:02d}:{minutos:02d}"
        
        registro = Registro(
            usuario_id=current_user.id,
            tipo='Dormiu',
            duracao=tempo_str,
            observacao=f"Dormiu das {inicio.strftime('%H:%M')} às {fim.strftime('%H:%M')}"
        )
        
        db.session.add(registro)
        db.session.commit()
        
        bichinho = BichinhoVirtual.query.filter_by(usuario_id=current_user.id).first()
        if bichinho:
            atualizar_niveis_bichinho(bichinho)
        
        session.pop('sono_inicio', None)
        
        return jsonify({'success': True, 'duracao': tempo_str})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== FUNÇÕES AUXILIARES ==========

def criar_bichinho_inicial(usuario_id):
    try:
        bichinho = BichinhoVirtual(
            usuario_id=usuario_id,
            humor='neutro',
            nivel_felicidade=50,
            nivel_fome=50,
            nivel_sono=50,
            nivel_energia=50,
            nivel_saude=50
        )
        db.session.add(bichinho)
        db.session.commit()
        print(f"✅ Bebêzinho criado para usuário {usuario_id}")
    except Exception as e:
        print(f"❌ Erro ao criar bebêzinho: {e}")

def atualizar_niveis_bichinho(bichinho):
    hoje = datetime.now().date()
    
    registros_hoje = Registro.query.filter(
        db.func.date(Registro.data_hora) == hoje,
        Registro.usuario_id == bichinho.usuario_id
    ).all()
    
    mamadas = sum(1 for r in registros_hoje if r.tipo == 'Mamou')
    sono = sum(1 for r in registros_hoje if r.tipo == 'Dormiu')
    coco = sum(1 for r in registros_hoje if r.tipo == 'Coco')
    xixi = sum(1 for r in registros_hoje if r.tipo == 'Xixi')
    regurgito = sum(1 for r in registros_hoje if r.tipo == 'Regurgito')
    febre = sum(1 for r in registros_hoje if r.tipo == 'Febre')
    nariz = sum(1 for r in registros_hoje if r.tipo == 'Nariz Entupido')
    
    # FOME
    if mamadas >= 8:
        bichinho.nivel_fome = max(0, bichinho.nivel_fome - 10)
    elif mamadas >= 5:
        bichinho.nivel_fome = max(0, bichinho.nivel_fome - 3)
    elif mamadas >= 2:
        bichinho.nivel_fome = min(100, bichinho.nivel_fome + 5)
    else:
        bichinho.nivel_fome = min(100, bichinho.nivel_fome + 15)
    
    # SONO
    if sono >= 3:
        bichinho.nivel_sono = max(0, bichinho.nivel_sono - 10)
        bichinho.nivel_energia = min(100, bichinho.nivel_energia + 10)
    elif sono >= 1:
        bichinho.nivel_sono = max(0, bichinho.nivel_sono - 5)
        bichinho.nivel_energia = min(100, bichinho.nivel_energia + 5)
    else:
        bichinho.nivel_sono = min(100, bichinho.nivel_sono + 10)
        bichinho.nivel_energia = max(0, bichinho.nivel_energia - 10)
    
    # SAÚDE
    saude = 100
    if febre > 0:
        saude -= 20 * febre
    if nariz > 0:
        saude -= 10 * nariz
    if regurgito >= 3:
        saude -= 10
    bichinho.nivel_saude = max(0, min(100, saude))
    
    # FELICIDADE
    felicidade = 50
    if mamadas >= 8:
        felicidade += 20
    elif mamadas >= 5:
        felicidade += 10
    else:
        felicidade -= 15
    
    if sono >= 3:
        felicidade += 15
    elif sono == 0:
        felicidade -= 15
    
    if xixi >= 6:
        felicidade += 10
    else:
        felicidade -= 10
    
    if coco >= 1:
        felicidade += 5
    
    if bichinho.nivel_saude < 50:
        felicidade -= 20
    
    bichinho.nivel_felicidade = max(0, min(100, felicidade))
    
    # DETERMINAR HUMOR
    if bichinho.nivel_saude <= 30:
        bichinho.humor = 'doente'
    elif bichinho.nivel_fome >= 80:
        bichinho.humor = 'com_fome'
    elif bichinho.nivel_sono >= 80:
        bichinho.humor = 'com_sono'
    elif bichinho.nivel_saude <= 50:
        bichinho.humor = 'cansado'
    elif bichinho.nivel_felicidade >= 80 and bichinho.nivel_energia >= 70:
        bichinho.humor = 'brincalhao'
    elif bichinho.nivel_felicidade >= 65:
        bichinho.humor = 'feliz'
    elif bichinho.nivel_felicidade <= 30:
        bichinho.humor = 'brabo'
    elif bichinho.nivel_felicidade >= 50 and bichinho.nivel_energia >= 50:
        bichinho.humor = 'tranquilo'
    else:
        bichinho.humor = 'neutro'
    
    bichinho.ultima_atualizacao = datetime.utcnow()
    db.session.commit()

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
        return {'status': 'excesso', 'mensagem': '⚠️ O bebê está mamando muito! Mais de 12 mamadas em 24h pode indicar que não está mamando o suficiente em cada vez.'}
    elif total < 8:
        return {'status': 'falta', 'mensagem': '⚠️ O bebê está mamando pouco! Menos de 8 mamadas em 24h pode indicar que não está se alimentando o suficiente.'}
    else:
        return {'status': 'ideal', 'mensagem': '✅ Ótimo! O bebê está mamando na quantidade ideal (8-12 mamadas por dia).'}

def verificar_lembrete_mamada():
    if current_user.is_authenticated:
        ultima_mamada = Registro.query.filter(
            Registro.tipo == 'Mamou',
            Registro.usuario_id == current_user.id
        ).order_by(Registro.data_hora.desc()).first()
        
        if ultima_mamada:
            diff = datetime.now() - ultima_mamada.data_hora
            if diff.total_seconds() > 10800:
                flash('⏰ Já faz 3 horas desde a última mamada! Hora de amamentar.', 'warning')

def buscar_dica_cientifica(stats):
    dicas = DicaCientifica.query.all()
    if not dicas:
        return None
    
    if stats['mamadas'] < 8:
        return dicas[0]
    elif stats['sono'] == 0:
        return dicas[2]
    elif stats['coco'] > 3:
        return dicas[3]
    else:
        return dicas[4]

def gerar_avaliacao(dados, usuario):
    total_mamadas = sum(d['mamadas'] for d in dados)
    media_mamadas = total_mamadas / 7 if dados else 0
    
    if media_mamadas >= 10:
        return "✅ Excelente! O bebê está mamando muito bem. Continue assim!"
    elif media_mamadas >= 7:
        return "✅ Bom! O bebê está mamando regularmente. Tente aumentar um pouco a frequência."
    else:
        return "⚠️ Atenção! O bebê está mamando pouco. Consulte um pediatra para avaliação."

if __name__ == '__main__':
    app.run(debug=True)