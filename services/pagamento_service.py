from datetime import date

from extensions import db
from models.mensalidade import Mensalidade
from models.pagamento import Pagamento


def _converter_data(valor):
    if not valor:
        return None

    if isinstance(valor, date):
        return valor

    try:
        return date.fromisoformat(valor)
    except ValueError:
        return None


def atualizar_pagamentos_atrasados():
    hoje = date.today()
    alterou = False

    pagamentos = Pagamento.query.filter(
        Pagamento.status.in_(["Pendente", "pendente"])
    ).all()

    for pagamento in pagamentos:
        data_vencimento = _converter_data(pagamento.data)

        if data_vencimento and data_vencimento < hoje:
            pagamento.status = "Atrasado"
            alterou = True

    mensalidades = Mensalidade.query.filter(
        Mensalidade.status.in_(["pendente", "Pendente"])
    ).all()

    for mensalidade in mensalidades:
        if mensalidade.data_vencimento < hoje:
            mensalidade.status = "atrasado"
            alterou = True

    if alterou:
        db.session.commit()
