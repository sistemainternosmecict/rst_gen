import os, sys, uuid
import base64
import io
import json
import qrcode
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import Image
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

load_dotenv()

# Configuração de credenciais
credentials_path = Path("credentials.json")

if not credentials_path.exists():
    credentials_data = json.loads(
        os.environ["GOOGLE_CREDENTIALS_JSON"]
    )

    with open(credentials_path, "w") as f:
        json.dump(credentials_data, f)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_path)

SCOPES = ['https://www.googleapis.com/auth/drive']

class Relatorio_servico_tecnico:
    BASE_EXPORT_DIR = Path(__file__).resolve().parent
    PAGE_WIDTH, PAGE_HEIGHT = A4
    LEFT_MARGIN = 40
    RIGHT_MARGIN = PAGE_WIDTH - 40
    current_y = PAGE_HEIGHT - 110
    def __init__(self, dados, qr_code_url=None):
        self.image_path = self.resource_path("header.png")
        self.footer = self.resource_path("footer.png")
        self.qr_code_url = qr_code_url
        self.dados_solicitante = {
            "nome": dados.get('nome_solicitante', ''),
            "cargo": dados.get('cargo_solicitante', ''),
            "matricula": dados.get('matricula_solicitante', '')
        }
        
        self.header_image = ImageReader(self.image_path)
        self.footer_image = ImageReader(self.footer)
        self.img_width = self.PAGE_WIDTH
        self.img_original_width, self.img_original_height = self.header_image.getSize()
        self.aspect = self.img_original_height / self.img_original_width
        self.img_height = self.img_width * self.aspect
        
        self.id_unico = str(uuid.uuid4().hex)[:8]
        self.filename = f"RST_{self.id_unico}.pdf"
        os.makedirs(self.BASE_EXPORT_DIR, exist_ok=True)
        self.export_dir = self.BASE_EXPORT_DIR
        self.definir_diretorio_exportacao(self.export_dir)
        self.c = canvas.Canvas(self.pdf_path, pagesize=A4)
        self.c.drawImage(
            self.header_image,
            0,                          
            self.PAGE_HEIGHT - self.img_height,  
            width=self.img_width,
            height=self.img_height,
            preserveAspectRatio=True,
            mask='auto'
        )

        self.assinatura_img = None
        if 'assinatura' in dados and dados['assinatura']:
            try:
                data = dados['assinatura'].split(',')[1] if ',' in dados['assinatura'] else dados['assinatura']
                img_data = base64.b64decode(data)
                self.assinatura_img = ImageReader(io.BytesIO(img_data))
            except Exception as e:
                print("Erro ao processar assinatura:", e)

        self.escrever_dados(dados)

    def adicionar_qr_code(self, url, x, y, size=80):
        qr = qrcode.make(url)
        # qr is a PIL image
        qr_io = io.BytesIO()
        qr.save(qr_io, format='PNG')
        qr_io.seek(0)
        qr_image = ImageReader(qr_io)
        self.c.drawImage(qr_image, x, y, width=size, height=size)

    @staticmethod
    def resource_path(relative_path):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    @staticmethod
    def upload_file_to_drive(file_path, file_name, mime_type):
        creds_file_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_file_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set or is empty.")
        if not os.path.exists(creds_file_path):
            raise FileNotFoundError(f"Service account credentials file not found at {creds_file_path}")

        creds = service_account.Credentials.from_service_account_file(creds_file_path, scopes=SCOPES, subject="thyezoliveiramonteiro@smec.saquarema.rj.gov.br")

        service = build('drive', 'v3', credentials=creds)

        folder_id = os.getenv('GOOGLE_DRIVE_RST_FOLDER_ID')
        if not folder_id:
            raise ValueError("Google Drive RST Folder ID not configured in .env")

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        return file.get('webViewLink')

    def draw_wrapped_text(self, text, x, y, max_width, font_name="Helvetica", font_size=9, line_height=12):
        c = self.c
        c.setFont(font_name, font_size)
        
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " + word if current_line else word)
            text_width = c.stringWidth(test_line, font_name, font_size)
            
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
                if c.stringWidth(word, font_name, font_size) > max_width:
                    for char in word:
                        if c.stringWidth(current_line + char, font_name, font_size) <= max_width:
                            current_line += char
                        else:
                            lines.append(current_line)
                            current_line = char
                    if current_line:
                        lines.append(current_line)
                    current_line = ""
                    continue
        
        if current_line:
            lines.append(current_line)

        current_y = y
        for line in lines:
            c.drawString(x, current_y, line)
            current_y -= line_height

        return current_y 

    def definir_diretorio_exportacao(self, dir):
        dir = os.path.join(dir, self.filename)
        self.pdf_path = dir
        return dir

    def escrever_dados(self, dados):
        c = self.c
        c.setTitle(f"Relatório de Serviço Técnico - {dados['data_chamado']}")
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(self.PAGE_WIDTH / 2, self.current_y, "RELATÓRIO DE SERVIÇO TÉCNICO")
        self.current_y -= 35
        c.setFillColor(colors.grey)
        c.rect(self.LEFT_MARGIN, self.current_y - 5, self.RIGHT_MARGIN - self.LEFT_MARGIN, 12, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self.PAGE_WIDTH / 2, self.current_y - 2, "Informações da Unidade")
        self.current_y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(self.LEFT_MARGIN, self.current_y, "Unidade Escolar:")
        c.drawString(self.LEFT_MARGIN + 85, self.current_y, dados['unidade_escolar'])
        c.line(self.LEFT_MARGIN + 85, self.current_y - 2, self.RIGHT_MARGIN, self.current_y - 2)
        self.current_y -= 20
        c.drawString(self.LEFT_MARGIN, self.current_y, "Bairro:")
        c.drawString(self.LEFT_MARGIN + 38, self.current_y, dados['bairro'])
        c.line(self.LEFT_MARGIN + 38, self.current_y - 2, self.LEFT_MARGIN + 200, self.current_y - 2)
        c.drawString(self.LEFT_MARGIN + 210, self.current_y, "Distrito:")
        c.drawString(self.LEFT_MARGIN + 250, self.current_y, dados['distrito'])
        c.line(self.LEFT_MARGIN + 250, self.current_y - 2, self.RIGHT_MARGIN, self.current_y - 2)
        self.current_y -= 25
        c.setFillColor(colors.grey)
        c.rect(self.LEFT_MARGIN, self.current_y - 5, self.RIGHT_MARGIN - self.LEFT_MARGIN, 12, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self.PAGE_WIDTH / 2, self.current_y - 2, "Dados do Solicitante")
        self.current_y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(self.LEFT_MARGIN, self.current_y, "Nome do solicitante:")
        c.drawString(self.LEFT_MARGIN + 95, self.current_y, dados['nome_solicitante'])
        c.line(self.LEFT_MARGIN + 95, self.current_y - 2, self.LEFT_MARGIN + 295, self.current_y - 2)
        c.drawString(self.LEFT_MARGIN + 300, self.current_y, "Cargo:")
        c.line(self.LEFT_MARGIN + 335, self.current_y - 2, self.LEFT_MARGIN + 435, self.current_y - 2)
        c.drawString(self.LEFT_MARGIN + 335, self.current_y, dados['cargo_solicitante'])
        c.drawString(self.LEFT_MARGIN + 440, self.current_y, "Mat:")
        c.line(self.LEFT_MARGIN + 460, self.current_y - 2, self.RIGHT_MARGIN, self.current_y - 2)
        c.drawString(self.LEFT_MARGIN + 460, self.current_y, dados['matricula_solicitante'])
        self.current_y -= 20
        c.drawString(self.LEFT_MARGIN, self.current_y, "Data:")
        c.drawString(self.LEFT_MARGIN + 30, self.current_y, dados['data_chamado'])
        c.line(self.LEFT_MARGIN + 30, self.current_y - 2, self.LEFT_MARGIN + 100, self.current_y - 2)
        dados_tecnico = {
            "nome_tecnico":dados["nome_tecnico"],
            "cargo_tecnico":dados["cargo_tecnico"],
            "matricula_tecnico":dados["matricula_tecnico"],
            "horario_atendimento":dados["horario_atendimento"],
            "data_atendimento":dados["data_atendimento"],
            "causa": []
        }
        dados_final = {
            "procedimentos_realizados":dados["procedimentos"],
            "observacoes":f'Este documento refere-se ao ofício de numero {dados["numero_oficio"]} da unidade {dados["unidade_escolar"]}. {dados["observacoes"]}'
        }
        if "causa" in dados:
            dados_tecnico["causa"] = dados["causa"]
        self.escrever_dados_tecnico(dados_tecnico)
        self.escrever_procedimentos_observacoes_avaliacao(dados_final)
        self.escrever_assinaturas_e_rodape()

    def escrever_dados_tecnico(self, dados_tecnico):
        c = self.c
        self.current_y -= 25
        self.current_y -= -5
        c.setFillColor(colors.grey)
        c.rect(self.LEFT_MARGIN, self.current_y - 5, self.RIGHT_MARGIN - self.LEFT_MARGIN, 12, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self.PAGE_WIDTH / 2, self.current_y - 2, "Dados do Técnico")
        self.current_y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(self.LEFT_MARGIN, self.current_y, "Nome do Técnico:")
        c.drawString(self.LEFT_MARGIN + 85, self.current_y, dados_tecnico['nome_tecnico'])
        c.line(self.LEFT_MARGIN + 85, self.current_y - 2, self.LEFT_MARGIN + 295, self.current_y - 2)
        c.drawString(self.LEFT_MARGIN + 300, self.current_y, "Cargo:")
        c.line(self.LEFT_MARGIN + 335, self.current_y - 2, self.LEFT_MARGIN + 435, self.current_y - 2)
        c.drawString(self.LEFT_MARGIN + 335, self.current_y, dados_tecnico['cargo_tecnico'])
        self.current_y -= 20
        c.drawString(self.LEFT_MARGIN, self.current_y, "Data:")
        c.drawString(self.LEFT_MARGIN + 30, self.current_y, dados_tecnico['data_atendimento'])
        c.line(self.LEFT_MARGIN + 30, self.current_y - 2, self.LEFT_MARGIN + 100, self.current_y - 2)
        self.current_y -= 25
        c.setFillColor(colors.grey)
        c.rect(self.LEFT_MARGIN, self.current_y - 5, self.RIGHT_MARGIN - self.LEFT_MARGIN, 12, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self.PAGE_WIDTH / 2, self.current_y - 2, "Causas ou Problemas Técnicos Relacionados")
        self.current_y -= 20
        if "causa" in dados_tecnico:
            c.setFont("Helvetica", 11)
            causas = [ "Configuração de sistema", "Entrega de equipamentos", "Substituição de equipamentos", "Manutenção de equipamentos", "Garantia de equipamentos", "Vistoria de equipamentos", "Remoção de equipamentos", "Rede e Internet", "Backup de arquivos", "Avaliação de Carência", "Outro" ]
            col_x = [self.LEFT_MARGIN, self.LEFT_MARGIN + 180, self.LEFT_MARGIN + 360]
            line_height = 16
            itens_por_coluna = 5
            for i, causa in enumerate(causas):
                col = i // itens_por_coluna
                row = i % itens_por_coluna
                x = col_x[col]
                y = self.current_y - (row * line_height)
                marcado = "x" if causa in dados_tecnico['causa'] else " "
                if causa == "Outro":
                    c.drawString(x, y, f"(  {marcado}  ) Outro: ________________", None, -0.5)
                else:
                    c.drawString(x, y, f"(  {marcado}  ) {causa}", None, -0.5)
            self.current_y -= (itens_por_coluna * line_height + 20)

    def escrever_procedimentos_observacoes_avaliacao(self, dados_final):
        c = self.c
        self.current_y -= -10
        c.setFillColor(colors.grey)
        c.rect(self.LEFT_MARGIN, self.current_y - 5, self.RIGHT_MARGIN - self.LEFT_MARGIN, 12, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self.PAGE_WIDTH / 2, self.current_y - 2, "Procedimentos Realizados")
        self.current_y -= 20
        c.setFont("Helvetica", 9)
        linhas_procedimentos = dados_final.get("procedimentos_realizados", "")
        self.current_y = self.draw_wrapped_text(
            text=linhas_procedimentos,
            x=self.LEFT_MARGIN,
            y=self.current_y,
            max_width=450,
            font_name="Helvetica",
            font_size=9,
            line_height=12
        )
        c.line(self.LEFT_MARGIN, self.current_y - 2, self.RIGHT_MARGIN, self.current_y - 2)
        self.current_y -= 20
        c.setFillColor(colors.grey)
        c.rect(self.LEFT_MARGIN, self.current_y - 5, self.RIGHT_MARGIN - self.LEFT_MARGIN, 12, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self.PAGE_WIDTH / 2, self.current_y - 2, "Observações")
        self.current_y -= 20
        c.setFont("Helvetica", 9)
        linhas_observacoes = dados_final.get("observacoes", "")
        self.current_y = self.draw_wrapped_text(
            text=linhas_observacoes,
            x=self.LEFT_MARGIN,
            y=self.current_y,
            max_width=450,
            font_name="Helvetica",
            font_size=9,
            line_height=12
        )
        c.line(self.LEFT_MARGIN, self.current_y - 2, self.RIGHT_MARGIN, self.current_y - 2)
        self.current_y -= 50

    def escrever_assinaturas_e_rodape(self):
        c = self.c
        c.setFillColor(colors.grey)
        c.rect(self.LEFT_MARGIN, self.current_y - 5, self.RIGHT_MARGIN - self.LEFT_MARGIN, 12, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self.PAGE_WIDTH / 2, self.current_y - 2, "Aceite do Serviço Técnico")
        self.current_y -= 55
        c.setFont("Helvetica", 9)
        linha_y = self.current_y
        largura_linha = 180
        
        # Linhas de assinatura
        c.line(self.LEFT_MARGIN, linha_y, self.LEFT_MARGIN + largura_linha, linha_y)
        c.line(self.RIGHT_MARGIN - largura_linha, linha_y, self.RIGHT_MARGIN, linha_y)
        c.drawCentredString(self.LEFT_MARGIN + largura_linha / 2, linha_y - 12, "Responsável Técnico")
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(self.RIGHT_MARGIN - largura_linha / 2, linha_y - 12, "Responsável na Unidade")
        
        # Bloco de dados do solicitante abaixo da assinatura
        c.setFont("Helvetica", 8)
        info_x = self.RIGHT_MARGIN - largura_linha / 2
        c.drawCentredString(info_x, linha_y - 24, str(self.dados_solicitante.get('nome', '')))
        c.drawCentredString(info_x, linha_y - 34, str(self.dados_solicitante.get('cargo', '')))
        c.drawCentredString(info_x, linha_y - 44, f"Mat: {self.dados_solicitante.get('matricula', '')}")
        
        c.setFont("Helvetica", 9)
        if self.assinatura_img:
            x_img = (self.RIGHT_MARGIN - largura_linha + 10) - 20 - 60
            y_img = linha_y - 130 # Ajustado para acomodar as 3 linhas
            c.drawImage(self.assinatura_img, x_img, y_img, width=320, height=180, preserveAspectRatio=True, mask='auto')
        
        if self.qr_code_url:
            size = 70
            x_qr = (self.PAGE_WIDTH - size) / 2
            self.adicionar_qr_code(self.qr_code_url, x_qr, 95, size=size)
            
            c.setFont("Helvetica", 7)
            c.drawCentredString(self.PAGE_WIDTH / 2, 85, f"Verifique a validade deste documento no link: {self.qr_code_url}")
        
        self.current_y = linha_y - 50
        try:
            c.drawImage(self.footer_image, -1, 0, width=self.PAGE_WIDTH + 1, height=60)
        except Exception as e:
            print("Erro ao inserir imagem de rodapé:", e)

    def salvar(self):
        print(f"PDF gerado em: {self.pdf_path}")
        self.c.save()
        return self.filename
