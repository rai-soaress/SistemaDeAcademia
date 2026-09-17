from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, request
from models.aluno import Aluno
from models.plano import Plano
from models.pagamento import Pagamento
from models.mensalidade import Mensalidade
from models.treino import Treino
from models.despesa import Despesa
from services.pagamento_service import atualizar_pagamentos_atrasados

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _converter_data_pagamento(valor):
    if not valor:
        return None

    if isinstance(valor, date):
        return valor

    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(valor, formato).date()
        except ValueError:
            continue

    return None


def _data_recebimento_pagamento(pagamento):
    if pagamento.data_pagamento:
        return pagamento.data_pagamento

    data_vencimento = _converter_data_pagamento(pagamento.data)

    if data_vencimento:
        mensalidade = Mensalidade.query.filter(
            Mensalidade.aluno_id == pagamento.aluno_id,
            Mensalidade.data_vencimento == data_vencimento,
            Mensalidade.status.in_(["pago", "Pago"]),
        ).first()

        if mensalidade and mensalidade.data_pagamento:
            return mensalidade.data_pagamento

    return data_vencimento


@admin_bp.route("/dashboard")
def dashboard():
    atualizar_pagamentos_atrasados()
    hoje = date.today()
    mes_selecionado = request.args.get("mes", "")
    try:
        inicio_mes = date.fromisoformat(f"{mes_selecionado}-01")
    except ValueError:
        inicio_mes = hoje.replace(day=1)
        mes_selecionado = inicio_mes.strftime("%Y-%m")

    if inicio_mes.month == 12:
        inicio_proximo_mes = date(inicio_mes.year + 1, 1, 1)
    else:
        inicio_proximo_mes = date(inicio_mes.year, inicio_mes.month + 1, 1)
    fim_mes = inicio_proximo_mes - timedelta(days=1)

    total_alunos = Aluno.query.count()
    total_planos = Plano.query.count()
    total_pagamentos = Pagamento.query.count()
    total_treinos = Treino.query.count()
    alunos_inadimplentes = Pagamento.query.with_entities(Pagamento.aluno_id).filter(
        Pagamento.status.in_(["Atrasado", "atrasado"])
    ).distinct().count()

    pagamentos = Pagamento.query.all()
    despesas_mes = Despesa.query.filter(
        Despesa.data >= inicio_mes,
        Despesa.data <= fim_mes
    ).all()

    entradas_mes = 0
    pagamentos_pendentes = 0
    pagamentos_atrasados = 0

    for pagamento in pagamentos:
        status = (pagamento.status or "").lower().strip()
        data_recebimento = _data_recebimento_pagamento(pagamento)
        data_vencimento = _converter_data_pagamento(pagamento.data)
        valor = pagamento.valor or 0

        if status == "pago" and data_recebimento and inicio_mes <= data_recebimento <= fim_mes:
            entradas_mes += valor

        if status == "pendente" and data_vencimento and inicio_mes <= data_vencimento <= fim_mes:
            pagamentos_pendentes += valor

        if status != "pago" and data_vencimento and inicio_mes <= data_vencimento <= fim_mes and data_vencimento < hoje:
            pagamentos_atrasados += valor

    saidas_mes = sum(despesa.valor for despesa in despesas_mes)
    lucro_mes = entradas_mes - saidas_mes

    return render_template(
        "admin_dashboard.html",
        total_alunos=total_alunos,
        total_planos=total_planos,
        total_pagamentos=total_pagamentos,
        total_treinos=total_treinos,
        alunos_inadimplentes=alunos_inadimplentes,
        entradas_mes=entradas_mes,
        saidas_mes=saidas_mes,
        lucro_mes=lucro_mes,
        pagamentos_pendentes=pagamentos_pendentes,
        pagamentos_atrasados=pagamentos_atrasados,
        mes_atual=inicio_mes.strftime("%m/%Y"),
        mes_selecionado=mes_selecionado,
    )
