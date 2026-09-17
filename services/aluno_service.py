import os

from flask import current_app

from extensions import db
from models.avaliacao import AvaliacaoFisica
from models.mensalidade import Mensalidade
from models.pagamento import Pagamento
from models.pdf_gerado import PdfGerado
from models.treino import Treino


def excluir_aluno(aluno):
    caminhos_pdf = []
    pasta_pdf = os.path.abspath(os.path.join(current_app.instance_path, "pdfs"))
    for pdf in PdfGerado.query.filter_by(aluno_id=aluno.id).all():
        caminho = os.path.abspath(pdf.caminho)
        if os.path.commonpath([pasta_pdf, caminho]) == pasta_pdf:
            caminhos_pdf.append(caminho)
        db.session.delete(pdf)
    db.session.flush()

    # A exclusao pelo ORM remove tambem os dias e exercicios dos treinos.
    for modelo in (Pagamento, Mensalidade, Treino, AvaliacaoFisica):
        for registro in modelo.query.filter_by(aluno_id=aluno.id).all():
            db.session.delete(registro)
    db.session.flush()

    db.session.delete(aluno)
    db.session.commit()

    for caminho in caminhos_pdf:
        try:
            os.remove(caminho)
        except (FileNotFoundError, PermissionError):
            pass
