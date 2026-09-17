from datetime import date
import os

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from extensions import db
from models.aluno import Aluno
from models.avaliacao import AvaliacaoFisica
from models.mensalidade import Mensalidade
from models.pagamento import Pagamento
from models.pdf_gerado import PdfGerado
from models.plano import Plano
from models.treino import Treino
from services.pagamento_service import atualizar_pagamentos_atrasados


aluno_bp = Blueprint("aluno", __name__, url_prefix="/alunos")


def _criar_cobranca_do_aluno(aluno, data_vencimento):
    if not aluno.plano:
        return

    pagamento = Pagamento(
        aluno_id=aluno.id,
        valor=aluno.plano.valor,
        data=data_vencimento.isoformat(),
        status="Pendente",
        forma_pagamento="",
        banco="",
        chave_pix="",
    )

    mensalidade = Mensalidade(
        aluno_id=aluno.id,
        plano_id=aluno.plano.id,
        valor=aluno.plano.valor,
        data_vencimento=data_vencimento,
        status="pendente",
    )

    db.session.add(pagamento)
    db.session.add(mensalidade)


def _pagamento_atual(aluno_id):
    pagamento_aberto = Pagamento.query.filter(
        Pagamento.aluno_id == aluno_id,
        Pagamento.status.in_(["Pendente", "Atrasado", "pendente", "atrasado"]),
    ).order_by(Pagamento.data.asc(), Pagamento.id.asc()).first()

    if pagamento_aberto:
        return pagamento_aberto

    return Pagamento.query.filter_by(aluno_id=aluno_id).order_by(
        Pagamento.id.desc()
    ).first()


@aluno_bp.route("/")
def listar():
    atualizar_pagamentos_atrasados()
    busca = request.args.get("busca", "").strip()

    if busca:
        alunos = Aluno.query.filter(Aluno.nome.contains(busca)).all()
    else:
        alunos = Aluno.query.all()

    pagamentos_atuais = {
        aluno.id: _pagamento_atual(aluno.id)
        for aluno in alunos
    }

    return render_template(
        "alunos.html",
        alunos=alunos,
        pagamentos_atuais=pagamentos_atuais,
    )


@aluno_bp.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    planos = Plano.query.all()

    if request.method == "POST":
        plano = Plano.query.get_or_404(request.form["plano_id"])
        try:
            data_vencimento = date.fromisoformat(
                request.form.get("data_vencimento") or date.today().isoformat()
            )
            dias_treino = int(request.form["dias_treino"])
        except (TypeError, ValueError):
            flash("Informe uma data e uma frequencia de treino validas.")
            return render_template("cadastrar_aluno.html", planos=planos, data_atual=date.today().isoformat())

        if dias_treino not in (3, 5):
            flash("A frequencia de treino deve ser 3 ou 5 dias por semana.")
            return render_template("cadastrar_aluno.html", planos=planos, data_atual=date.today().isoformat())

        aluno = Aluno(
            nome=request.form["nome"],
            email=request.form["email"],
            telefone=request.form["telefone"],
            dias_treino=dias_treino,
            plano_id=plano.id,
        )
        aluno.plano = plano

        db.session.add(aluno)
        db.session.flush()

        _criar_cobranca_do_aluno(aluno, data_vencimento)

        db.session.commit()

        return redirect(url_for("aluno.listar"))

    return render_template(
        "cadastrar_aluno.html",
        planos=planos,
        data_atual=date.today().isoformat(),
    )


@aluno_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    aluno = Aluno.query.get_or_404(id)
    planos = Plano.query.all()

    if request.method == "POST":
        plano_anterior_id = aluno.plano_id
        novo_plano = Plano.query.get_or_404(request.form["plano_id"])

        aluno.nome = request.form["nome"]
        aluno.email = request.form["email"]
        aluno.telefone = request.form["telefone"]
        try:
            dias_treino = int(request.form["dias_treino"])
        except (TypeError, ValueError):
            flash("A frequencia de treino deve ser um numero valido.")
            return render_template("editar_aluno.html", aluno=aluno, planos=planos)

        if dias_treino not in (3, 5):
            flash("A frequencia de treino deve ser 3 ou 5 dias por semana.")
            return render_template("editar_aluno.html", aluno=aluno, planos=planos)

        aluno.dias_treino = dias_treino
        aluno.plano_id = novo_plano.id
        aluno.plano = novo_plano

        tem_cobranca_aberta = Pagamento.query.filter(
            Pagamento.aluno_id == aluno.id,
            Pagamento.status.in_(["Pendente", "Atrasado", "pendente", "atrasado"]),
        ).first()

        if plano_anterior_id != novo_plano.id and not tem_cobranca_aberta:
            _criar_cobranca_do_aluno(aluno, date.today())

        db.session.commit()

        return redirect(url_for("aluno.listar"))

    return render_template("editar_aluno.html", aluno=aluno, planos=planos)


@aluno_bp.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    aluno = Aluno.query.get_or_404(id)

    Pagamento.query.filter_by(aluno_id=aluno.id).delete()
    Treino.query.filter_by(aluno_id=aluno.id).delete()
    Mensalidade.query.filter_by(aluno_id=aluno.id).delete()

    pasta_pdf = os.path.abspath(os.path.join(current_app.instance_path, "pdfs"))
    for pdf in PdfGerado.query.filter_by(aluno_id=aluno.id).all():
        caminho_pdf = os.path.abspath(pdf.caminho)
        if os.path.commonpath([pasta_pdf, caminho_pdf]) == pasta_pdf and os.path.isfile(caminho_pdf):
            try:
                os.remove(caminho_pdf)
            except PermissionError:
                pass
        db.session.delete(pdf)

    AvaliacaoFisica.query.filter_by(aluno_id=aluno.id).delete()

    db.session.delete(aluno)
    db.session.commit()

    return redirect(url_for("aluno.listar"))
