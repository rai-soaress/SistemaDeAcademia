from datetime import date
import os
import json
from uuid import uuid4
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, send_file, send_from_directory, url_for
from werkzeug.utils import secure_filename

from extensions import db
from models.aluno import Aluno
from models.avaliacao import AvaliacaoFisica
from models.exercicio import Exercicio
from models.pdf_gerado import PdfGerado
from models.treino import Treino, TreinoDia, TreinoExercicio
from services.pdf_service import gerar_pdf_avaliacao, gerar_pdf_completo

treino_bp = Blueprint("treino", __name__, url_prefix="/treinos")

EXTENSOES_IMAGEM = {"jpg", "jpeg", "png", "webp"}
EXTENSOES_VIDEO = {"mp4", "webm", "mov", "avi"}


def _salvar_midia(arquivo, extensoes_permitidas):
    if not arquivo or not arquivo.filename:
        return ""

    nome_seguro = secure_filename(arquivo.filename)
    extensao = nome_seguro.rsplit(".", 1)[-1].lower() if "." in nome_seguro else ""
    if extensao not in extensoes_permitidas:
        return ""

    nome = f"{uuid4().hex}.{extensao}"
    pasta = os.path.join(current_app.instance_path, "uploads", "exercicios")
    os.makedirs(pasta, exist_ok=True)
    arquivo.save(os.path.join(pasta, nome))
    return url_for("treino.midia_exercicio", nome=nome)


DIAS_TREINO = {
    3: [(1, "Segunda-feira"), (3, "Quarta-feira"), (5, "Sexta-feira")],
    5: [
        (1, "Segunda-feira"),
        (2, "Terca-feira"),
        (3, "Quarta-feira"),
        (4, "Quinta-feira"),
        (5, "Sexta-feira"),
    ],
}

OBJETIVOS = [
    "Hipertrofia",
    "Emagrecimento",
    "Saude",
    "Fortalecimento Muscular",
    "Ganho de Forca",
    "Condicionamento Fisico",
    "Definicao Muscular",
    "Outro",
]

CATEGORIAS_PT = {
    "Arms": "Bracos",
    "Back": "Costas",
    "Calves": "Panturrilhas",
    "Cardio": "Cardio",
    "Chest": "Peito",
    "Legs": "Pernas",
    "Shoulders": "Ombros",
    "Abs": "Abdomen",
    "Bench": "Banco",
    "Dumbbell": "Halteres",
    "Barbell": "Barra",
    "Cable": "Cabo",
    "Gym mat": "Colchonete",
    "Pull-up bar": "Barra fixa",
    "Swiss Ball": "Bola suica",
    "none (bodyweight exercise)": "Peso corporal",
    "back": "Costas",
    "chest": "Peito",
    "legs": "Pernas",
    "shoulders": "Ombros",
    "upper arms": "Bracos",
    "lower arms": "Antebracos",
    "waist": "Abdomen",
    "cardio": "Cardio",
}

EXERCICIOS_PT = {
    "Crunches": "Abdominal crunch",
    "Negative Crunches": "Abdominal crunch negativo",
    "Hyperextensions": "Extensao lombar",
    "Push-ups": "Flexao de braco",
    "Pull-ups": "Barra fixa",
    "Squats": "Agachamento",
    "Bench Press": "Supino reto",
    "Incline Bench Press": "Supino inclinado",
    "Deadlift": "Levantamento terra",
    "Lunges": "Avanco",
    "Biceps Curls": "Rosca biceps",
    "Triceps Extensions": "Extensao de triceps",
    "Shoulder Press": "Desenvolvimento de ombros",
    "Leg Press": "Leg press",
    "Plank": "Prancha",
}

