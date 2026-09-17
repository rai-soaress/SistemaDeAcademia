from extensions import db

class Plano(db.Model):
    __tablename__ = "planos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    dias_treino = db.Column(db.Integer, nullable=False, default=3)
    descricao = db.Column(db.Text)
