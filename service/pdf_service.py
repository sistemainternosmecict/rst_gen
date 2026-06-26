from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter
from datetime import datetime
import os, secrets

class Pdf_service:
    def construir_documento(self, dados_doc:dict):
        data_atual = datetime.now().strftime("%d-%m-%Y")
        template_path = os.getenv("TEMPLATE_PATH", "")
        dados_divididos = self.dividir_dados(dados_doc)
        #self.pdf_output_path = f'rst/RST_{data_atual}_{self._gerar_sufixo_aleatorio()}.pdf'
        self.pdf_output_path = f'rst/RST.pdf'
        self.construir_pagina(template_path, dados_divididos)
        self.salvar_pdf()

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
            "rst_assinatura_tecnico": dados_doc.rst_assinatura_tecnico
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
        self.cv.drawString(120, 681, dados_unidade["rst_unidade_escolar"])
        self.cv.drawString(70, 660, dados_unidade["rst_bairro"])
        self.cv.drawString(370, 660, dados_unidade["rst_distrito"])

    def escrever_dados_solicitante(self, dados_solicitante:dict):
        self.cv.drawString(140, 612, dados_solicitante["rst_nome_solicitante"])
        self.cv.drawString(70, 590, dados_solicitante["rst_cargo_solicitante"])
        self.cv.drawString(480, 590, dados_solicitante["rst_matricula_solicitante"])

    def construir_pagina(self, template_path:str, dados_divididos:list):
        self.dados_temporarios = "temp_pdf_data.pdf"
        self.width, self.height = A4

        self.cv = canvas.Canvas(self.dados_temporarios, pagesize=A4)

        self.escrever_informacoes_unidade(dados_divididos[0])
        self.escrever_dados_solicitante(dados_divididos[1])

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

    def _gerar_sufixo_aleatorio(bytes_aleatorios: int = 8) -> str:
        return secrets.token_urlsafe(9).lower()
