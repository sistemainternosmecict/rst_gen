from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter
from datetime import datetime
import os, secrets

class Pdf_service:
    def construir_documento(self, dados_doc:dict):
        data_atual = datetime.now().strftime("%d-%m-%Y")
        template_path = os.getenv("TEMPLATE_PATH", "")
        pdf_output_path = f'rst/RST_{data_atual}_{self._gerar_sufixo_aleatorio()}.pdf'
        self.dividir_dados(dados_doc)
        self.construir_pagina(template_path, pdf_output_path)

    def construir_pagina(self, template_path:str, output_path:str):
        dados_temporarios = "temp_pdf_data.pdf"
        self.width, self.height = A4

        self.cv = canvas.Canvas(dados_temporarios, pagesize=A4)
        self.cv.showPage()
        self.cv.save()

        reader_template = PdfReader(template_path)
        reader_temporario = PdfReader(dados_temporarios)
        writer = PdfWriter()

        pagina_template = reader_template.pages[0]
        pagina_temporaria = reader_temporario.pages[0]

        pagina_template.merge_page(pagina_temporaria)
        writer.add_page(pagina_template)

        with open(output_path, "wb") as f:
            writer.write(f)

        if os.path.exists(dados_temporarios):
            os.remove(dados_temporarios)

    def dividir_dados(self, dados_doc:dict):
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
            "rst_data_chamado":dados_doc.rst_data_chamado
        }

        self.dados_tecnico = {
            "rst_nome_tecnico": dados_doc.rst_nome_tecnico,
            "rst_data_atendimento": dados_doc.rst_data_atendimento
        }

        self.causas = dados_doc.rst_causas
        self.procedimentos = dados_doc.rst_procedimentos
        self.observacoes = {
            "rst_observacoes":dados_doc.rst_observacoes,
            "rst_numero_oficio": dados_doc.rst_numero_oficio
        }

        self.dados_assinaturas = {
            "rst_assinatura_solicitante": dados_doc.rst_assinatura_solicitante,
            "rst_assinatura_tecnico": dados_doc.rst_assinatura_tecnico
        }

        print(self.dados_unidade, self.dados_solicitante, self.dados_tecnico, self.causas, self.procedimentos, self.observacoes, self.dados_assinaturas)

    def _gerar_sufixo_aleatorio(bytes_aleatorios: int = 8) -> str:
        return secrets.token_urlsafe(9).lower()
