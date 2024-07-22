from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import json
import os

app = Flask(__name__)
app.secret_key = '15anosfbL'
login_manager = LoginManager()
login_manager.init_app(app)

# Caminhos para arquivos de dados
DATA_FOLDER = 'data'

def load_data(filename):
    try:
        with open(os.path.join(DATA_FOLDER, filename), 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_data(filename, data):
    with open(os.path.join(DATA_FOLDER, filename), 'w') as file:
        json.dump(data, file, indent=4)

# Modelo de Usuário
class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(username):
    return User(username)
@app.errorhandler(401)
def unauthorized_error(error):
    return render_template('401.html'), 401

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        usuarios = load_data('usuarios.json')

        # Verifica se o usuário e senha são válidos
        for usuario in usuarios:
            if usuario['username'] == username and usuario['password'] == password:
                user = User(username)
                login_user(user)
                return redirect(url_for('home'))

        # Se a autenticação falhar
        flash('Usuário ou senha inválidos. Por favor, tente novamente.', 'error')
        return redirect(url_for('index'))
    return render_template('login.html')
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
# Função para verificar se o usuário está logado e passar o nome de usuário para os templates
@app.context_processor
def inject_logged_in_user():
    return {'logged_in_user': current_user.id if current_user.is_authenticated else None}

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/clientes')
@login_required
def clientes():
    clientes = load_data('clientes.json')
    return render_template('clientes.html', clientes=clientes)

@app.route('/buscar_cliente')
@login_required
def buscar_cliente():
    term = request.args.get('term', '')
    clientes = load_data('clientes.json')
    resultados = [cliente for cliente in clientes if term.lower() in cliente['nome'].lower()]
    return jsonify({'clientes': resultados})

@app.route('/buscar_veiculo', methods=['GET'])
@login_required
def buscar_veiculo():
    term = request.args.get('term', '').upper().replace('-', '')
    veiculos = load_data('veiculos.json')
    resultados = [veiculo for veiculo in veiculos if term in veiculo['placa'].replace('-', '')]
    return jsonify({'veiculos': resultados})

@app.route('/buscar_manutencao', methods=['GET'])
@login_required
def buscar_manutencao():
    term = request.args.get('term', '').strip()
    manutencoes = load_data('manutencoes.json')

    if term:
        # Busca por placa ou data
        resultados = [manutencao for manutencao in manutencoes if term in manutencao['placa'] or term in manutencao['data']]
    else:
        resultados = manutencoes

    return jsonify({'manutencoes': resultados})

@app.route('/veiculos')
@login_required
def veiculos():
    veiculos = load_data('veiculos.json')
    return render_template('veiculos.html', veiculos=veiculos)

@app.route('/manutencoes', methods=['GET', 'POST'])
@login_required
def manutencoes():
    if request.method == 'POST':
        if 'add' in request.form:
            manutencao = {
                'data': request.form['data'],
                'placa': request.form['placa'],
                'informacoes': request.form['informacoes'],
                'mecanico': request.form['mecanico'],
                'valor': request.form['valor'],
                'usuario_cadastro': current_user.id
            }
            manutencoes = load_data('manutencoes.json')
            manutencoes.append(manutencao)
            save_data('manutencoes.json', manutencoes)
        elif 'edit' in request.form:
            index = int(request.form['edit'])
            manutencao = {
                'data': request.form['data'],
                'placa': request.form['placa'],
                'informacoes': request.form['informacoes'],
                'mecanico': request.form['mecanico'],
                'valor': request.form['valor'],
                'usuario_cadastro': current_user.id
            }
            manutencoes = load_data('manutencoes.json')
            manutencoes[index] = manutencao
            save_data('manutencoes.json', manutencoes)
        elif 'delete' in request.form:
            index = int(request.form['delete'])
            manutencoes = load_data('manutencoes.json')
            manutencoes.pop(index)
            save_data('manutencoes.json', manutencoes)
        return redirect(url_for('manutencoes'))

    manutencoes = load_data('manutencoes.json')
    return render_template('manutencoes.html', manutencoes=manutencoes)

@app.route('/adicionar_cliente', methods=['POST'])
@login_required
def adicionar_cliente():
    cliente = {
        'nome': request.form['nome'],
        'rg': request.form['rg'],
        'endereco': request.form['endereco'],
        'telefone': request.form['telefone'],
        'whatsapp': request.form['whatsapp'],
        'usuario_cadastro': current_user.id
    }

    # Carregar os dados dos clientes existentes
    clientes = load_data('clientes.json')

    # Verificar se o RG já existe
    rg_existente = any(c['rg'] == cliente['rg'] for c in clientes)

    if rg_existente:
        # Se o RG já existir, exibir uma mensagem de erro e redirecionar
        flash('RG já cadastrado. Por favor, verifique e tente novamente.')
        return redirect(url_for('clientes'))

    # Adicionar o novo cliente à lista e salvar
    clientes.append(cliente)
    save_data('clientes.json', clientes)
    flash('Cliente adicionado com sucesso!')
    return redirect(url_for('clientes'))

@app.route('/editar_cliente', methods=['POST'])
@login_required
def editar_cliente():
    rg = request.form.get('rg')
    nome = request.form.get('nome')
    endereco = request.form.get('endereco')
    telefone = request.form.get('telefone')
    whatsapp = request.form.get('whatsapp')
    
    clientes = load_data('clientes.json')
    
    for cliente in clientes:
        if cliente['rg'] == rg:
            cliente.update({
                'nome': nome,
                'endereco': endereco,
                'telefone': telefone,
                'whatsapp': whatsapp
            })
            break
    
    save_data('clientes.json', clientes)
    
    return redirect(url_for('clientes'))

@app.route('/excluir_cliente', methods=['POST'])
@login_required
def excluir_cliente():
    rg = request.form['rg']
    clientes = load_data('clientes.json')
    clientes = [c for c in clientes if c['rg'] != rg]
    save_data('clientes.json', clientes)
    return redirect(url_for('clientes'))

@app.route('/adicionar_veiculo', methods=['POST'])
@login_required
def adicionar_veiculo():
    veiculo = {
        'placa': request.form['placa'],
        'modelo': request.form['modelo'],
        'ano': request.form['ano'],
        'usuario_cadastro': current_user.id
    }

    # Carregar os dados dos veículos existentes
    veiculos = load_data('veiculos.json')

    # Verificar se a placa já existe
    placa_existente = any(v['placa'] == veiculo['placa'] for v in veiculos)

    if placa_existente:
        # Se a placa já existir, exibir uma mensagem de erro
        flash('Placa já cadastrada. Por favor, verifique e tente novamente.', 'error')
        return redirect(url_for('veiculos'))

    # Adicionar o novo veículo à lista e salvar
    veiculos.append(veiculo)
    save_data('veiculos.json', veiculos)
    
    # Adiciona uma mensagem de sucesso
    flash('Veículo adicionado com sucesso!', 'success')

    return redirect(url_for('veiculos'))

@app.route('/editar_veiculo', methods=['POST'])
@login_required
def editar_veiculo():
    placa = request.form['placa']
    modelo = request.form['modelo']
    ano = request.form['ano']
    
    veiculos = load_data('veiculos.json')
    for veiculo in veiculos:
        if veiculo['placa'] == placa:
            veiculo.update({
                'modelo': modelo,
                'ano': ano
            })
            break
    
    save_data('veiculos.json', veiculos)
    flash('Veículo editado com sucesso!', 'success')
    return redirect(url_for('veiculos'))

@app.route('/excluir_veiculo', methods=['POST'])
@login_required
def excluir_veiculo():
    placa = request.form['placa']
    veiculos = load_data('veiculos.json')
    veiculos = [v for v in veiculos if v['placa'] != placa]
    save_data('veiculos.json', veiculos)
    flash('Veículo excluído com sucesso!', 'success')
    return redirect(url_for('veiculos'))

@app.route('/adicionar_manutencao', methods=['POST'])
@login_required
def adicionar_manutencao():
    manutencao = {
        'data': request.form['data'],
        'placa': request.form['placa'],
        'informacoes': request.form['informacoes'],
        'mecanico': request.form['mecanico'],
        'valor': request.form['valor'],
        'usuario_cadastro': current_user.id
    }

    # Carregar os dados dos veículos existentes
    veiculos = load_data('veiculos.json')

    # Verificar se a placa do veículo está cadastrada
    placa_cadastrada = any(v['placa'] == manutencao['placa'] for v in veiculos)

    if not placa_cadastrada:
        # Se a placa não estiver cadastrada, exibir uma mensagem de erro
        flash('Placa do veículo não cadastrada. Por favor, cadastre o veículo antes de adicionar a manutenção.', 'error')
        return redirect(url_for('manutencoes'))

    # Carregar os dados das manutenções existentes
    manutencoes = load_data('manutencoes.json')

    # Adicionar a nova manutenção à lista e salvar
    manutencoes.append(manutencao)
    save_data('manutencoes.json', manutencoes)
    
    # Adiciona uma mensagem de sucesso
    flash('Manutenção adicionada com sucesso!', 'success')

    return redirect(url_for('manutencoes'))

@app.route('/editar_manutencao', methods=['POST'])
@login_required
def editar_manutencao():
    index = int(request.form['index'])
    manutencao = {
        'data': request.form['data'],
        'placa': request.form['placa'],
        'informacoes': request.form['informacoes'],
        'mecanico': request.form['mecanico'],
        'valor': request.form['valor'],
        'usuario_cadastro': current_user.id
    }

    manutencoes = load_data('manutencoes.json')
    manutencoes[index] = manutencao
    save_data('manutencoes.json', manutencoes)
    flash('Manutenção editada com sucesso!', 'success')
    return redirect(url_for('manutencoes'))

@app.route('/excluir_manutencao', methods=['POST'])
@login_required
def excluir_manutencao():
    index = int(request.form['index'])
    manutencoes = load_data('manutencoes.json')
    manutencoes.pop(index)
    save_data('manutencoes.json', manutencoes)
    flash('Manutenção excluída com sucesso!', 'success')
    return redirect(url_for('manutencoes'))

if __name__ == '__main__':
    app.run(debug=True)
   
