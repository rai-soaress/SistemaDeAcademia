from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import secrets
import hmac
from services.recuperacao_service import criar_token, validar_token, enviar_recuperacao
from werkzeug.security import check_password_hash, generate_password_hash
from models.usuario import Usuario
from extensions import db

auth_bp = Blueprint("auth", __name__)


def senha_forte(senha):
    return (len(senha) >= 8 and any(c.isupper() for c in senha)
            and any(c.islower() for c in senha) and any(c.isdigit() for c in senha)
            and any(not c.isalnum() and not c.isspace() for c in senha))


@auth_bp.route('/recuperar-senha', methods=['GET', 'POST'])
def recuperar_senha():
    if request.method == 'POST':
        if not hmac.compare_digest(session.get('recuperacao_csrf', ''), request.form.get('csrf', '')) or not session.get('recuperacao_csrf'):
            return 'Formulario expirado. Recarregue a pagina.', 400
        usuario = Usuario.query.filter_by(email=request.form.get('email', '').strip()).first()
        if usuario:
            try:
                enviar_recuperacao(usuario, criar_token(usuario))
            except Exception:
                current_app.logger.error('Falha ao enviar email de recuperacao; verifique a configuracao SMTP.')
        flash('Se o e-mail estiver cadastrado, você receberá um link para redefinir a senha. Confira também o spam.')
        return redirect(url_for('auth.login'))
    session['recuperacao_csrf'] = secrets.token_urlsafe(32)
    return render_template('recuperar_senha.html', redefinir=False)


@auth_bp.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    usuario = validar_token(token)
    if not usuario:
        flash('Link inválido ou expirado. Solicite um novo link.')
        return redirect(url_for('auth.recuperar_senha'))
    if request.method == 'POST':
        if not session.get('recuperacao_csrf') or not hmac.compare_digest(session['recuperacao_csrf'], request.form.get('csrf', '')):
            return 'Formulario expirado. Recarregue a pagina.', 400
        senha = request.form.get('senha', '')
        if not senha_forte(senha):
            flash('Use pelo menos 8 caracteres, com maiúscula, minúscula, número e símbolo.')
        elif senha != request.form.get('confirmacao'):
            flash('As senhas não coincidem.')
        else:
            usuario.senha = generate_password_hash(senha)
            db.session.commit()
            session.clear()
            flash('Senha redefinida! Entre com sua nova senha.')
            return redirect(url_for('auth.login'))
    session['recuperacao_csrf'] = secrets.token_urlsafe(32)
    response = current_app.make_response(render_template('recuperar_senha.html', redefinir=True))
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store'
    return response

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