TERMOS_EXERCICIO_PT = {
    "upward facing dog": "cachorro olhando para cima",
    "assisted hanging knee raise": "elevacao de joelhos suspensa assistida",
    "hanging knee raise": "elevacao de joelhos suspensa",
    "impossible dips": "paralelas avancadas",
    "kneeling cable crunch": "abdominal ajoelhado no cabo",
    "lying leg raise": "elevacao de pernas deitado",
    "standing calf raise": "elevacao de panturrilha em pe",
    "barbell bench press": "supino com barra",
    "dumbbell bench press": "supino com halteres",
    "incline dumbbell press": "supino inclinado com halteres",
    "romanian deadlift": "levantamento terra romeno",
    "push-up": "flexao de braco",
    "push up": "flexao de braco",
    "inside leg kick": "chute interno de perna",
    "cable crossover": "cruzamento de cabos",
    "cross-over": "cruzamento de cabos",
    "variation": "variacao",
    "Bench Press": "Supino",
    "Narrow Grip": "pegada fechada",
    "Wide Grip": "pegada aberta",
    "Biceps Curl": "Rosca biceps",
    "Curl": "Rosca",
    "Cable": "cabo",
    "Dumbbell": "halter",
    "Barbell": "barra",
    "Shoulder": "ombro",
    "Press": "desenvolvimento",
    "Row": "remada",
    "Pulldown": "puxada",
    "Extension": "extensao",
    "Leg": "perna",
    "Calf": "panturrilha",
    "Raise": "elevacao",
    "Lateral": "lateral",
    "Seated": "sentado",
    "Standing": "em pe",
    "Incline": "inclinado",
    "Decline": "declinado",
    "Front": "frontal",
    "Back": "costas",
    "Squat": "agachamento",
    "Crunch": "abdominal",
    "With": "com",
    "Machine": "maquina",
    "One Arm": "unilateral",
    "Two Arm": "bilateral",
}


def _traduzir(valor, mapa):
    if not valor:
        return ""

    partes = [parte.strip() for parte in str(valor).split(",") if parte.strip()]

    if len(partes) > 1:
        return ", ".join(mapa.get(parte, parte) for parte in partes)

    return mapa.get(valor, valor)


def _traduzir_nome_exercicio(nome):
    if not nome:
        return "Exercicio sem nome"

    if nome in EXERCICIOS_PT:
        return EXERCICIOS_PT[nome]

    traducoes = {
        **{chave.lower(): valor for chave, valor in EXERCICIOS_PT.items()},
        **{chave.lower(): valor for chave, valor in TERMOS_EXERCICIO_PT.items()},
    }
    traduzido = nome.lower()

    for termo_en in sorted(traducoes, key=len, reverse=True):
        traduzido = traduzido.replace(termo_en, traducoes[termo_en])

    return traduzido[:1].upper() + traduzido[1:]


def _float_ou_none(valor):
    if not valor:
        return None

    try:
        return float(str(valor).replace(",", "."))
    except ValueError:
        return None


def _data_ou_none(valor):
    if not valor:
        return None

    try:
        return date.fromisoformat(valor)
    except ValueError:
        return None


def _texto_traduzido(exercicio):
    traducoes = exercicio.get("translations") or []

    for idioma in (10, 2):
        for traducao in traducoes:
            if traducao.get("language") == idioma and traducao.get("name"):
                return traducao

    return next((traducao for traducao in traducoes if traducao.get("name")), {})


def _normalizar_exercicio_api(exercicio):
    body_parts = exercicio.get("bodyParts") or []
    equipamentos = exercicio.get("equipments") or []
    musculos = exercicio.get("targetMuscles") or []
    secundarios = exercicio.get("secondaryMuscles") or []
    instrucoes = exercicio.get("instructions") or []
    grupo = body_parts[0] if body_parts else "Geral"

    return {
        "id": f"api-{exercicio.get('exerciseId')}",
        "api_id": exercicio.get("exerciseId"),
        "nome": _traduzir_nome_exercicio(exercicio.get("name")),
        "grupo_muscular": _traduzir(grupo, CATEGORIAS_PT),
        "equipamento": _traduzir(", ".join(equipamentos), CATEGORIAS_PT),
        "musculo_principal": _traduzir(", ".join(musculos), CATEGORIAS_PT),
        "musculos_secundarios": _traduzir(", ".join(secundarios), CATEGORIAS_PT),
        "imagem_url": "",
        "gif_url": exercicio.get("gifUrl") or "",
        "video_url": "",
        "descricao": "\n".join(instrucoes),
        "origem": "ExerciseDB",
    }


