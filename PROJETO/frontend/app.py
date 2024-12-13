from flask import Flask, render_template_string, request, redirect, url_for, jsonify, session
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Template completo com todas as seções incorporadas
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ titulo if titulo else 'Sistema de Gestão' }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
        <div class="container">
            <a class="navbar-brand" href="/">Sistema de Gestão</a>
            {% if session.get('token') %}
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/categorias">Categorias</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/produtos">Produtos</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/fornecedores">Fornecedores</a>
                    </li>
                </ul>
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/logout">Sair</a>
                    </li>
                </ul>
            </div>
            {% endif %}
        </div>
    </nav>
    <div class="container">
        {% if pagina == 'login' %}
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h2 class="card-title text-center mb-4">Login</h2>
                            <form method="POST" action="/">
                                <div class="mb-3">
                                    <label for="username" class="form-label">Usuário:</label>
                                    <input type="text" class="form-control" id="username" name="username" required>
                                </div>
                                <div class="mb-3">
                                    <label for="password" class="form-label">Senha:</label>
                                    <input type="password" class="form-control" id="password" name="password" required>
                                </div>
                                <button type="submit" class="btn btn-primary w-100">Entrar</button>
                            </form>
                            {% if error %}
                            <div class="alert alert-danger mt-3">{{ error }}</div>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
        {% elif pagina == 'crud' %}
            <h2 class="mb-4">{{ titulo }}</h2>

            <!-- Modal de Formulário -->
            <div class="modal fade" id="formModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="modalTitle">Novo {{ titulo }}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="entityForm">
                                <input type="hidden" id="id">
                                {% for campo in campos %}
                                <div class="mb-3">
                                    <label for="{{ campo.id }}" class="form-label">{{ campo.label }}:</label>
                                    {% if campo.type == 'select' %}
                                        <select class="form-control" id="{{ campo.id }}" name="{{ campo.id }}" {% if campo.required %}required{% endif %}>
                                            <option value="">Selecione</option>
                                            {% for option in campo.options %}
                                            <option value="{{ option.id }}">{{ option.nome }}</option>
                                            {% endfor %}
                                        </select>
                                    {% else %}
                                        <input type="{{ campo.type }}" class="form-control" id="{{ campo.id }}" name="{{ campo.id }}" {% if campo.required %}required{% endif %}>
                                    {% endif %}
                                </div>
                                {% endfor %}
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-primary" onclick="salvarEntidade()">Salvar</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tabela de Dados -->
            <div class="card">
                <div class="card-body">
                    <button class="btn btn-primary mb-3" onclick="novaEntidade()">Novo {{ titulo }}</button>
                    <div class="table-responsive">
                        <table class="table">
                            <thead>
                                <tr>
                                    {% for campo in campos %}
                                    <th>{{ campo.label }}</th>
                                    {% endfor %}
                                    <th>Ações</th>
                                </tr>
                            </thead>
                            <tbody id="tableBody"></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <script>
            const API_URL = '/api/{{ endpoint }}';
            let editando = null;

            async function carregarDados() {
                try {
                    const response = await fetch(API_URL);
                    const data = await response.json();
                    const tbody = document.getElementById('tableBody');
                    tbody.innerHTML = data.map(item => `
                        <tr>
                            {% for campo in campos %}
                            <td>${item.{{ campo.id }}}</td>
                            {% endfor %}
                            <td>
                                <button class="btn btn-sm btn-warning" onclick="editarEntidade(${item.id})">Editar</button>
                                <button class="btn btn-sm btn-danger" onclick="excluirEntidade(${item.id})">Excluir</button>
                            </td>
                        </tr>
                    `).join('');
                } catch (error) {
                    console.error('Erro ao carregar dados:', error);
                    alert('Erro ao carregar dados. Por favor, tente novamente.');
                }
            }

            function novaEntidade() {
                editando = null;
                document.getElementById('entityForm').reset();
                document.getElementById('modalTitle').textContent = 'Novo {{ titulo }}';
                new bootstrap.Modal(document.getElementById('formModal')).show();
            }

            async function editarEntidade(id) {
                try {
                    const response = await fetch(`${API_URL}/${id}`);
                    const data = await response.json();
                    editando = id;
                    {% for campo in campos %}
                    document.getElementById('{{ campo.id }}').value = data.{{ campo.id }};
                    {% endfor %}
                    document.getElementById('modalTitle').textContent = 'Editar {{ titulo }}';
                    new bootstrap.Modal(document.getElementById('formModal')).show();
                } catch (error) {
                    console.error('Erro ao editar:', error);
                    alert('Erro ao carregar dados para edição. Por favor, tente novamente.');
                }
            }

            async function salvarEntidade() {
                try {
                    const form = document.getElementById('entityForm');
                    const formData = new FormData(form);
                    const data = Object.fromEntries(formData.entries());
                    
                    const method = editando ? 'PUT' : 'POST';
                    const url = editando ? `${API_URL}/${editando}` : API_URL;
                    
                    const response = await fetch(url, {
                        method: method,
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });

                    if (!response.ok) {
                        throw new Error('Erro ao salvar');
                    }
                    
                    bootstrap.Modal.getInstance(document.getElementById('formModal')).hide();
                    carregarDados();
                } catch (error) {
                    console.error('Erro ao salvar:', error);
                    alert('Erro ao salvar dados. Por favor, tente novamente.');
                }
            }

            async function excluirEntidade(id) {
                if (confirm('Tem certeza que deseja excluir?')) {
                    try {
                        const response = await fetch(`${API_URL}/${id}`, { method: 'DELETE' });
                        if (!response.ok) {
                            throw new Error('Erro ao excluir');
                        }
                        carregarDados();
                    } catch (error) {
                        console.error('Erro ao excluir:', error);
                        alert('Erro ao excluir. Por favor, tente novamente.');
                    }
                }
            }

            carregarDados();
            </script>
        {% else %}
            <h2>Bem-vindo ao Sistema de Gestão</h2>
            <p>Escolha uma opção no menu acima para começar.</p>
        {% endif %}
    </div>
