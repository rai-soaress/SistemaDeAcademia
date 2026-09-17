from extensions import db


class Despesa(db.Model):
    __tablename__ = "despesas"

    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(150), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    categoria = db.Column(db.String(80), nullable=False)
    data = db.Column(db.Date, nullable=False)
    observacao = db.Column(db.Text)