def _buscar_imagem_exercicio_api(exercicio_id):
    url = f"https://wger.de/api/v2/exerciseimage/?{urlencode({'exercise': exercicio_id, 'limit': 1})}"

    try:
        with urlopen(url, timeout=2) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))
    except Exception:
        return ""

    imagens = dados.get("results", [])

    if not imagens:
        return ""

    return imagens[0].get("image") or ""


def _buscar_exercicio_info_api(exercicio_id):
    url = f"https://wger.de/api/v2/exerciseinfo/{exercicio_id}/"

    try:
        with urlopen(url, timeout=2) as resposta:
            return json.loads(resposta.read().decode("utf-8"))
    except Exception:
        return None


def _exercicios_api_com_imagem(limite=12, busca="", varredura=30):
    url = f"https://wger.de/api/v2/exerciseimage/?{urlencode({'limit': varredura})}"
    exercicios = []
    vistos = set()
    busca_lower = busca.lower()

    try:
        with urlopen(url, timeout=8) as resposta:
            imagens = json.loads(resposta.read().decode("utf-8")).get("results", [])
    except Exception:
        return exercicios

    for imagem in imagens:
        exercicio_id = imagem.get("exercise")

        if not exercicio_id or exercicio_id in vistos:
            continue

        vistos.add(exercicio_id)
        info = _buscar_exercicio_info_api(exercicio_id)

        if not info:
            continue

        exercicio = _normalizar_exercicio_api(info)
        exercicio["imagem_url"] = exercicio["imagem_url"] or imagem.get("image") or ""

        if busca_lower and busca_lower not in exercicio["nome"].lower():
            continue

        exercicios.append(exercicio)

        if len(exercicios) >= limite:
            break

    return exercicios


def _exercicios_locais():
    return [
        {
            "id": str(exercicio.id),
            "api_id": "",
            "nome": exercicio.nome,
            "grupo_muscular": exercicio.grupo_muscular,
            "equipamento": exercicio.equipamento or "",
            "musculo_principal": exercicio.musculo_principal or "",
            "musculos_secundarios": exercicio.musculos_secundarios or "",
            "imagem_url": exercicio.imagem_url or "",
            "gif_url": exercicio.gif_url or "",
            "video_url": exercicio.video_url or "",
            "descricao": "",
            "origem": "Local",
        }
        for exercicio in Exercicio.query.order_by(Exercicio.nome.asc()).all()
    ]


def _exercicios_personalizados(busca=""):
    query = Exercicio.query.filter_by(personalizado=True)
    if busca:
        query = query.filter(Exercicio.nome.ilike(f"%{busca}%"))

    return [
        {
            "id": str(exercicio.id),
            "api_id": "",
            "nome": exercicio.nome,
            "grupo_muscular": exercicio.grupo_muscular,
            "equipamento": exercicio.equipamento or "",
            "musculo_principal": exercicio.musculo_principal or "",
            "musculos_secundarios": exercicio.musculos_secundarios or "",
            "imagem_url": exercicio.imagem_url or "",
            "gif_url": exercicio.gif_url or "",
            "video_url": exercicio.video_url or "",
            "descricao": "",
            "origem": "Personalizado",
        }
        for exercicio in query.order_by(Exercicio.nome.asc()).all()
    ]


