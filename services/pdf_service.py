import io
import os
import re
import unicodedata
from datetime import date
from urllib.request import Request, urlopen

from flask import current_app
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _baixar_imagem(url):
    if not url or not url.startswith(("http://", "https://")):
        if not url.startswith("/treinos/midia/"):
            return None

        nome = os.path.basename(url)
        caminho = os.path.join(current_app.instance_path, "uploads", "exercicios", nome)
        try:
            with open(caminho, "rb") as arquivo:
                conteudo = arquivo.read(4 * 1024 * 1024)
        except OSError:
            return None

        try:
            imagem = PILImage.open(io.BytesIO(conteudo)).convert("RGB")
            imagem.thumbnail((240, 180))
            buffer = io.BytesIO()
            imagem.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer
        except Exception:
            return None

    try:
        requisicao = Request(url, headers={"User-Agent": "SistemaAcademia/1.0"})
        with urlopen(requisicao, timeout=5) as resposta:
            conteudo = resposta.read(4 * 1024 * 1024)

        imagem = PILImage.open(io.BytesIO(conteudo))
        imagem.seek(0)
        imagem = imagem.convert("RGB")
        imagem.thumbnail((240, 180))
        buffer = io.BytesIO()
        imagem.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer
    except Exception:
        return None


def _paragrafo(texto, estilo):
    return Paragraph(str(texto or "-").replace("&", "&amp;"), estilo)


def _nome_arquivo(valor):
    valor = unicodedata.normalize("NFKD", str(valor or "aluno"))
    valor = valor.encode("ascii", "ignore").decode("ascii").lower()
    valor = re.sub(r"[^a-z0-9]+", "_", valor).strip("_")
    return valor or "aluno"


TERMOS_EXERCICIO_PT = {
    "barbell": "barra", "dumbbell": "halter", "cable": "cabo",
    "machine": "maquina", "body weight": "peso corporal",
    "bench press": "supino", "shoulder press": "desenvolvimento de ombros",
    "leg press": "leg press", "squat": "agachamento", "deadlift": "levantamento terra",
    "lunge": "avanco", "curl": "rosca", "extension": "extensao",
    "pulldown": "puxada", "pull up": "barra fixa", "push up": "flexao",
    "row": "remada", "raise": "elevacao", "plank": "prancha",
    "crunch": "abdominal", "chest": "peito", "back": "costas",
    "shoulder": "ombro", "leg": "perna", "standing": "em pe",
    "seated": "sentado", "incline": "inclinado", "decline": "declinado",
    "wide grip": "pegada aberta", "narrow grip": "pegada fechada",
}


def _nome_exercicio_pt(nome):
    resultado = str(nome or "Exercicio sem nome")
    for termo, traducao in sorted(TERMOS_EXERCICIO_PT.items(), key=lambda item: len(item[0]), reverse=True):
        resultado = resultado.replace(termo, traducao).replace(termo.title(), traducao)
    return resultado[:1].upper() + resultado[1:]


def _tabela_avaliacao(avaliacao, estilos):
    texto = estilos["BodyText"]
    dados = [
        ["Aluno", avaliacao.aluno.nome],
        ["Nome na avaliacao", avaliacao.nome],
        ["Data da avaliacao", avaliacao.data_avaliacao],
        ["Nascimento", avaliacao.data_nascimento or "-"],
        ["Inicio", avaliacao.data_inicio or "-"],
        ["Objetivo", avaliacao.objetivo or "-"],
        ["Responsavel tecnico", avaliacao.responsavel_tecnico or "-"],
        ["Peso / altura", f"{avaliacao.peso or '-'} kg / {avaliacao.altura or '-'} m"],
        ["IMC", avaliacao.imc or "-"],
        ["Braco / antebraco", f"{avaliacao.braco or '-'} cm / {avaliacao.antebraco or '-'} cm"],
        ["Torax / abdomen", f"{avaliacao.torax or '-'} cm / {avaliacao.abdomen or '-'} cm"],
        ["Cintura / quadril", f"{avaliacao.cintura or '-'} cm / {avaliacao.quadril or '-'} cm"],
        ["Perna / panturrilha", f"{avaliacao.perna or '-'} cm / {avaliacao.panturrilha or '-'} cm"],
        ["Observacoes", avaliacao.observacoes or "-"],
    ]
    tabela = Table(dados, colWidths=[4.5 * cm, 12.5 * cm])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8f0f7")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c5d1")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    return tabela


def _cabecalho_academia(canvas, documento):
    caminho_logo = os.path.join(current_app.static_folder, "img", "logo_fit_trainer.png")
    tamanho = 3.2 * cm
    largura, altura = documento.pagesize
    canvas.saveState()
    canvas.drawImage(
        caminho_logo,
        (largura - tamanho) / 2,
        altura - tamanho,
        width=tamanho,
        height=tamanho,
        preserveAspectRatio=True,
        mask="auto",
    )
    canvas.restoreState()


