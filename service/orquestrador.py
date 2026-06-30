from service.pdf_service import Pdf_service
#from service.rst_service import Rst_service
from service.ferramentas import Ferramentas
from service.drive_service import Drive_service
from dotenv import load_dotenv
import os

load_dotenv()

class Orquestrador:
    def gerar_documento_assinado(self, dados_doc:dict):
        ferramentas = Ferramentas()
        rst_doc_hash = ferramentas.calcular_hash_documento(dados_doc)
        pdfS = Pdf_service()
        caminho_documento = pdfS.construir_documento(dados_doc, rst_doc_hash)
        drive_id_pasta = os.getenv("GDRIVE_DIR_ID")
        drive_s = Drive_service()
        link_arquivo_drive = drive_s.salvar_arquivo_drive(caminho_documento, drive_id_pasta)
        print(link_arquivo_drive)

        #rstS = Rst_service()
        #rst_doc_hash = rstS.registrar_documento(dados_doc) 

