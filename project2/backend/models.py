from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime

#SQLAlchemy é um ORM (Object Relational Mapper) usado para interação com bancos de dados relacionais, como o PostgreSQL.
#É a biblioteca que faz a conexão com o banco de dados e mapear as classes do Python para tabelas no banco.

# Configurações do app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://angelo:8zb8usf3aflo3ayy@44.219.162.7:5432/sistema_gestao'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'jduask@&dsauinwd4567'
db = SQLAlchemy(app)


# Relacionamento 1:N: Categoria -> Produto
class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    removido = db.Column(db.Boolean, default=False)
    produtos = db.relationship('Produto', backref='categoria', lazy=True)

# Tabela intermediária de muitos-para-muitos
produto_fornecedor = db.Table(
    'produto_fornecedor',
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


# Modelo Users
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Inicializa o banco de dados
with app.app_context():
    db.create_all()