@treino_bp.route("/")
def listar():
    treinos = Treino.query.order_by(Treino.id.desc()).all()
    avaliacoes = AvaliacaoFisica.query.order_by(AvaliacaoFisica.data_avaliacao.desc()).all()
    pdfs = PdfGerado.query.order_by(PdfGerado.criado_em.desc()).all()

    return render_template(
        "treinos.html",
        treinos=treinos,
        avaliacoes=avaliacoes,
        pdfs=pdfs,
    )


@treino_bp.route("/api/exercicios")
def api_exercicios():
    busca = request.args.get("busca", "").strip()
    try:
        limite = max(1, min(int(request.args.get("limite", "24")), 100))
    except (TypeError, ValueError):
        limite = 24
    params = {"limit": min(limite, 25)}
    url = f"https://oss.exercisedb.dev/api/v1/exercises?{urlencode(params)}"

    try:
        requisicao = Request(url, headers={"User-Agent": "SistemaAcademia/1.0"})
        with urlopen(requisicao, timeout=8) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))

        exercicios = [
            _normalizar_exercicio_api(exercicio)
            for exercicio in dados.get("data", [])
        ]

        if busca:
            busca_lower = busca.lower()
            exercicios = [
                exercicio for exercicio in exercicios
                if busca_lower in exercicio["nome"].lower()
                or busca_lower in exercicio["grupo_muscular"].lower()
                or busca_lower in exercicio["musculo_principal"].lower()
            ]

        if exercicios:
            return jsonify({"origem": "api", "exercicios": exercicios})
    except Exception:
        pass

    exercicios = _exercicios_locais()

    if busca:
        busca_lower = busca.lower()
        exercicios = [
            exercicio
            for exercicio in exercicios
            if busca_lower in exercicio["nome"].lower()
        ]

    return jsonify({"origem": "local", "exercicios": exercicios[:limite]})


@treino_bp.route("/api/exercicios-personalizados")
def api_exercicios_personalizados():
    busca = request.args.get("busca", "").strip()
    return jsonify({"origem": "personalizado", "exercicios": _exercicios_personalizados(busca)})


