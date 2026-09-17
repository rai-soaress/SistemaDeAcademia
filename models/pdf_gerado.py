from datetime import datetime

from extensions import db


class PdfGerado(db.Model):
    __tablename__ = "pdfs_gerados"

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey("alunos.id"), nullable=False)
    treino_id = db.Column(db.Integer, db.ForeignKey("treinos.id"), nullable=True)
    avaliacao_id = db.Column(db.Integer, db.ForeignKey("avaliacoes_fisicas.id"), nullable=True)
    caminho = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    aluno = db.relationship("Aluno", backref="pdfs_gerados")
    treino = db.relationship("Treino")
    avaliacao = db.relationship("AvaliacaoFisica")
