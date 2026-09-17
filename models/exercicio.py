from extensions import db


class Exercicio(db.Model):
    __tablename__ = "exercicios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    grupo_muscular = db.Column(db.String(80), nullable=False)
    equipamento = db.Column(db.String(80), nullable=True)
    musculo_principal = db.Column(db.String(80), nullable=True)
    musculos_secundarios = db.Column(db.String(180), nullable=True)
    imagem_url = db.Column(db.String(255), nullable=True)
    gif_url = db.Column(db.String(255), nullable=True)
    video_url = db.Column(db.String(255), nullable=True)
    personalizado = db.Column(db.Boolean, nullable=False, default=False)
