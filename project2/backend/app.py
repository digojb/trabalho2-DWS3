from flask import jsonify, request
import jwt
import datetime
from functools import wraps
import hashlib
from models import app, db, Categoria, Produto, Fornecedor, Users, produto_fornecedor

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

def check_password_hash(input_string):
    
    # Certifica-se de que a entrada seja codificada como bytes
    input_bytes = input_string.encode('utf-8')
    # Gera o hash MD5
    md5_hash = hashlib.md5(input_bytes).hexdigest()
    
    return md5_hash

# Rota de login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json  # Obtém os dados enviados pelo cliente
    
    # Procura o usuário no banco de dados
    user = Users.query.filter_by(username=data['username']).first()
    
    # Verifica se o usuário existe e se a senha está correta
    if user and check_password_hash(data['password']) == user.password:
        
        # Gera o token JWT
        token = jwt.encode({'username': user.username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
                           app.config['SECRET_KEY'])
        
        return jsonify({"token": token})
    
    # Retorna erro de credenciais inválidas
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
    resultado = []
    
    for p in produtos:
        fornecedores = [fornecedor.id for fornecedor in p.fornecedores]  # Coleta os IDs dos fornecedores
        
        produto_info = {
            "id": p.id,
            "nome": p.nome,
            "descricao": p.descricao,
            "preco": p.preco,
            "data_cadastro": p.data_cadastro,
            "categoria_id": p.categoria_id,
            "fornecedores": fornecedores  # Inclui os fornecedores associados
        }
        
        resultado.append(produto_info)
    
    return jsonify(resultado)

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
    db.session.commit()  # Salva o produto primeiro para obter o id do novo produto

    # Verificando se existem fornecedores para associar ao produto
    if 'fornecedores' in data:
        for fornecedor_id in data['fornecedores']:
            # Insere a relação na tabela intermediária
            relacao_produto_fornecedor = produto_fornecedor.insert().values(
                produto_id=novo_produto.id,
                fornecedor_id=fornecedor_id
            )
            db.session.execute(relacao_produto_fornecedor)  # Executa a inserção na tabela intermediária
        db.session.commit()  # Commit para garantir a persistência

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

@app.route('/api/fornecedor_por_produto/<int:produto_id>', methods=['GET'])
@token_required
def get_fornecedores_by_produto(produto_id):
    # Realiza o JOIN entre ProdutoFornecedor e Fornecedor
    fornecedores = (Fornecedor.query
                    .join(produto_fornecedor, Fornecedor.id == produto_fornecedor.fornecedor_id)
                    .filter(produto_fornecedor.produto_id == produto_id)
                    .filter(Fornecedor.removido == False)  # Exclui fornecedores marcados como removidos
                    .all())
    
    if fornecedores:
        return jsonify([{
            "id": fornecedor.id,
            "nome": fornecedor.nome
        } for fornecedor in fornecedores])
    else:
        return jsonify({"message": "Nenhum fornecedor encontrado para o produto especificado"}), 404


if __name__ == '__main__':
    app.run(port=5000, debug=True)