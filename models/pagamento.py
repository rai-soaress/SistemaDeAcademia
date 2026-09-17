from extensions import db

class Pagamento(db.Model):
    __tablename__ = "pagamentos"

    id = db.Column(db.Integer, primary_key=True)

    aluno_id = db.Column(db.Integer, db.ForeignKey("alunos.id"), nullable=False)
    aluno = db.relationship("Aluno", backref="pagamentos")

    valor = db.Column(db.Float, nullable=False)
    data = db.Column(db.String(20), nullable=False)
    data_pagamento = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(30), nullable=False)

    forma_pagamento = db.Column(db.String(50))
    banco = db.Column(db.String(100))
    chave_pix = db.Column(db.String(150))
