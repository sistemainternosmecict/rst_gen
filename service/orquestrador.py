from service.pdf_service import Pdf_service
class Orquestrador:
    def gerar_documento_assinado(self, dados_doc:dict):
        pdfS = Pdf_service()
        pdfS.construir_documento(dados_doc)
