from flask import Flask, render_template_string, request, redirect, url_for, jsonify, session
import requests
import json
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

current_dir = os.path.dirname(os.path.abspath(__file__))

template_path = os.path.join(current_dir, 'template.html')
with open(template_path, 'r', encoding='utf8') as file:
    TEMPLATE = file.read()

config_path = os.path.join(current_dir, 'crud_config.json')
with open(config_path, 'r', encoding='utf8') as file:
    CRUD_CONFIGS = json.load(file)

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

