import unittest
from pathlib import Path
from unittest.mock import patch
from flask import Flask
from sqlalchemy.exc import SQLAlchemyError
from extensions import db
from models.usuario import Usuario
from routes.auth_routes import auth_bp
from werkzeug.security import check_password_hash


class CadastroTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__, template_folder=str(Path(__file__).resolve().parents[1] / 'templates'))
        self.app.config.update(TESTING=True, SECRET_KEY='test', SQLALCHEMY_DATABASE_URI='sqlite:///:memory:')
        db.init_app(self.app)
        self.app.register_blueprint(auth_bp)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        self.data = dict(nome='Teste', email='teste@example.com', senha='SenhaTeste1!')

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.ctx.pop()

    def test_cadastro_e_duplicado(self):
        response = self.client.post('/registrar-admin', data=self.data, follow_redirects=True)
        self.assertIn('cadastrado com sucesso', response.get_data(as_text=True))
        self.assertTrue(check_password_hash(Usuario.query.one().senha, self.data['senha']))
        response = self.client.post('/registrar-admin', data=self.data)
        self.assertEqual(response.status_code, 409)
        self.assertIn('já está cadastrado', response.get_data(as_text=True))
        self.assertIn('value="teste@example.com"', response.get_data(as_text=True))
        self.assertEqual(Usuario.query.count(), 1)

    def test_senha_fraca_preserva_campos(self):
        self.data['senha'] = 'abcdefgh'
        response = self.client.post('/registrar-admin', data=self.data)
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn('letra maiúscula', html)
        self.assertIn('value="Teste"', html)
        self.assertIn('value="teste@example.com"', html)
        self.assertNotIn('abcdefgh', html)
        self.assertEqual(Usuario.query.count(), 0)

    def test_falha_banco_nao_confirma_cadastro(self):
        with patch.object(db.session, 'commit', side_effect=SQLAlchemyError('test')):
            response = self.client.post('/registrar-admin', data=self.data)
        self.assertEqual(response.status_code, 503)
        self.assertIn('Não foi possível salvar', response.get_data(as_text=True))
        self.assertEqual(Usuario.query.count(), 0)
