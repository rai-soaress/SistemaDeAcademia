from extensions import db
from datetime import date

class Treino(db.Model):
    __tablename__ = "treinos"

    id = db.Column(db.Integer, primary_key=True)

    aluno_id = db.Column(db.Integer, db.ForeignKey("alunos.id"), nullable=False)
    aluno = db.relationship("Aluno", backref="treinos")

    objetivo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False, default="")
    frequencia_semanal = db.Column(db.Integer, nullable=False, default=3)
    data_criacao = db.Column(db.Date, nullable=False, default=date.today)
    responsavel_tecnico = db.Column(db.String(100), nullable=True)

    dias = db.relationship(
        "TreinoDia",
        backref="treino",
        cascade="all, delete-orphan",
        order_by="TreinoDia.ordem",
    )


class TreinoDia(db.Model):
    __tablename__ = "treino_dias"

    id = db.Column(db.Integer, primary_key=True)
    treino_id = db.Column(db.Integer, db.ForeignKey("treinos.id"), nullable=False)
    nome = db.Column(db.String(30), nullable=False)
    ordem = db.Column(db.Integer, nullable=False, default=0)

    exercicios = db.relationship(
        "TreinoExercicio",
        backref="dia",
        cascade="all, delete-orphan",
        order_by="TreinoExercicio.ordem",
    )


class TreinoExercicio(db.Model):
    __tablename__ = "treino_exercicios"

    id = db.Column(db.Integer, primary_key=True)
    treino_dia_id = db.Column(db.Integer, db.ForeignKey("treino_dias.id"), nullable=False)
    exercicio_id = db.Column(db.Integer, db.ForeignKey("exercicios.id"), nullable=True)
    nome = db.Column(db.String(120), nullable=False)
    grupo_muscular = db.Column(db.String(80), nullable=True)
    equipamento = db.Column(db.String(80), nullable=True)
    imagem_url = db.Column(db.String(255), nullable=True)
    gif_url = db.Column(db.String(255), nullable=True)
    video_url = db.Column(db.String(255), nullable=True)
    series = db.Column(db.String(30), nullable=False, default="3")
    repeticoes = db.Column(db.String(30), nullable=False, default="12")
    carga = db.Column(db.String(30), nullable=True)
    descanso = db.Column(db.String(30), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    ordem = db.Column(db.Integer, nullable=False, default=0)

    exercicio = db.relationship("Exercicio")
