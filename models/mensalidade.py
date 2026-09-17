from extensions import db
from datetime import date


class Mensalidade(db.Model):
    __tablename__ = "mensalidades"

    id = db.Column(db.Integer, primary_key=True)

    aluno_id = db.Column(db.Integer, db.ForeignKey("alunos.id"), nullable=False)
    plano_id = db.Column(db.Integer, db.ForeignKey("planos.id"), nullable=False)

    valor = db.Column(db.Float, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)

    status = db.Column(db.String(20), default="pendente")
    data_pagamento = db.Column(db.Date, nullable=True)

    forma_pagamento = db.Column(db.String(30), nullable=True)
    codigo_transacao = db.Column(db.String(100), nullable=True)

    aluno = db.relationship("Aluno", backref="mensalidades")
    plano = db.relationship("Plano", backref="mensalidades")

    def verificar_atraso(self):
        if self.status == "pendente" and self.data_vencimento < date.today():
            self.status = "atrasado"