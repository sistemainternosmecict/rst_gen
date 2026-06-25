from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter
import os

class Pdf_service:
    def construir_documento(self, dados_doc:dict):
        print(dados_doc)
        template_path = os.getenv("TEMPLATE_PATH", "")
        pdf_output_path = f'RST_{dados_doc.rst_task_id}.pdf'
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

        print(f"PDF gerado com sucesso: {output_path}")

    def construir_cabecalho(self):
        pass
