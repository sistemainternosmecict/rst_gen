import os
import requests
from dotenv import load_dotenv

load_dotenv()


class Send_mail_service:
    def enviar_email_para_unidade(self, email_unidade: str, link_arquivo_drive: str):
        try:
            url = os.getenv("API_URL_FOR_MAIL_SEND")
            dados_para_enviar = {
                "to": email_unidade,
                "drive_file_url": link_arquivo_drive,
            }
            resposta = requests.post(url, json=dados_para_enviar)
            resposta_retorno = {"sent": resposta.json()}
            return resposta_retorno

        except Exception as e:
            print(f"Erro crítico no envio de e-mail: {e}")
            raise e
