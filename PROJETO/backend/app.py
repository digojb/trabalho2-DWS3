#BACK END APP.PY

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import jwt
import datetime
from functools import wraps

# Configurações do app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'teste teste teste teste'
db = SQLAlchemy(app)
CORS(app)

# Mock de usuário para login
USER = {"username": "admin", "password": "admin"}

# Modelagem das tabelas
# Relacionamento 1:N: Categoria -> Produto
class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    removido = db.Column(db.Boolean, default=False)
    produtos = db.relationship('Produto', backref='categoria', lazy=True)

# Relacionamento M:N: Produto <-> Fornecedor
produto_fornecedor = db.Table('produto_fornecedor',
    db.Column('produto_id', db.Integer, db.ForeignKey('produto.id'), primary_key=True),
    db.Column('fornecedor_id', db.Integer, db.ForeignKey('fornecedor.id'), primary_key=True)
)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    preco = db.Column(db.Float, nullable=False)
    data_cadastro = db.Column(db.Date, default=datetime.datetime.utcnow)
    removido = db.Column(db.Boolean, default=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    fornecedores = db.relationship('Fornecedor', secondary=produto_fornecedor, lazy='subquery',
                                    backref=db.backref('produtos', lazy=True))

class Fornecedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    contato = db.Column(db.String(100), nullable=True)
    removido = db.Column(db.Boolean, default=False)

# Inicializa o banco de dados
with app.app_context():
    db.create_all()

# Middleware de autenticação JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Token is missing"}), 403
        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated

# Rota de login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if data['username'] == USER['username'] and data['password'] == USER['password']:
        token = jwt.encode(
            {'user': data['username'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
            app.config['SECRET_KEY'],
            algorithm="HS256"
        )
        return jsonify({"token": token})
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# CRUD Categoria
@app.route('/api/categorias', methods=['GET'])
@token_required
def get_all_categorias():
    categorias = Categoria.query.filter_by(removido=False).all()
    return jsonify([{"id": c.id, "nome": c.nome, "descricao": c.descricao} for c in categorias])

@app.route('/api/categorias/<int:id>', methods=['GET'])
@token_required
def get_categoria_by_id(id):
    categoria = Categoria.query.filter_by(id=id, removido=False).first()
    if not categoria:
        return jsonify({"message": "Categoria não encontrada"}), 404
    return jsonify({"id": categoria.id, "nome": categoria.nome, "descricao": categoria.descricao})

@app.route('/api/categorias', methods=['POST'])
@token_required
def insert_categoria():
    data = request.json
    nova_categoria = Categoria(nome=data['nome'], descricao=data.get('descricao'))
    db.session.add(nova_categoria)
    db.session.commit()
    return jsonify({"message": "Categoria adicionada com sucesso"}), 201

@app.route('/api/categorias/<int:id>', methods=['PUT'])
@token_required
def update_categoria(id):
    data = request.json
    categoria = Categoria.query.filter_by(id=id, removido=False).first()
    if not categoria:
        return jsonify({"message": "Categoria não encontrada"}), 404
    categoria.nome = data['nome']
    categoria.descricao = data.get('descricao')
    db.session.commit()
    return jsonify({"message": "Categoria atualizada com sucesso"})

@app.route('/api/categorias/<int:id>', methods=['DELETE'])
@token_required
def delete_categoria(id):
    categoria = Categoria.query.filter_by(id=id, removido=False).first()
    if not categoria:
        return jsonify({"message": "Categoria não encontrada"}), 404
    categoria.removido = True
    db.session.commit()
    return jsonify({"message": "Categoria removida com sucesso"})

# CRUD Produto
@app.route('/api/produtos', methods=['GET'])
@token_required
def get_all_produtos():
    produtos = Produto.query.filter_by(removido=False).all()
    return jsonify([{
        "id": p.id,
        "nome": p.nome,
        "descricao": p.descricao,
        "preco": p.preco,
        "data_cadastro": p.data_cadastro,
        "categoria_id": p.categoria_id
    } for p in produtos])

@app.route('/api/produtos/<int:id>', methods=['GET'])
@token_required
def get_produto_by_id(id):
    produto = Produto.query.filter_by(id=id, removido=False).first()
    if not produto:
        return jsonify({"message": "Produto não encontrado"}), 404
    return jsonify({
        "id": produto.id,
        "nome": produto.nome,
        "descricao": produto.descricao,
        "preco": produto.preco,
        "data_cadastro": produto.data_cadastro,
        "categoria_id": produto.categoria_id
    })

@app.route('/api/produtos', methods=['POST'])
@token_required
def insert_produto():
    data = request.json
    novo_produto = Produto(
        nome=data['nome'],
        descricao=data.get('descricao'),
        preco=data['preco'],
        categoria_id=data['categoria_id']
    )
    db.session.add(novo_produto)
    db.session.commit()
    return jsonify({"message": "Produto adicionado com sucesso"}), 201

@app.route('/api/produtos/<int:id>', methods=['PUT'])
@token_required
def update_produto(id):
    data = request.json
    produto = Produto.query.filter_by(id=id, removido=False).first()
    if not produto:
        return jsonify({"message": "Produto não encontrado"}), 404
    produto.nome = data['nome']
    produto.descricao = data.get('descricao')
    produto.preco = data['preco']
    produto.categoria_id = data['categoria_id']
    db.session.commit()
    return jsonify({"message": "Produto atualizado com sucesso"})

@app.route('/api/produtos/<int:id>', methods=['DELETE'])
@token_required
def delete_produto(id):
    produto = Produto.query.filter_by(id=id, removido=False).first()
    if not produto:
        return jsonify({"message": "Produto não encontrado"}), 404
    produto.removido = True
    db.session.commit()
    return jsonify({"message": "Produto removido com sucesso"})

# CRUD Fornecedor
@app.route('/api/fornecedores', methods=['GET'])
@token_required
def get_all_fornecedores():
    fornecedores = Fornecedor.query.filter_by(removido=False).all()
    return jsonify([{
        "id": f.id,
        "nome": f.nome,
        "descricao": f.descricao,
        "contato": f.contato
    } for f in fornecedores])

@app.route('/api/fornecedores/<int:id>', methods=['GET'])

@token_required
def get_fornecedor_by_id(id):
    fornecedor = Fornecedor.query.filter_by(id=id, removido=False).first()
    if not fornecedor:
        return jsonify({"message": "Fornecedor não encontrado"}), 404
    return jsonify({
        "id": fornecedor.id,
        "nome": fornecedor.nome,
        "descricao": fornecedor.descricao,
        "contato": fornecedor.contato
    })

@app.route('/api/fornecedores', methods=['POST'])
@token_required
def insert_fornecedor():
    data = request.json
    novo_fornecedor = Fornecedor(
        nome=data['nome'],
        descricao=data.get('descricao'),
        contato=data.get('contato')
    )
    db.session.add(novo_fornecedor)
    db.session.commit()
    return jsonify({"message": "Fornecedor adicionado com sucesso"}), 201

@app.route('/api/fornecedores/<int:id>', methods=['PUT'])
@token_required
def update_fornecedor(id):
    data = request.json
    fornecedor = Fornecedor.query.filter_by(id=id, removido=False).first()
    if not fornecedor:
        return jsonify({"message": "Fornecedor não encontrado"}), 404
    fornecedor.nome = data['nome']
    fornecedor.descricao = data.get('descricao')
    fornecedor.contato = data.get('contato')
    db.session.commit()
    return jsonify({"message": "Fornecedor atualizado com sucesso"})

@app.route('/api/fornecedores/<int:id>', methods=['DELETE'])
@token_required
def delete_fornecedor(id):
    fornecedor = Fornecedor.query.filter_by(id=id, removido=False).first()
    if not fornecedor:
        return jsonify({"message": "Fornecedor não encontrado"}), 404
    fornecedor.removido = True
    db.session.commit()
    return jsonify({"message": "Fornecedor removido com sucesso"})

if __name__ == '__main__':
    app.run(port=5000)