def gerar_pdf_avaliacao(avaliacao):
    pasta = os.path.join(current_app.instance_path, "pdfs")
    os.makedirs(pasta, exist_ok=True)
    aluno = _nome_arquivo(avaliacao.aluno.nome)
    caminho = os.path.join(pasta, f"avaliacao_{aluno}_{avaliacao.id}_{date.today().isoformat()}.pdf")
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle("TituloAvaliacao", parent=estilos["Title"], alignment=TA_CENTER, spaceAfter=16)
    documento = SimpleDocTemplate(caminho, pagesize=A4, rightMargin=1.5 * cm, leftMargin=1.5 * cm, topMargin=2.5 * cm, bottomMargin=1.5 * cm)
    documento.build(
        [_paragrafo("AVALIACAO FISICA DO ALUNO", titulo), _tabela_avaliacao(avaliacao, estilos)],
        onFirstPage=_cabecalho_academia,
        onLaterPages=_cabecalho_academia,
    )
    return caminho


def gerar_pdf_completo(treino, avaliacao=None):
    pasta = os.path.join(current_app.instance_path, "pdfs")
    os.makedirs(pasta, exist_ok=True)
    aluno = _nome_arquivo(treino.aluno.nome)
    caminho = os.path.join(pasta, f"treino_{aluno}_{treino.id}_{date.today().isoformat()}.pdf")

    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle("Titulo", parent=estilos["Title"], alignment=TA_CENTER, spaceAfter=16)
    subtitulo = ParagraphStyle("Subtitulo", parent=estilos["Heading2"], spaceBefore=10, spaceAfter=8)
    texto = ParagraphStyle("Texto", parent=estilos["BodyText"], fontSize=9, leading=12)
    pequeno = ParagraphStyle("Pequeno", parent=texto, fontSize=8, textColor=colors.HexColor("#555555"))

    documento = SimpleDocTemplate(
        caminho,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=1.5 * cm,
    )
    elementos = [_paragrafo("AVALIACAO FISICA", titulo)]
    dados_avaliacao = [
        ["Aluno", treino.aluno.nome],
        ["Objetivo", treino.objetivo],
        ["Frequencia", f"{treino.frequencia_semanal} dias por semana"],
        ["Responsavel tecnico", treino.responsavel_tecnico or "Nao informado"],
    ]

    if avaliacao:
        dados_avaliacao.extend([
            ["Data da avaliacao", avaliacao.data_avaliacao],
            ["Peso / altura", f"{avaliacao.peso or '-'} kg / {avaliacao.altura or '-'} m"],
            ["IMC", avaliacao.imc or "-"],
            ["Medidas", f"Braco {avaliacao.braco or '-'} cm | Antebraco {avaliacao.antebraco or '-'} cm | Torax {avaliacao.torax or '-'} cm"],
            ["Medidas inferiores", f"Abdomen {avaliacao.abdomen or '-'} cm | Cintura {avaliacao.cintura or '-'} cm | Quadril {avaliacao.quadril or '-'} cm | Perna {avaliacao.perna or '-'} cm | Panturrilha {avaliacao.panturrilha or '-'} cm"],
            ["Observacoes", avaliacao.observacoes or "-"],
        ])
    else:
        dados_avaliacao.append(["Avaliacao", "Nenhuma avaliacao fisica vinculada."])

    tabela_avaliacao = Table(dados_avaliacao, colWidths=[4 * cm, 13 * cm])
    tabela_avaliacao.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8f0f7")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c5d1")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    elementos.extend([tabela_avaliacao, PageBreak(), _paragrafo("PLANILHA DE TREINO", titulo)])

    for dia in treino.dias:
        elementos.append(_paragrafo(dia.nome.upper(), subtitulo))
        for exercicio in dia.exercicios:
            imagem_buffer = _baixar_imagem(exercicio.gif_url or exercicio.imagem_url)
            imagem = Image(imagem_buffer, width=4.8 * cm, height=3.6 * cm) if imagem_buffer else _paragrafo("Sem imagem", pequeno)
            detalhes = [
                _paragrafo(f"<b>{_nome_exercicio_pt(exercicio.nome)}</b>", texto),
                _paragrafo(f"{exercicio.grupo_muscular or 'Geral'} | {exercicio.equipamento or 'Sem equipamento'}", pequeno),
                _paragrafo(f"Series: {exercicio.series or '-'} | Repeticoes: {exercicio.repeticoes or '-'}", texto),
                _paragrafo(f"Carga: {exercicio.carga or '-'} | Descanso: {exercicio.descanso or '-'}", texto),
            ]
            tabela_exercicio = Table([[imagem, detalhes]], colWidths=[5.2 * cm, 11.8 * cm])
            tabela_exercicio.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d2da")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            elementos.extend([tabela_exercicio, Spacer(1, 8)])

    elementos.append(_paragrafo("Imagens: ExerciseDB by AscendAPI", pequeno))
    documento.build(elementos, onFirstPage=_cabecalho_academia, onLaterPages=_cabecalho_academia)
    return caminho
