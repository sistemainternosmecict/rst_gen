import os
import io
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from dotenv import load_dotenv
from googleapiclient.http import MediaIoBaseDownload
from repository.drive_repository import Drive_repository

# Removemos o "import postmark" pois usaremos smtplib

load_dotenv()

class Send_mail_service:
    def __init__(self):
        self.server_token = os.getenv("POSTMARK_SERVER_TOKEN")
        self.sender_email = os.getenv("POSTMARK_SENDER_EMAIL")
        self.drive_repo = Drive_repository()
        self.service = self.drive_repo.obter_service()
        
        # Configurações do SMTP do Postmark
        self.smtp_server = "smtp.postmarkapp.com"
        self.smtp_port = 587  # Porta recomendada com STARTTLS

    def _criar_copia_do_documento(self, link_arquivo_drive: str) -> bytes:
        try:
            if "file/d/" in link_arquivo_drive:
                file_id = link_arquivo_drive.split("file/d/")[1].split("/")[0]
            elif "id=" in link_arquivo_drive:
                file_id = link_arquivo_drive.split("id=")[1].split("&")[0]
            else:
                file_id = link_arquivo_drive # Caso já seja o ID puro

            request = self.service.files().get_media(fileId=file_id)
            file_stream = io.BytesIO()
            downloader = MediaIoBaseDownload(file_stream, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

            return file_stream.getvalue()

        except Exception as e:
            print(f"Erro ao baixar o binário correto do arquivo no Drive: {e}")
            raise e

    def _construir_mensagem(self, email_unidade: str, bytes_pdf: bytes) -> MIMEMultipart:
        # Criamos uma mensagem multipart (necessária para e-mails com anexos)
        msg = MIMEMultipart("mixed")
        msg["From"] = self.sender_email
        msg["To"] = email_unidade
        msg["Subject"] = "Relatório de Serviço Técnico - SMECICT"

        # Corpo do e-mail em HTML
        corpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <h2 style="color: #0056b3;">Agradecimento</h2>
                <p>Olá,</p>
                <p>Gostaríamos de agradecer pela recepção e colaboração durante o atendimento realizado em sua unidade escolar.</p>
                <p>O <strong>Relatório de Serviço Técnico (RST)</strong> referente à visita foi gerado com sucesso, assinado digitalmente e encontra-se <strong>anexado a este e-mail</strong>.</p>
                <p>Qualquer dúvida ou nova solicitação, estaremos à total disposição para ajudá-los.</p>
                <br>
                <p>Atenciosamente,</p>
                <p><strong>SMECICT</strong><br>
                Prefeitura Municipal de Saquarema / RJ</p>
            </body>
        </html>
        """
        
        # Anexa a parte HTML ao e-mail
        parte_html = MIMEText(corpo_html, "html")
        msg.attach(parte_html)

        # Anexa o arquivo PDF
        parte_anexo = MIMEApplication(bytes_pdf, _subtype="pdf")
        parte_anexo.add_header(
            "Content-Disposition", 
            "attachment", 
            filename="Relatorio_Servico_Tecnico.pdf"
        )
        msg.attach(parte_anexo)

        return msg

    def enviar_email_para_unidade(self, email_unidade: str, link_arquivo_drive: str):
        try:
            # 1. Obtém os bytes do PDF a partir do Google Drive
            bytes_pdf = self._criar_copia_do_documento(link_arquivo_drive)
            
            # 2. Constrói o objeto de e-mail com anexo estruturado
            mensagem = self._construir_mensagem(email_unidade, bytes_pdf)
            
            # 3. Estabelece a ligação SMTP e envia
            print(f"Conectando ao servidor SMTP do Postmark para enviar para {email_unidade}...")
            
            # Criamos a conexão SMTP utilizando a porta 587
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Ativa a criptografia STARTTLS (obrigatória)
                
                # Autenticação: O Postmark utiliza o Server API Token tanto para o utilizador como para a senha
                server.login(self.server_token, self.server_token)
                
                # Envia o e-mail convertido para string
                server.sendmail(
                    self.sender_email, 
                    email_unidade, 
                    mensagem.as_string()
                )

            print(f"Sucesso: E-mail enviado com sucesso para {email_unidade}!")

        except Exception as e:
            print(f"Erro crítico no envio de e-mail: {e}")
            raise e
