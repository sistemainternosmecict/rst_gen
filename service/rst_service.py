from service.ferramentas import Ferramentas

class Rst_service:
    def registrar_documento(dados_doc:dict):
        ferramentas = Ferramentas()
        rst_doc_hash = ferramentas.calcular_hash_documento(dados_doc)

        return rst_doc_hash
