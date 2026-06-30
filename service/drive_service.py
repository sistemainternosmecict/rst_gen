from repository.drive_repository import Drive_repository

class Drive_service:
    def salvar_arquivo_drive(self, arquivo_pdf:str, gdrive_drive_id:str)->str:
        drive_repo = Drive_repository()
        url_arquivo_drive = drive_repo.salvar_arquivo_drive(arquivo_pdf, gdrive_drive_id)
        return url_arquivo_drive
