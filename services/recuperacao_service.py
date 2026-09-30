import hashlib
import hmac
import smtplib
import ssl
import json
from urllib.request import Request, urlopen
from email.message import EmailMessage

from flask import current_app
from itsdangerous import URLSafeTimedSerializer


def serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='recuperar-senha')


def assinatura_senha(usuario):
    return hashlib.sha256(usuario.senha.encode()).hexdigest()


def criar_token(usuario):
    return serializer().dumps({'id': usuario.id, 'senha': assinatura_senha(usuario)})


def validar_token(token):
    from models.usuario import Usuario
    from extensions import db
    from itsdangerous import BadData
    try:
        dados = serializer().loads(token, max_age=1800)
        usuario = db.session.get(Usuario, dados['id'])
        if usuario and hmac.compare_digest(dados['senha'], assinatura_senha(usuario)):
            return usuario
    except (BadData, KeyError, TypeError):
        pass
    return None


def enviar_recuperacao(usuario, token):
    config = current_app.config
    base = config['PUBLIC_BASE_URL'].rstrip('/')
    if not base or not config['SMTP_FROM']:
        raise RuntimeError('Configure PUBLIC_BASE_URL e SMTP_FROM.')
    mensagem = EmailMessage()
    mensagem['Subject'] = 'Redefinir sua senha - Fit Trainer'
    mensagem['From'] = config['SMTP_FROM']
    mensagem['To'] = usuario.email
    mensagem.set_content(
        'Para criar uma nova senha, abra o link abaixo. Ele expira em 30 minutos '
        'e deixa de funcionar depois que a senha for alterada.\n\n'
        f'{base}/redefinir-senha/{token}\n\n'
        'Se voce nao solicitou esta alteracao, ignore este email.'
    )
    if config['RESEND_API_KEY']:
        payload = {'from': config['SMTP_FROM'], 'to': [usuario.email],
                   'subject': str(mensagem['Subject']), 'text': mensagem.get_content()}
        request = Request('https://api.resend.com/emails', data=json.dumps(payload).encode(),
                          headers={'Authorization': 'Bearer ' + config['RESEND_API_KEY'],
                                   'Content-Type': 'application/json', 'User-Agent': 'FitTrainer/1.0'}, method='POST')
        with urlopen(request, timeout=15) as response:
            response.read()
        return
    if not config['SMTP_HOST']:
        raise RuntimeError('Configure RESEND_API_KEY ou SMTP_HOST.')
    cliente = smtplib.SMTP_SSL if config['SMTP_SSL'] else smtplib.SMTP
    kwargs = {'timeout': 15}
    if config['SMTP_SSL']:
        kwargs['context'] = ssl.create_default_context()
    with cliente(config['SMTP_HOST'], config['SMTP_PORT'], **kwargs) as smtp:
        if not config['SMTP_SSL']:
            smtp.starttls(context=ssl.create_default_context())
        if config['SMTP_USERNAME']:
            smtp.login(config['SMTP_USERNAME'], config['SMTP_PASSWORD'])
        smtp.send_message(mensagem)
