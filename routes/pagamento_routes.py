from calendar import monthrange
from datetime import date

from flask import Blueprint, flash, render_template, request, redirect, url_for
from models.pagamento import Pagamento
from models.aluno import Aluno
from models.mensalidade import Mensalidade
from services.pagamento_service import atualizar_pagamentos_atrasados
from services.aluno_service import excluir_aluno
from extensions import db

pagamento_bp = Blueprint("pagamento", __name__, url_prefix="/pagamentos")


def _adicionar_um_mes(data_base):
    mes = data_base.month + 1
    ano = data_base.year

    if mes > 12:
        mes = 1
        ano += 1

    ultimo_dia = monthrange(ano, mes)[1]
    dia = min(data_base.day, ultimo_dia)

    return date(ano, mes, dia)


def _converter_data(valor):
    if not valor:
        return date.today()

    try:
        return date.fromisoformat(valor)
    except ValueError:
        return date.today()


@pagamento_bp.route("/")
def listar():
    atualizar_pagamentos_atrasados()
    status_atual = request.args.get("status", "todos")
    query = Pagamento.query

    if status_atual == "pendentes":
        query = query.filter(Pagamento.status.in_(["Pendente", "pendente"]))
    elif status_atual == "atrasados":
        query = query.filter(Pagamento.status.in_(["Atrasado", "atrasado"]))
    elif status_atual == "pagos":
        query = query.filter(Pagamento.status.in_(["Pago", "pago"]))
    else:
        status_atual = "todos"

    pagamentos = query.order_by(Pagamento.data.asc(), Pagamento.id.desc()).all()
    grupos = {}
    for pagamento in pagamentos:
        grupo = grupos.setdefault(pagamento.aluno_id, {
            "aluno": pagamento.aluno,
            "pagamentos": [],
            "total_pago": 0,
            "total_em_aberto": 0,
        })
        grupo["pagamentos"].append(pagamento)
        if (pagamento.status or "").lower().strip() == "pago":
            grupo["total_pago"] += pagamento.valor or 0
        else:
            grupo["total_em_aberto"] += pagamento.valor or 0

    historicos = sorted(grupos.values(), key=lambda grupo: grupo["aluno"].nome.lower())
    for historico in historicos:
        historico["pagamentos"].sort(key=lambda pagamento: pagamento.id, reverse=True)

    contadores = {
        "todos": Pagamento.query.count(),
        "pendentes": Pagamento.query.filter(
            Pagamento.status.in_(["Pendente", "pendente"])
        ).count(),
        "atrasados": Pagamento.query.filter(
            Pagamento.status.in_(["Atrasado", "atrasado"])
        ).count(),
        "pagos": Pagamento.query.filter(
            Pagamento.status.in_(["Pago", "pago"])
        ).count(),
    }

    return render_template(
        "pagamentos.html",
        pagamentos=pagamentos,
        historicos=historicos,
        status_atual=status_atual,
        contadores=contadores,
    )


@pagamento_bp.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    alunos = Aluno.query.all()

    if request.method == "POST":
        aluno_id = request.form["aluno_id"]
        aluno = Aluno.query.get_or_404(aluno_id)

        valor = request.form.get("valor")

        if not valor and aluno.plano:
            valor = aluno.plano.valor

        status = request.form["status"]

        try:
            valor_numerico = float(str(valor).replace(",", "."))
        except (TypeError, ValueError):
            flash("Informe um valor de pagamento valido.")
            return render_template("cadastrar_pagamento.html", alunos=alunos)

        if valor_numerico < 0:
            flash("O valor do pagamento nao pode ser negativo.")
            return render_template("cadastrar_pagamento.html", alunos=alunos)

        pagamento = Pagamento(
            aluno_id=aluno.id,
            valor=valor_numerico,
            data=request.form["data"],
            data_pagamento=date.today() if status.lower().strip() == "pago" else None,
            status=status,
            forma_pagamento=request.form["forma_pagamento"],
            banco=request.form["banco"],
            chave_pix=request.form["chave_pix"]
        )

        db.session.add(pagamento)
        db.session.commit()

        return redirect(url_for("pagamento.listar"))

    return render_template("cadastrar_pagamento.html", alunos=alunos)