@treino_bp.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    alunos = Aluno.query.order_by(Aluno.nome.asc()).all()
    exercicios = Exercicio.query.order_by(Exercicio.nome.asc()).all()
    grupos = sorted({exercicio.grupo_muscular for exercicio in exercicios if exercicio.grupo_muscular})
    equipamentos = sorted({exercicio.equipamento for exercicio in exercicios if exercicio.equipamento})

    if request.method == "POST":
        try:
            frequencia = int(request.form.get("frequencia_semanal") or 3)
        except (TypeError, ValueError):
            flash("A frequencia de treino deve ser 3 ou 5 dias por semana.")
            return render_template("cadastrar_treino.html", alunos=alunos, exercicios=exercicios, grupos=grupos, equipamentos=equipamentos, objetivos=OBJETIVOS, dias_treino=DIAS_TREINO)

        if frequencia not in DIAS_TREINO:
            flash("A frequencia de treino deve ser 3 ou 5 dias por semana.")
            return render_template("cadastrar_treino.html", alunos=alunos, exercicios=exercicios, grupos=grupos, equipamentos=equipamentos, objetivos=OBJETIVOS, dias_treino=DIAS_TREINO)

        dias = DIAS_TREINO[frequencia]

        aluno_id = request.form.get("aluno_id", type=int)
        objetivo = request.form.get("objetivo", "").strip()
        tem_exercicio = any(
            any(nome.strip() for nome in request.form.getlist(f"nome_personalizado_{codigo}"))
            or any(valor.strip() for valor in request.form.getlist(f"exercicio_id_{codigo}"))
            for codigo, _ in dias
        )
        if not aluno_id or not db.session.get(Aluno, aluno_id) or not objetivo or not tem_exercicio:
            flash("Selecione um aluno valido, informe o objetivo e adicione pelo menos um exercicio.")
            return render_template("cadastrar_treino.html", alunos=alunos, exercicios=exercicios, grupos=grupos, equipamentos=equipamentos, objetivos=OBJETIVOS, dias_treino=DIAS_TREINO), 400

        treino = Treino(
            aluno_id=aluno_id,
            objetivo=objetivo,
            descricao=request.form.get("descricao", ""),
            frequencia_semanal=frequencia,
            data_criacao=date.today(),
            responsavel_tecnico=request.form.get("responsavel_tecnico"),
        )
        db.session.add(treino)
        db.session.flush()

        for ordem_dia, (codigo_dia, dia_nome) in enumerate(dias, start=1):
            treino_dia = TreinoDia(treino_id=treino.id, nome=dia_nome, ordem=ordem_dia)
            db.session.add(treino_dia)
            db.session.flush()

            exercicio_ids = request.form.getlist(f"exercicio_id_{codigo_dia}")
            nomes_personalizados = request.form.getlist(f"nome_personalizado_{codigo_dia}")
            series = request.form.getlist(f"series_{codigo_dia}")
            repeticoes = request.form.getlist(f"repeticoes_{codigo_dia}")
            cargas = request.form.getlist(f"carga_{codigo_dia}")
            descansos = request.form.getlist(f"descanso_{codigo_dia}")
            observacoes = request.form.getlist(f"observacoes_{codigo_dia}")
            grupos_api = request.form.getlist(f"grupo_muscular_{codigo_dia}")
            equipamentos_api = request.form.getlist(f"equipamento_{codigo_dia}")
            imagens_api = request.form.getlist(f"imagem_url_{codigo_dia}")
            gifs_api = request.form.getlist(f"gif_url_{codigo_dia}")
            videos_api = request.form.getlist(f"video_url_{codigo_dia}")

            total = max(len(exercicio_ids), len(nomes_personalizados))

            for indice in range(total):
                exercicio = None
                exercicio_id = exercicio_ids[indice] if indice < len(exercicio_ids) else ""
                nome_personalizado = (
                    nomes_personalizados[indice].strip()
                    if indice < len(nomes_personalizados)
                    else ""
                )

                if exercicio_id:
                    exercicio = Exercicio.query.get(exercicio_id)

                nome = exercicio.nome if exercicio else nome_personalizado

                if not nome:
                    continue

                db.session.add(TreinoExercicio(
                    treino_dia_id=treino_dia.id,
                    exercicio_id=exercicio.id if exercicio else None,
                    nome=nome,
                    grupo_muscular=(
                        exercicio.grupo_muscular
                        if exercicio
                        else grupos_api[indice] if indice < len(grupos_api) and grupos_api[indice]
                        else "Personalizado"
                    ),
                    equipamento=(
                        exercicio.equipamento
                        if exercicio
                        else equipamentos_api[indice] if indice < len(equipamentos_api)
                        else ""
                    ),
                    imagem_url=(
                        exercicio.imagem_url
                        if exercicio
                        else imagens_api[indice] if indice < len(imagens_api)
                        else ""
                    ),
                    gif_url=(
                        exercicio.gif_url
                        if exercicio
                        else gifs_api[indice] if indice < len(gifs_api)
                        else ""
                    ),
                    video_url=(
                        exercicio.video_url
                        if exercicio
                        else videos_api[indice] if indice < len(videos_api)
                        else ""
                    ),
                    series=series[indice] if indice < len(series) and series[indice] else "3",
                    repeticoes=repeticoes[indice] if indice < len(repeticoes) and repeticoes[indice] else "12",
                    carga=cargas[indice] if indice < len(cargas) else "",
                    descanso=descansos[indice] if indice < len(descansos) else "",
                    observacoes=observacoes[indice] if indice < len(observacoes) else "",
                    ordem=indice + 1,
                ))

        if not any(dia.exercicios for dia in treino.dias):
            db.session.rollback()
            flash("Adicione pelo menos um exercicio valido ao treino.")
            return render_template("cadastrar_treino.html", alunos=alunos, exercicios=exercicios, grupos=grupos, equipamentos=equipamentos, objetivos=OBJETIVOS, dias_treino=DIAS_TREINO), 400

        db.session.commit()
        return redirect(url_for("treino.listar"))

    return render_template(
        "cadastrar_treino.html",
        alunos=alunos,
        exercicios=exercicios,
        grupos=grupos,
        equipamentos=equipamentos,
        objetivos=OBJETIVOS,
        dias_treino=DIAS_TREINO,
    )


