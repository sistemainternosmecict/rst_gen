import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class Drive_service:
    SCOPES = ["https://www.googleapis.com/auth/drive"]

    def __init__(self):
        creds_path = os.getenv("SERVICE_ACCOUNT_PATH")
        if not os.path.exists(creds_path):
                raise FileNotFoundError(f"Arquivo de credenciais não encontrado em: {creds_path}")

        self.service = self._autenticar(creds_path)

    def _autenticar(self, creds_path:str):
        usuario_alvo = "thyezoliveiramonteiro@smec.saquarema.rj.gov.br"
        creds = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=self.SCOPES
        ).with_subject(usuario_alvo)
        return build('drive', 'v3', credentials=creds)

    def salvar_arquivo_drive(self, arquivo_pdf:str, drive_dir_id:str)->str:
        try:
            nome_arquivo = os.path.basename(arquivo_pdf)
            file_metadata = {
                'name': nome_arquivo,
                'parents': [drive_dir_id]
            }
            media = MediaFileUpload(
                arquivo_pdf,
                mimetype='application/pdf',
                resumable=True
            )
            arquivo_drive = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink',
                supportsAllDrives=True
            ).execute()

            link_visualizacao = arquivo_drive.get('webViewLink')
            return link_visualizacao
        except Exception as error:
            print(f"Ocorreu um erro ao fazer upload para o Google Drive: {error}")
            raise error