@pagamento_bp.route("/baixar/<int:id>", methods=["POST"])
def baixar(id):
    pagamento = Pagamento.query.get_or_404(id)
    hoje = date.today()
    forma_pagamento = request.form.get("forma_pagamento", "").strip()

    pagamento.status = "Pago"
    pagamento.data_pagamento = hoje
    pagamento.forma_pagamento = forma_pagamento or pagamento.forma_pagamento or "Nao informado"

    mensalidade = Mensalidade.query.filter(
        Mensalidade.aluno_id == pagamento.aluno_id,
        Mensalidade.status.in_(["pendente", "atrasado", "Pendente", "Atrasado"]),
    ).order_by(Mensalidade.data_vencimento.asc()).first()

    if mensalidade:
        mensalidade.status = "pago"
        mensalidade.data_pagamento = hoje
        mensalidade.forma_pagamento = pagamento.forma_pagamento
    elif pagamento.aluno and pagamento.aluno.plano:
        mensalidade = Mensalidade(
            aluno_id=pagamento.aluno.id,
            plano_id=pagamento.aluno.plano.id,
            valor=pagamento.valor,
            data_vencimento=hoje,
            status="pago",
            data_pagamento=hoje,
            forma_pagamento=pagamento.forma_pagamento,
        )
        db.session.add(mensalidade)

    db.session.commit()

    if pagamento.aluno and pagamento.aluno.plano:
        return redirect(url_for("pagamento.pos_baixa", id=pagamento.id))

    return redirect(url_for("pagamento.listar"))


@pagamento_bp.route("/pos-baixa/<int:id>")
def pos_baixa(id):
    pagamento = Pagamento.query.get_or_404(id)
    data_vencimento = _converter_data(pagamento.data)
    proxima_data = _adicionar_um_mes(data_vencimento)

    return render_template(
        "pos_baixa_pagamento.html",
        pagamento=pagamento,
        proxima_data=proxima_data,
    )


@pagamento_bp.route("/gerar-proxima/<int:id>", methods=["POST"])
def gerar_proxima(id):
    pagamento = Pagamento.query.get_or_404(id)
    aluno = pagamento.aluno

    if not aluno or not aluno.plano:
        return redirect(url_for("pagamento.listar"))

    data_vencimento = _converter_data(pagamento.data)
    proxima_data = _adicionar_um_mes(data_vencimento)

    cobranca_aberta = Pagamento.query.filter(
        Pagamento.aluno_id == aluno.id,
        Pagamento.status.in_(["Pendente", "Atrasado", "pendente", "atrasado"]),
    ).first()

    if not cobranca_aberta:
        nova_cobranca = Pagamento(
            aluno_id=aluno.id,
            valor=aluno.plano.valor,
            data=proxima_data.isoformat(),
            status="Pendente",
            forma_pagamento="",
            banco="",
            chave_pix="",
        )
        db.session.add(nova_cobranca)

    mensalidade_aberta = Mensalidade.query.filter(
        Mensalidade.aluno_id == aluno.id,
        Mensalidade.status.in_(["pendente", "atrasado", "Pendente", "Atrasado"]),
    ).first()

    if not mensalidade_aberta:
        nova_mensalidade = Mensalidade(
            aluno_id=aluno.id,
            plano_id=aluno.plano.id,
            valor=aluno.plano.valor,
            data_vencimento=proxima_data,
            status="pendente",
        )
        db.session.add(nova_mensalidade)

    db.session.commit()

    return redirect(url_for("aluno.listar"))


@pagamento_bp.route("/cancelar-plano/<int:id>", methods=["POST"])
def cancelar_plano(id):
    pagamento = Pagamento.query.get_or_404(id)
    aluno = pagamento.aluno

    if aluno:
        excluir_aluno(aluno)

    return redirect(url_for("aluno.listar"))


@pagamento_bp.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    pagamento = Pagamento.query.get_or_404(id)

    db.session.delete(pagamento)
    db.session.commit()

    return redirect(url_for("pagamento.listar"))