@treino_bp.route("/exercicio-personalizado", methods=["POST"])
def exercicio_personalizado():
    resposta_json = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    def erro_cadastro(mensagem):
        if resposta_json:
            return jsonify({"erro": mensagem}), 400
        flash(mensagem)
        return redirect(url_for("treino.cadastrar"))

    nome = request.form.get("nome", "").strip() or "Exercicio personalizado"
    grupo = request.form.get("grupo_muscular", "").strip() or "Geral"

    imagem_url = _salvar_midia(request.files.get("imagem_arquivo"), EXTENSOES_IMAGEM)
    video_url = _salvar_midia(request.files.get("video_arquivo"), EXTENSOES_VIDEO)

    if request.files.get("imagem_arquivo") and not imagem_url:
        return erro_cadastro("A imagem deve estar em JPG, JPEG, PNG ou WEBP.")

    if request.files.get("video_arquivo") and not video_url:
        return erro_cadastro("O video deve estar em MP4, WEBM, MOV ou AVI.")

    exercicio = Exercicio(
        nome=nome,
        grupo_muscular=grupo,
        equipamento=request.form.get("equipamento"),
        musculo_principal=request.form.get("musculo_principal"),
        musculos_secundarios=request.form.get("musculos_secundarios"),
        imagem_url=imagem_url or request.form.get("imagem_url"),
        gif_url=request.form.get("gif_url"),
        video_url=video_url or request.form.get("video_url"),
        personalizado=True,
    )
    db.session.add(exercicio)
    db.session.commit()
    if resposta_json:
        return jsonify({"exercicios": _exercicios_personalizados()}), 201
    return redirect(url_for("treino.cadastrar"))


@treino_bp.route("/midia/<path:nome>")
def midia_exercicio(nome):
    pasta = os.path.join(current_app.instance_path, "uploads", "exercicios")
    return send_from_directory(pasta, nome)


@treino_bp.route("/avaliacao/nova", methods=["GET", "POST"])
def nova_avaliacao():
    alunos = Aluno.query.order_by(Aluno.nome.asc()).all()

    if request.method == "POST":
        peso = _float_ou_none(request.form.get("peso"))
        altura = _float_ou_none(request.form.get("altura"))
        imc = round(peso / (altura * altura), 2) if peso and altura and altura > 0 else None

        avaliacao = AvaliacaoFisica(
            aluno_id=request.form["aluno_id"],
            nome=request.form["nome"],
            data_nascimento=_data_ou_none(request.form.get("data_nascimento")),
            responsavel_tecnico=request.form.get("responsavel_tecnico"),
            data_inicio=_data_ou_none(request.form.get("data_inicio")),
            objetivo=request.form.get("objetivo"),
            observacoes=request.form.get("observacoes"),
            data_avaliacao=_data_ou_none(request.form.get("data_avaliacao")) or date.today(),
            peso=peso,
            altura=altura,
            imc=imc,
            braco=_float_ou_none(request.form.get("braco")),
            antebraco=_float_ou_none(request.form.get("antebraco")),
            panturrilha=_float_ou_none(request.form.get("panturrilha")),
            perna=_float_ou_none(request.form.get("perna")),
            torax=_float_ou_none(request.form.get("torax")),
            abdomen=_float_ou_none(request.form.get("abdomen")),
            cintura=_float_ou_none(request.form.get("cintura")),
            quadril=_float_ou_none(request.form.get("quadril")),
        )
        db.session.add(avaliacao)
        db.session.commit()
        return redirect(url_for("treino.listar"))

    return render_template(
        "cadastrar_avaliacao.html",
        alunos=alunos,
        objetivos=OBJETIVOS,
        data_atual=date.today().isoformat(),
    )


