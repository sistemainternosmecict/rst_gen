from repository.rst_repository import Rst_repository
class Rst_service:
    def registrar_documento(self, payload_completo:dict):
        rst_repo = Rst_repository()
        rst_repo.registrar_novo_documento_banco(payload_completo)
