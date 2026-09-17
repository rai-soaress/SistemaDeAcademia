from datetime import date

from extensions import db


class AvaliacaoFisica(db.Model):
    __tablename__ = "avaliacoes_fisicas"

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey("alunos.id"), nullable=False)
    aluno = db.relationship("Aluno", backref="avaliacoes_fisicas")

    nome = db.Column(db.String(100), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=True)
    responsavel_tecnico = db.Column(db.String(100), nullable=True)
    data_inicio = db.Column(db.Date, nullable=True)
    objetivo = db.Column(db.String(100), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    data_avaliacao = db.Column(db.Date, nullable=False, default=date.today)

    peso = db.Column(db.Float, nullable=True)
    altura = db.Column(db.Float, nullable=True)
    imc = db.Column(db.Float, nullable=True)

    braco = db.Column(db.Float, nullable=True)
    antebraco = db.Column(db.Float, nullable=True)
    panturrilha = db.Column(db.Float, nullable=True)
    perna = db.Column(db.Float, nullable=True)
    torax = db.Column(db.Float, nullable=True)
    abdomen = db.Column(db.Float, nullable=True)
    cintura = db.Column(db.Float, nullable=True)
    quadril = db.Column(db.Float, nullable=True)
