from service.pdf_service import Pdf_service
#from service.rst_service import Rst_service
from service.ferramentas import Ferramentas

class Orquestrador:
    def gerar_documento_assinado(self, dados_doc:dict):
        ferramentas = Ferramentas()
        rst_doc_hash = ferramentas.calcular_hash_documento(dados_doc)
        pdfS = Pdf_service()
        pdfS.construir_documento(dados_doc, rst_doc_hash)

        #rstS = Rst_service()
        #rst_doc_hash = rstS.registrar_documento(dados_doc) 

