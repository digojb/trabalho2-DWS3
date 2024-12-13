
#MODELS BACK END

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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
    data_cadastro = db.Column(db.Date, default=datetime.utcnow)
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