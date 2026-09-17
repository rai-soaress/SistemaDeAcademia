from extensions import db

class Aluno(db.Model):
    __tablename__ = "alunos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    dias_treino = db.Column(db.Integer, nullable=False, default=3)

    plano_id = db.Column(db.Integer, db.ForeignKey("planos.id"))
    plano = db.relationship("Plano", backref="alunos")
