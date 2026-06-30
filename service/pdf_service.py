from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter
from datetime import datetime
from PIL import Image, ImageOps
import os, secrets, qrcode, io, base64

MAPA_COORDENADAS_CAUSAS = {
    "Configuração de sistema": (39, 488),
    "Entrega de equipamentos": (39, 473),
    "Substituição de equipamentos": (39, 458),
    "Garantia de equipamentos": (39, 443),
    "Vistoria de equipamentos": (39, 428),
    "Remoção de equipamentos": (230, 488),
    "Rede e Internet": (230, 473),
    "Backup de arquivos": (230, 458),
    "Avaliação de Carência": (230, 443),
    "Outros": (230, 428),
}

class Pdf_service:
    def construir_documento(self, dados_doc:dict, rst_doc_hash:str):
        data_atual = datetime.now().strftime("%d%m%Y")
        template_path = os.getenv("TEMPLATE_PATH", "")
        dados_divididos = self.dividir_dados(dados_doc)
        self.pdf_output_path = f'{os.getenv("LOCAL_PDF_DIR", "")}/RST{data_atual}_{self._gerar_sufixo_aleatorio()}.pdf'
        url_para_validacao = self._criar_link_para_verificacao_validade(rst_doc_hash)
        self.construir_pagina(template_path, dados_divididos, url_para_validacao)
        self.salvar_pdf()
        return self.pdf_output_path

    def dividir_dados(self, dados_doc:dict)->list:
        self.dados_unidade = {
            "rst_unidade_escolar": dados_doc.rst_unidade_escolar,
            "rst_email_unidade": dados_doc.rst_email_unidade,
            "rst_bairro": dados_doc.rst_bairro,
            "rst_distrito": dados_doc.rst_distrito,
        }

        self.dados_solicitante = {
            "rst_nome_solicitante": dados_doc.rst_nome_solicitante,
            "rst_cargo_solicitante": dados_doc.rst_cargo_solicitante,
            "rst_matricula_solicitante":dados_doc.rst_matricula_solicitante,
        }

        self.dados_tecnico = {
            "rst_nome_tecnico": dados_doc.rst_nome_tecnico,
            "rst_data_atendimento": dados_doc.rst_data_atendimento
        }

        self.causas = dados_doc.rst_causas
        self.procedimentos = dados_doc.rst_procedimentos
        self.observacoes = {
            "rst_observacoes":dados_doc.rst_observacoes,
            "rst_numero_oficio": dados_doc.rst_numero_oficio,
            "rst_data_chamado":dados_doc.rst_data_chamado,
            "rst_unidade_escolar": dados_doc.rst_unidade_escolar,
        }

        self.dados_assinaturas = {
            "rst_assinatura_solicitante": dados_doc.rst_assinatura_solicitante,
            "rst_assinatura_tecnico": dados_doc.rst_assinatura_tecnico,
            "rst_nome_solicitante": dados_doc.rst_nome_solicitante,
            "rst_cargo_solicitante": dados_doc.rst_cargo_solicitante,
            "rst_matricula_solicitante":dados_doc.rst_matricula_solicitante,
            "rst_nome_tecnico": dados_doc.rst_nome_tecnico
        }

        return [
            self.dados_unidade,
            self.dados_solicitante,
            self.dados_tecnico,
            self.causas,
            self.procedimentos,
            self.observacoes,
            self.dados_assinaturas
        ]

    def escrever_informacoes_unidade(self, dados_unidade:dict):
        self.cv.drawString(120, 682, dados_unidade["rst_unidade_escolar"])
        self.cv.drawString(70, 660, dados_unidade["rst_bairro"])
        self.cv.drawString(370, 660, dados_unidade["rst_distrito"])

    def escrever_dados_solicitante(self, dados_solicitante:dict):
        self.cv.drawString(140, 612, dados_solicitante["rst_nome_solicitante"])
        self.cv.drawString(70, 590, dados_solicitante["rst_cargo_solicitante"])
        self.cv.drawString(480, 590, dados_solicitante["rst_matricula_solicitante"])

    def escrever_dados_tecnico(self, dados_tecnico:dict):
        self.cv.drawString(120, 542, dados_tecnico["rst_nome_tecnico"])
        self.cv.drawString(470, 542, dados_tecnico["rst_data_atendimento"])

    def escrever_causas_problemas_tecnicos_relacionados(self, causas:list):
        self.cv.setFont("Helvetica-Bold", 12)
        for causa in causas:
            if causa in MAPA_COORDENADAS_CAUSAS:
                x, y = MAPA_COORDENADAS_CAUSAS[causa]
                self.cv.drawCentredString(x, y, "X")

    def escrever_procedimentos_realizados(self, procedimentos:str):
        self._escrever_paragrafo_contido(procedimentos)

    def escrever_observacoes(self, observacoes:dict):
        self.cv.setFont("Helvetica", 9)
        self._escrever_paragrafo_contido(observacoes["rst_observacoes"], 240, 220)
        self.cv.setFont("Helvetica-Bold", 7)
        self.cv.drawString(30, 260, f"RST referente ao ofício {observacoes["rst_numero_oficio"]} da unidade {observacoes["rst_unidade_escolar"]} recebido dia {observacoes["rst_data_chamado"]}")

    def escrever_assinaturas(self, dados_assinaturas:dict):
        largura_assinatura = 5 * cm
        altura_assinatura = 4 * cm
        posicao_y = 4.2 * cm

        posicao_x_esquerda = 3.0 * cm
        posicao_x_direita = 21.0 * cm - 3.0 * cm - largura_assinatura # 21cm é a largura total do A4

        self.cv.drawCentredString(posicao_x_direita + (largura_assinatura / 2), altura_assinatura + 50, dados_assinaturas["rst_nome_solicitante"])
        self.cv.drawCentredString(posicao_x_direita + (largura_assinatura / 2), altura_assinatura + 40, dados_assinaturas["rst_cargo_solicitante"])
        self.cv.drawCentredString(posicao_x_direita + (largura_assinatura / 2), altura_assinatura + 30, dados_assinaturas["rst_matricula_solicitante"])
        self.cv.drawCentredString(posicao_x_esquerda + (largura_assinatura / 2), altura_assinatura + 50, dados_assinaturas["rst_nome_tecnico"])

        def transformar_imagem_em_azul(base64_str):
            if "," in base64_str:
                base64_str = base64_str.split(",")[1]

            bytes_img = base64.b64decode(base64_str)
            img_pil = Image.open(io.BytesIO(bytes_img)).convert("RGBA")

            r, g, b, a = img_pil.split()
            azul_solido = Image.new("RGBA", img_pil.size, (0, 0, 255, 255))

            cinza = ImageOps.grayscale(img_pil)
            mascara_traço = ImageOps.invert(cinza)
            img_azul = Image.composite(azul_solido, img_pil, mascara_traço)
            img_final = Image.merge("RGBA", (img_azul.split()[0], img_azul.split()[1], img_azul.split()[2], a))

            buffer_final = io.BytesIO()
            img_final.save(buffer_final, format="PNG")
            buffer_final.seek(0)

            return ImageReader(buffer_final)

        base64_solicitante = dados_assinaturas.get("rst_assinatura_solicitante")
        if base64_solicitante:
            try:
                img_solicitante = transformar_imagem_em_azul(base64_solicitante) 
                self.cv.drawImage(
                    img_solicitante,
                    posicao_x_direita,
                    posicao_y,
                    width=largura_assinatura,
                    height=altura_assinatura,
                    mask='auto'
                )
            except Exception as e:
                print(f"Erro ao processar assinatura do solicitante: {e}")

        base64_tecnico = dados_assinaturas.get("rst_assinatura_tecnico")
        if base64_tecnico:
            try:
                img_tecnico = transformar_imagem_em_azul(base64_tecnico) 
                self.cv.drawImage(
                    img_tecnico,
                    posicao_x_esquerda,
                    posicao_y,
                    width=largura_assinatura,
                    height=altura_assinatura,
                    mask='auto'
            )
            except Exception as e:
                print(f"Erro ao processar assinatura do técnico: {e}")

    def escrever_link_para_validacao(self, url_para_validacao:str):
        self.cv.setFont("Helvetica", 9)
        instrucoes = f"Leia o qr code ou acesse o seguinte link para validar o documento."
        x = 24
        y = 2.8 * cm
        self.cv.drawString(x, y, instrucoes)
        self.cv.drawString(x, y - 10, url_para_validacao)

    def construir_pagina(self, template_path:str, dados_divididos:list, url_para_validacao:str):
        self.dados_temporarios = "temp_pdf_data.pdf"
        self.width, self.height = A4

        self.cv = canvas.Canvas(self.dados_temporarios, pagesize=A4)

        self.escrever_informacoes_unidade(dados_divididos[0])
        self.escrever_dados_solicitante(dados_divididos[1])
        self.escrever_dados_tecnico(dados_divididos[2])
        self.escrever_causas_problemas_tecnicos_relacionados(dados_divididos[3])
        self.escrever_procedimentos_realizados(dados_divididos[4])
        self.escrever_observacoes(dados_divididos[5])
        self.escrever_assinaturas(dados_divididos[6])
        self.escrever_link_para_validacao(url_para_validacao)
        self._criar_qr_code(url_para_validacao)

        self.cv.showPage()
        self.cv.save()

        reader_template = PdfReader(template_path)
        reader_temporario = PdfReader(self.dados_temporarios)
        self.writer = PdfWriter()

        pagina_template = reader_template.pages[0]
        pagina_temporaria = reader_temporario.pages[0]
        pagina_template.merge_page(pagina_temporaria)

        self.writer.add_page(pagina_template)

    def salvar_pdf(self):
        with open(self.pdf_output_path, "wb") as f:
            self.writer.write(f)

        if os.path.exists(self.dados_temporarios):
            os.remove(self.dados_temporarios)

    def _escrever_paragrafo_contido(self, texto: str, y:int = 315, limite:int = 330):
        paragrafo_x = 30
        paragrafo_y = y
        paragrafo_largura = 535
        paragrafo_altura = 70
        paragrafo_tamanho_fonte = 10
        paragrafo_espacamento_linha = 16
        paragrafo_limite_caracteres = limite
        paragrafo_debug = False

        if len(texto) > paragrafo_limite_caracteres:
            texto = texto[:paragrafo_limite_caracteres] + "..."

        if paragrafo_debug:
            self.cv.saveState()
            self.cv.setStrokeColorRGB(1, 0, 0)  # Vermelho para debug
            self.cv.setLineWidth(0.5)
            self.cv.rect(paragrafo_x, paragrafo_y, paragrafo_largura, paragrafo_altura, stroke=1, fill=0)
            self.cv.restoreState()

        estilo_customizado = ParagraphStyle(
            name="EstiloDinamico",
            fontName="Helvetica",
            fontSize=paragrafo_tamanho_fonte,
            leading=paragrafo_espacamento_linha,  # Controla o espaçamento vertical
            alignment=TA_LEFT           # Alinhamento do texto
        )

        p = Paragraph(texto, estilo_customizado)

        frame = Frame(
            paragrafo_x, paragrafo_y, paragrafo_largura, paragrafo_altura,
            leftPadding=2, rightPadding=2, topPadding=2, bottomPadding=2,
            id='frame_paragrafo'
        )

        frame.addFromList([p], self.cv)
    
    def _criar_qr_code(self, url_validacao:str):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=1,
        )
        qr.add_data(url_validacao)
        qr.make(fit=True)

        img_qr = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img_qr.save(buffer, format="PNG")
        buffer.seek(0)

        tamanho_qr = 2.2 * cm

        reader = ImageReader(buffer)
        self.cv.drawImage(reader, (self.width / 2) - (tamanho_qr / 2), 2, width=tamanho_qr, height=tamanho_qr)

    def _criar_link_para_verificacao_validade(self, rst_doc_hash:str):
        return f"{os.getenv("URL_BASE")}/validar_documento_por_hash/{rst_doc_hash}"

    def _gerar_sufixo_aleatorio(self, bytes_aleatorios: int = 8) -> str:
        return secrets.token_urlsafe(9).lower()
