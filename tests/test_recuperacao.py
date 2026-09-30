import unittest
from unittest.mock import patch

from flask import Flask
from extensions import db
from models.usuario import Usuario
from routes.auth_routes import auth_bp
from services.recuperacao_service import criar_token, validar_token
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path


class RecuperacaoTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__, template_folder=str(Path(__file__).resolve().parents[1] / 'templates'))
        self.app.config.update(TESTING=True, SECRET_KEY='test-secret', SQLALCHEMY_DATABASE_URI='sqlite:///:memory:')
        db.init_app(self.app)
        self.app.register_blueprint(auth_bp)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.user = Usuario(nome='Teste', email='teste@example.com', senha=generate_password_hash('Original1!'))
        db.session.add(self.user)
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def csrf(self, path):
        self.client.get(path)
        with self.client.session_transaction() as session:
            return session['recuperacao_csrf']

    def test_request_does_not_disclose_account(self):
        with patch('routes.auth_routes.enviar_recuperacao') as send:
            bodies = []
            for email in ('teste@example.com', 'ausente@example.com'):
                csrf = self.csrf('/recuperar-senha')
                response = self.client.post('/recuperar-senha', data={'csrf': csrf, 'email': email}, follow_redirects=True)
                bodies.append(response.data)
            self.assertEqual(bodies[0], bodies[1])
            send.assert_called_once()

    def test_reset_invalidates_link(self):
        token = criar_token(self.user)
        path = '/redefinir-senha/' + token
        csrf = self.csrf(path)
        response = self.client.post(path, data={'csrf': csrf, 'senha': 'NovaSenha1!', 'confirmacao': 'NovaSenha1!'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(check_password_hash(self.user.senha, 'NovaSenha1!'))
        self.assertIsNone(validar_token(token))

    def test_invalid_and_expired_token(self):
        self.assertIsNone(validar_token('invalido'))
        with patch('itsdangerous.timed.time.time', return_value=1000):
            token = criar_token(self.user)
        self.assertIsNone(validar_token(token))

    def test_csrf_and_password_rules(self):
        token = criar_token(self.user)
        path = '/redefinir-senha/' + token
        self.assertEqual(self.client.post(path, data={'senha': 'NovaSenha1!'}).status_code, 400)
        for senha, confirmacao in [('fraca', 'fraca'), ('NovaSenha1!', 'diferente')]:
            csrf = self.csrf(path)
            self.client.post(path, data={'csrf': csrf, 'senha': senha, 'confirmacao': confirmacao})
            self.assertTrue(check_password_hash(self.user.senha, 'Original1!'))

    def test_https_email_transport(self):
        from services.recuperacao_service import enviar_recuperacao
        self.app.config.update(PUBLIC_BASE_URL='https://academia.example', SMTP_FROM='contato@example.com', RESEND_API_KEY='test-key')
        with patch('services.recuperacao_service.urlopen') as send:
            enviar_recuperacao(self.user, 'test-token')
            request = send.call_args.args[0]
            self.assertEqual(request.full_url, 'https://api.resend.com/emails')
            self.assertIn(b'https://academia.example/redefinir-senha/test-token', request.data)


if __name__ == '__main__':
    unittest.main()
