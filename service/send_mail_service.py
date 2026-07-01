import os, smtplib, io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from googleapiclient.http import MediaIoBaseDownload
from repository.drive_repository import Drive_repository

load_dotenv()

class Send_mail_service:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.drive_repo = Drive_repository()
        self.service = self.drive_repo.obter_service()

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
        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = email_unidade
        msg['Subject'] = "Relatório de Serviço Técnico - SMECICT"
        corpo_html = """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <h2 style="color: #0056b3;">Agradecimento</h2>
                <p>Olá,</p>
                <p>Gostaríamos de agradecer pela recepção e colaboração durante o atendimento realizado em sua unidade escolar.</p>
                <p>O <strong>Relatório de Serviço Técnico (RST)</strong> referente à visita foi gerado com sucesso, assinado digitalmente e encontra-se <strong>anexado a esta mensagem</strong> para fins de arquivamento e conferência.</p>
                <p>Qualquer dúvida ou nova solicitação, estaremos à total disposição para ajudá-los.</p>
                <br>
                <p>Atenciosamente,</p>
                <p><strong>SMECICT</strong><br>
                Prefeitura Municipal de Saquarema / RJ</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(corpo_html, 'html'))
        anexo = MIMEBase('application', 'pdf')
        anexo.set_payload(bytes_pdf)
        encoders.encode_base64(anexo)
        anexo.add_header(
            'Content-Disposition',
            'attachment',
            filename="Relatorio_Serviço_Tecnico.pdf"
        )
        msg.attach(anexo)
        return msg

    def enviar_email_para_unidade(self, email_unidade: str, link_arquivo_drive: str):
        """
        Método principal que coordena o download, montagem do e-mail e envio via SMTP.
        """
        print(f">>> Iniciando processo de envio para EMAIL: {email_unidade}")
        print(f">>> ARQUIVO_DRIVE: {link_arquivo_drive}")
        try:
            bytes_pdf = self._criar_copia_do_documento(link_arquivo_drive)
            mensagem_completa = self._construir_mensagem(email_unidade, bytes_pdf)
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Ativa a criptografia TLS obrigatória
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, email_unidade, mensagem_completa.as_string())
            print(f"Sucesso: E-mail enviado com sucesso para {email_unidade}!")
        except Exception as e:
            print(f"Erro crítico no envio de e-mail: {e}")
            raise e
