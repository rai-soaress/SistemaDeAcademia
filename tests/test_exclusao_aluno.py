import tempfile
import unittest
from datetime import date
from pathlib import Path

from flask import Flask
from sqlalchemy import event

from extensions import db
from models.aluno import Aluno
from models.avaliacao import AvaliacaoFisica
from models.exercicio import Exercicio
from models.mensalidade import Mensalidade
from models.pagamento import Pagamento
from models.pdf_gerado import PdfGerado
from models.plano import Plano
from models.treino import Treino, TreinoDia, TreinoExercicio
from routes.aluno_routes import aluno_bp


class ExclusaoAlunoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = Flask(__name__, instance_path=self.temp.name)
        self.app.config.update(TESTING=True, SECRET_KEY='test', SQLALCHEMY_DATABASE_URI='sqlite:///:memory:')
        db.init_app(self.app)
        self.app.register_blueprint(aluno_bp)
        self.ctx = self.app.app_context()
        self.ctx.push()
        @event.listens_for(db.engine, 'connect')
        def foreign_keys(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.ctx.pop()
        self.temp.cleanup()

    def test_excluir_com_treino_avaliacao_pdf_e_cobrancas(self):
        plano = Plano(nome='Mensal', valor=100)
        aluno = Aluno(nome='Excluir', plano=plano)
        outro = Aluno(nome='Preservar', plano=plano)
        treino = Treino(aluno=aluno, objetivo='Forca')
        dia = TreinoDia(treino=treino, nome='A')
        item = TreinoExercicio(dia=dia, nome='Agachamento')
        avaliacao = AvaliacaoFisica(aluno=aluno, nome='Inicial')
        pagamento = Pagamento(aluno=aluno, valor=100, data='2026-09-30', status='Pendente')
        mensalidade = Mensalidade(aluno=aluno, plano=plano, valor=100, data_vencimento=date.today())
        arquivo = Path(self.temp.name) / 'pdfs' / 'teste.pdf'
        arquivo.parent.mkdir()
        arquivo.write_bytes(b'test')
        pdf = PdfGerado(aluno=aluno, treino=treino, avaliacao=avaliacao, caminho=str(arquivo))
        db.session.add_all([aluno, outro, treino, dia, item, avaliacao, pagamento, mensalidade, pdf])
        db.session.commit()
        aluno_id, outro_id = aluno.id, outro.id
        db.session.remove()
        response = self.app.test_client().post(f'/alunos/excluir/{aluno_id}')
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(db.session.get(Aluno, aluno_id))
        self.assertIsNotNone(db.session.get(Aluno, outro_id))
        self.assertEqual(Plano.query.count(), 1)
        for model in (Treino, TreinoDia, TreinoExercicio, AvaliacaoFisica, Pagamento, Mensalidade, PdfGerado):
            self.assertEqual(model.query.count(), 0, model.__name__)
        self.assertFalse(arquivo.exists())
