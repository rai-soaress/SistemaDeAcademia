from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from models.usuario import Usuario
from extensions import db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
def login():
    return render_template("login.html")

@auth_bp.route("/logar", methods=["POST"])
def logar():
    email = request.form.get("email")
    senha = request.form.get("senha")

    usuario = Usuario.query.filter_by(email=email).first()

    senha_valida = usuario and (
        check_password_hash(usuario.senha, senha)
        if usuario.senha.startswith(("scrypt:", "pbkdf2:"))
        else usuario.senha == senha
    )

    if senha_valida:
        if usuario.senha == senha:
            usuario.senha = generate_password_hash(senha)
            db.session.commit()
        session["usuario_id"] = usuario.id
        session["usuario_nome"] = usuario.nome
        return redirect(url_for("admin.dashboard"))

    flash("Email ou senha inválidos.")
    return redirect(url_for("auth.login"))

@auth_bp.route("/cadastro-admin")
def cadastro_admin():
    return render_template("cadastro_admin.html")

@auth_bp.route("/registrar-admin", methods=["POST"])
def registrar_admin():
    nome = request.form.get("nome")
    email = request.form.get("email")
    senha = request.form.get("senha")

    if not (
        senha
        and len(senha) >= 8
        and any(c.isupper() for c in senha)
        and any(c.islower() for c in senha)
        and any(c.isdigit() for c in senha)
        and any(not c.isalnum() and not c.isspace() for c in senha)
    ):
        flash("A senha deve ter pelo menos 8 caracteres, com letra maiúscula, letra minúscula, número e símbolo.")
        return redirect(url_for("auth.cadastro_admin"))

    existe = Usuario.query.filter_by(email=email).first()

    if existe:
        flash("Esse email já está cadastrado.")
        return redirect(url_for("auth.cadastro_admin"))

    novo = Usuario(
        nome=nome,
        email=email,
        senha=generate_password_hash(senha),
    )

    db.session.add(novo)
    db.session.commit()

    flash("Administrador cadastrado com sucesso.")
    return redirect(url_for("auth.login"))

@auth_bp.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("auth.login"))