</body>
</html>
"""

# Configurações das páginas CRUD
CRUD_CONFIGS = {
    'categorias': {
        'titulo': 'Categorias',
        'endpoint': 'categorias',
        'campos': [
            {'id': 'nome', 'label': 'Nome', 'type': 'text', 'required': True},
            {'id': 'descricao', 'label': 'Descrição', 'type': 'text'}
        ]
    },
    'produtos': {
        'titulo': 'Produtos',
        'endpoint': 'produtos',
        'campos': [
            {'id': 'nome', 'label': 'Nome', 'type': 'text', 'required': True},
            {'id': 'descricao', 'label': 'Descrição', 'type': 'text'},
            {'id': 'preco', 'label': 'Preço', 'type': 'number', 'required': True},
            {'id': 'categoria_id', 'label': 'Categoria', 'type': 'select', 'required': True, 'options': []}
        ]
    },
    'fornecedores': {
        'titulo': 'Fornecedores',
        'endpoint': 'fornecedores',
        'campos': [
            {'id': 'nome', 'label': 'Nome', 'type': 'text', 'required': True},
            {'id': 'descricao', 'label': 'Descrição', 'type': 'text'},
            {'id': 'contato', 'label': 'Contato', 'type': 'text'}
        ]
    }
}

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'token' in session:
        return redirect('/home')
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            response = requests.post('http://127.0.0.1:5000/api/login', json={
                "username": username,
                "password": password
            })

            if response.status_code == 200:
                token = response.json()['token']
                session['token'] = token
                session['user'] = username
                return redirect('/home')
            else:
                return render_template_string(TEMPLATE, pagina='login', error="Credenciais inválidas")
        except requests.exceptions.ConnectionError:
            return render_template_string(TEMPLATE, pagina='login', error="Erro de conexão com o servidor")
    
    return render_template_string(TEMPLATE, pagina='login', error=None)

@app.route('/home')
def home():
    if 'token' not in session:
        return redirect('/')
    return render_template_string(TEMPLATE, pagina='home', session=session)

# Rotas CRUD
@app.route('/<endpoint>')
def crud_page(endpoint):
    if 'token' not in session:
        return redirect('/')
    if endpoint not in CRUD_CONFIGS:
        return redirect('/')

    if endpoint == 'produtos':
        # Carregar as categorias para o campo de seleção
        try:
            response = requests.get('http://127.0.0.1:5000/api/categorias', headers={'Authorization': session['token']})
            if response.status_code == 200:
                categorias = response.json()
                CRUD_CONFIGS['produtos']['campos'][3]['options'] = categorias
        except requests.exceptions.ConnectionError:
            CRUD_CONFIGS['produtos']['campos'][3]['options'] = []

    return render_template_string(
        TEMPLATE, 
        pagina='crud',
        session=session,
        **CRUD_CONFIGS[endpoint]
    )

# API proxy
@app.route('/api/<endpoint>', methods=['GET', 'POST'])
@app.route('/api/<endpoint>/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_proxy(endpoint, id=None):
    if 'token' not in session:
        return jsonify({"message": "Não autorizado"}), 403

    headers = {'Authorization': session['token']}
    url = f'http://127.0.0.1:5000/api/{endpoint}'
    if id is not None:
        url += f'/{id}'

    try:
        if request.method == 'GET':
            response = requests.get(url, headers=headers)
        elif request.method == 'POST':
            response = requests.post(url, json=request.json, headers=headers)
        elif request.method == 'PUT':
            response = requests.put(url, json=request.json, headers=headers)
        elif request.method == 'DELETE':
            response = requests.delete(url, headers=headers)

        return jsonify(response.json()), response.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"message": "Erro de conexão com o servidor"}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(port=3000)


#ARRUMAR A TABELA DE PRODUTO, POIS EM VEZ DE MOSTRAR O NOME DA CATEGORIA, ESTÁ MOSTRANDO O ID DA CATEGORIA
#FAZER A LIGACAO DE PRODUTO COM FORNECEDOR
#ORGAZIAR O CODIGO EM ARQUIVOS E PASTAS SEPARADAS ROUTES, TEMPLATE, ETC
#ADICIONAR FUNCAO PARA VISUALIZAR OS DADOS DA LINHA EM UMA POPUP