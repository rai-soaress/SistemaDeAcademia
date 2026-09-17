import os
from flask import Flask, redirect, url_for, request, session
from sqlalchemy import inspect, text
from config import Config
from extensions import db
from models.exercicio import Exercicio

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.aluno_routes import aluno_bp
from routes.plano_routes import plano_bp
from routes.pagamento_routes import pagamento_bp
from routes.treino_routes import treino_bp
from routes.despesa_routes import despesa_bp

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs("instance", exist_ok=True)

db.init_app(app)

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(aluno_bp)
app.register_blueprint(plano_bp)
app.register_blueprint(pagamento_bp)
app.register_blueprint(treino_bp)
app.register_blueprint(despesa_bp)


@app.before_request
def exigir_login():
    endpoint = request.endpoint or ""
    if endpoint.startswith("static") or endpoint.startswith("auth."):
        return None
    if "usuario_id" not in session:
        return redirect(url_for("auth.login"))
    return None

@app.route("/")
def index():
    return redirect(url_for("auth.login"))

with app.app_context():
    db.create_all()

    inspector = inspect(db.engine)
    colunas_planos = [coluna["name"] for coluna in inspector.get_columns("planos")]
    colunas_alunos = [coluna["name"] for coluna in inspector.get_columns("alunos")]
    colunas_pagamentos = [coluna["name"] for coluna in inspector.get_columns("pagamentos")]
    colunas_treinos = [coluna["name"] for coluna in inspector.get_columns("treinos")]

    if "dias_treino" not in colunas_planos:
        db.session.execute(
            text("ALTER TABLE planos ADD COLUMN dias_treino INTEGER NOT NULL DEFAULT 3")
        )
        db.session.commit()

    if "dias_treino" not in colunas_alunos:
        db.session.execute(
            text("ALTER TABLE alunos ADD COLUMN dias_treino INTEGER NOT NULL DEFAULT 3")
        )
        db.session.commit()

    if "data_pagamento" not in colunas_pagamentos:
        db.session.execute(
            text("ALTER TABLE pagamentos ADD COLUMN data_pagamento DATE")
        )
        db.session.commit()

    if "frequencia_semanal" not in colunas_treinos:
        db.session.execute(
            text("ALTER TABLE treinos ADD COLUMN frequencia_semanal INTEGER NOT NULL DEFAULT 3")
        )
        db.session.commit()

    if "data_criacao" not in colunas_treinos:
        db.session.execute(
            text("ALTER TABLE treinos ADD COLUMN data_criacao DATE")
        )
        db.session.commit()

    if "responsavel_tecnico" not in colunas_treinos:
        db.session.execute(
            text("ALTER TABLE treinos ADD COLUMN responsavel_tecnico VARCHAR(100)")
        )
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)
