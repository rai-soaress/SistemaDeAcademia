from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models.despesa import Despesa


despesa_bp = Blueprint("despesa", __name__, url_prefix="/despesas")

CATEGORIAS_DESPESA = [
    "Agua",
    "Energia",
    "Internet",
    "Aluguel",
    "Manutencao",
    "Compra de equipamentos",
    "Limpeza",
    "Outros",
]


@despesa_bp.route("/")
def listar():
    busca = request.args.get("busca", "").strip()
    categoria = request.args.get("categoria", "").strip()
    mes_selecionado = request.args.get("mes", "")
    try:
        inicio_mes = date.fromisoformat(f"{mes_selecionado}-01")
    except ValueError:
        inicio_mes = date.today().replace(day=1)
        mes_selecionado = inicio_mes.strftime("%Y-%m")

    if inicio_mes.month == 12:
        inicio_proximo_mes = date(inicio_mes.year + 1, 1, 1)
    else:
        inicio_proximo_mes = date(inicio_mes.year, inicio_mes.month + 1, 1)

    query = Despesa.query.filter(
        Despesa.data >= inicio_mes,
        Despesa.data < inicio_proximo_mes,
    )

    if busca:
        query = query.filter(Despesa.descricao.contains(busca))

    if categoria:
        query = query.filter(Despesa.categoria == categoria)

    despesas = query.order_by(Despesa.data.desc(), Despesa.id.desc()).all()
    total_despesas = sum(despesa.valor for despesa in despesas)

    return render_template(
        "despesas.html",
        despesas=despesas,
        categorias=CATEGORIAS_DESPESA,
        busca=busca,
        categoria_selecionada=categoria,
        mes_selecionado=mes_selecionado,
        mes_atual=inicio_mes.strftime("%m/%Y"),
        total_despesas=total_despesas,
    )


@despesa_bp.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    if request.method == "POST":
        try:
            valor = float(request.form["valor"].replace(",", "."))
            data_despesa = date.fromisoformat(request.form["data"])
        except (AttributeError, TypeError, ValueError):
            flash("Informe um valor e uma data validos.")
            return render_template("cadastrar_despesa.html", categorias=CATEGORIAS_DESPESA, data_atual=date.today().isoformat())

        despesa = Despesa(
            descricao=request.form["descricao"], valor=valor,
            categoria=request.form["categoria"], data=data_despesa,
            observacao=request.form.get("observacao", ""),
        )

        db.session.add(despesa)
        db.session.commit()

        return redirect(url_for("despesa.listar"))

    return render_template(
        "cadastrar_despesa.html",
        categorias=CATEGORIAS_DESPESA,
        data_atual=date.today().isoformat(),
    )


@despesa_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    despesa = Despesa.query.get_or_404(id)

    if request.method == "POST":
        despesa.descricao = request.form["descricao"]
        try:
            despesa.valor = float(request.form["valor"].replace(",", "."))
            despesa.data = date.fromisoformat(request.form["data"])
        except (AttributeError, TypeError, ValueError):
            flash("Informe um valor e uma data validos.")
            return render_template("editar_despesa.html", despesa=despesa, categorias=CATEGORIAS_DESPESA)

        despesa.categoria = request.form["categoria"]
        despesa.observacao = request.form.get("observacao", "")

        db.session.commit()

        return redirect(url_for("despesa.listar"))

    return render_template(
        "editar_despesa.html",
        despesa=despesa,
        categorias=CATEGORIAS_DESPESA,
    )


@despesa_bp.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    despesa = Despesa.query.get_or_404(id)

    db.session.delete(despesa)
    db.session.commit()

    return redirect(url_for("despesa.listar"))