@treino_bp.route("/pdf/<int:id>")
def gerar_pdf(id):
    treino = Treino.query.get_or_404(id)
    avaliacao = AvaliacaoFisica.query.filter_by(aluno_id=treino.aluno_id).order_by(
        AvaliacaoFisica.data_avaliacao.desc(),
        AvaliacaoFisica.id.desc(),
    ).first()
    caminho = gerar_pdf_completo(treino, avaliacao)

    pdf = PdfGerado(
        aluno_id=treino.aluno_id,
        treino_id=treino.id,
        avaliacao_id=avaliacao.id if avaliacao else None,
        caminho=caminho,
    )
    db.session.add(pdf)
    db.session.commit()

    return send_file(caminho, as_attachment=True, download_name=os.path.basename(caminho))


@treino_bp.route("/avaliacao/<int:id>/pdf")
def gerar_pdf_avaliacao_rota(id):
    avaliacao = AvaliacaoFisica.query.get_or_404(id)
    caminho = gerar_pdf_avaliacao(avaliacao)
    pdf = PdfGerado(
        aluno_id=avaliacao.aluno_id,
        avaliacao_id=avaliacao.id,
        caminho=caminho,
    )
    db.session.add(pdf)
    db.session.commit()
    return send_file(caminho, as_attachment=True, download_name=os.path.basename(caminho))


@treino_bp.route("/avaliacao/<int:id>/excluir", methods=["POST"])
def excluir_avaliacao(id):
    avaliacao = AvaliacaoFisica.query.get_or_404(id)
    pdfs = PdfGerado.query.filter_by(avaliacao_id=avaliacao.id).all()
    pasta_pdf = os.path.abspath(os.path.join(current_app.instance_path, "pdfs"))

    for pdf in pdfs:
        caminho_pdf = os.path.abspath(pdf.caminho)
        if os.path.commonpath([pasta_pdf, caminho_pdf]) == pasta_pdf and os.path.isfile(caminho_pdf):
            try:
                os.remove(caminho_pdf)
            except PermissionError:
                pass
        db.session.delete(pdf)

    db.session.delete(avaliacao)
    db.session.commit()
    flash("Avaliacao excluida com sucesso.")
    return redirect(url_for("treino.listar"))


@treino_bp.route("/pdf-gerado/<int:id>")
def baixar_pdf(id):
    pdf = PdfGerado.query.get_or_404(id)
    return send_file(pdf.caminho, as_attachment=True)


@treino_bp.route("/pdf-gerado/<int:id>/excluir", methods=["POST"])
def excluir_pdf(id):
    pdf = PdfGerado.query.get_or_404(id)
    pasta_pdf = os.path.abspath(os.path.join(current_app.instance_path, "pdfs"))
    caminho_pdf = os.path.abspath(pdf.caminho)

    arquivo_excluido = True
    if os.path.commonpath([pasta_pdf, caminho_pdf]) == pasta_pdf and os.path.isfile(caminho_pdf):
        try:
            os.remove(caminho_pdf)
        except PermissionError:
            arquivo_excluido = False

    db.session.delete(pdf)
    db.session.commit()
    flash(
        "PDF excluido com sucesso."
        if arquivo_excluido
        else "Registro do PDF excluido. O arquivo esta aberto e sera necessario fecha-lo para remove-lo."
    )
    return redirect(url_for("treino.listar"))


@treino_bp.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    treino = Treino.query.get_or_404(id)
    db.session.delete(treino)
    db.session.commit()
    return redirect(url_for("treino.listar"))
