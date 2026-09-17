from flask import Blueprint, flash, render_template, request, redirect, url_for
from models.plano import Plano
from extensions import db

plano_bp = Blueprint("plano", __name__, url_prefix="/planos")

@plano_bp.route("/")
def listar():
    planos = Plano.query.all()
    return render_template("planos.html", planos=planos)

@plano_bp.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    if request.method == "POST":
        try:
            valor = float(request.form["valor"].replace(",", "."))
            dias_treino = int(request.form["dias_treino"])
        except (AttributeError, TypeError, ValueError):
            flash("Informe um valor e uma frequencia validos.")
            return render_template("cadastrar_plano.html")

        if dias_treino not in (3, 5):
            flash("A frequencia de treino deve ser 3 ou 5 dias por semana.")
            return render_template("cadastrar_plano.html")

        plano = Plano(
            nome=request.form["nome"], valor=valor,
            dias_treino=dias_treino, descricao=request.form["descricao"]
        )

        db.session.add(plano)
        db.session.commit()

        return redirect(url_for("plano.listar"))

    return render_template("cadastrar_plano.html")

@plano_bp.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    plano = Plano.query.get_or_404(id)

    if plano.alunos or plano.mensalidades:
        flash("Nao e possivel excluir um plano que ja possui alunos ou mensalidades.")
        return redirect(url_for("plano.listar"))

    db.session.delete(plano)
    db.session.commit()

    return redirect(url_for("plano.listar"))
