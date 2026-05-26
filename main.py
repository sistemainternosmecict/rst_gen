from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import os, sys, uuid
from flask import Flask, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import os
import json
from pathlib import Path

credentials_path = Path("credentials.json")

if not credentials_path.exists():
    credentials_data = json.loads(
        os.environ["GOOGLE_CREDENTIALS_JSON"]
    )

    with open(credentials_path, "w") as f:
        json.dump(credentials_data, f)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_path)

app = Flask(__name__)
# Mantendo as origens que foram adicionadas remotamente, mas permitindo flexibilidade se necessário
CORS(app, origins=["*"]) 

load_dotenv()

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

def draw_wrapped_text(c, text, x, y, max_width, font_name="Helvetica", font_size=9, line_height=12):
    """
    Desenha texto com quebra automática de linha dentro de uma largura máxima.
    
    Retorna a nova posição Y após o texto.
    """
    c.setFont(font_name, font_size)
    
    # Quebra o texto em palavras
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " + word if current_line else word)
        # Mede largura do texto
        text_width = c.stringWidth(test_line, font_name, font_size)
        
        if text_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
            # Se uma única palavra for maior que max_width, força quebra
            if c.stringWidth(word, font_name, font_size) > max_width:
                # Força quebra por caractere (raro, mas seguro)
                for char in word:
                    if c.stringWidth(current_line + char, font_name, font_size) <= max_width:
                        current_line += char
                    else:
                        lines.append(current_line)
                        current_line = char
                # Adiciona o resto
                if current_line:
                    lines.append(current_line)
                current_line = ""
                continue
    
    if current_line:
        lines.append(current_line)

    # Desenha cada linha
    current_y = y
    for line in lines:
        c.drawString(x, current_y, line)
        current_y -= line_height

    return current_y  # nova posição Y

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']

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

class Relatorio_servico_tecnico:
    BASE_EXPORT_DIR = Path(__file__).resolve().parent
    image_path = resource_path("header.png")
    footer = resource_path("footer.png")
    PAGE_WIDTH, PAGE_HEIGHT = A4
    LEFT_MARGIN = 40
    RIGHT_MARGIN = PAGE_WIDTH - 40
    current_y = PAGE_HEIGHT - 110

    header_image = ImageReader(image_path)
    footer_image = ImageReader(footer)
    img_width = PAGE_WIDTH
    img_original_width, img_original_height = header_image.getSize()
    aspect = img_original_height / img_original_width
    img_height = img_width * aspect

    def __init__(self, dados):
        self.id_unico = str(uuid.uuid4().hex)[:8]
        self.filename = f"RST_{self.id_unico}.pdf"
        os.makedirs(self.BASE_EXPORT_DIR, exist_ok=True)
        self.export_dir = self.BASE_EXPORT_DIR
        self.definir_diretorio_exportacao(self.export_dir)
        self.c = canvas.Canvas(self.pdf_path, pagesize=A4)
        self.c.drawImage(
            self.header_image,
            0,                          # x: início da imagem à esquerda
            self.PAGE_HEIGHT - self.img_height,  # y: topo da página menos altura da imagem
            width=self.img_width,
            height=self.img_height,
            preserveAspectRatio=True,
            mask='auto'
        )

        self.escrever_dados(dados)

    def definir_diretorio_exportacao(self, dir):
        dir = os.path.join(dir, self.filename)
        self.pdf_path = dir
        return dir

    def escrever_dados(self, dados):
        c = self.c

        c.setTitle(f"Relatório de Serviço Técnico - {dados['data_chamado']}")

        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(self.PAGE_WIDTH / 2, self.current_y, "RELATÓRIO DE SERVIÇO TÉCNICO")
        
        # self.inserir_protocolo_ao_lado(dados['protocolo'], self.current_y)
        self.current_y -= 35

        # Seção: Informações da Unidade (fundo cinza)
        c.setFillColor(colors.grey)
        c.rect(self.LEFT_MARGIN, self.current_y - 5, self.RIGHT_MARGIN - self.LEFT_MARGIN, 12, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self.PAGE_WIDTH / 2, self.current_y - 2, "Informações da Unidade")
        self.current_y -= 20

        # Campo: Unidade Escola
        c.setFont("Helvetica", 10)
        c.drawString(self.LEFT_MARGIN, self.current_y, "Unidade Escolar:")

        c.drawString(self.LEFT_MARGIN + 85, self.current_y, dados['unidade_escolar'])
        c.line(self.LEFT_MARGIN + 85, self.current_y - 2, self.RIGHT_MARGIN, self.current_y - 2)
        self.current_y -= 20

        # Campo: Bairro / Distrito / CEP
        c.drawString(self.LEFT_MARGIN, self.current_y, "Bairro:")
        c.drawString(self.LEFT_MARGIN + 38, self.current_y, dados['bairro'])
        c.line(self.LEFT_MARGIN + 38, self.current_y - 2, self.LEFT_MARGIN + 200, self.current_y - 2)

        c.drawString(self.LEFT_MARGIN + 210, self.current_y, "Distrito:")
        c.drawString(self.LEFT_MARGIN + 250, self.current_y, dados['distrito'])
        c.line(self.LEFT_MARGIN + 250, self.current_y - 2, self.RIGHT_MARGIN, self.current_y - 2)
        self.current_y -= 25

        # Seção: Dados do Solicitante (fundo cinza)
        c.setFillColor(colors.grey)
        c.rect(self.LEFT_MARGIN, self.current_y - 5, self.RIGHT_MARGIN - self.LEFT_MARGIN, 12, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self.PAGE_WIDTH / 2, self.current_y - 2, "Dados do Solicitante")
        self.current_y -= 20

        # Campo: Nome do solicitante
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
        # Seção: Dados do Técnico
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
        #c.drawString(self.LEFT_MARGIN + 440, self.current_y, "Mat:")
        #c.line(self.LEFT_MARGIN + 460, self.current_y - 2, self.RIGHT_MARGIN, self.current_y - 2)
        #c.drawString(self.LEFT_MARGIN + 460, self.current_y, dados_tecnico['matricula_tecnico'])
        self.current_y -= 20

        c.drawString(self.LEFT_MARGIN, self.current_y, "Data:")
        c.drawString(self.LEFT_MARGIN + 30, self.current_y, dados_tecnico['data_atendimento'])
        c.line(self.LEFT_MARGIN + 30, self.current_y - 2, self.LEFT_MARGIN + 100, self.current_y - 2)
        self.current_y -= 25

        # Seção: Causas ou Problemas Técnicos Relacionados
        c.setFillColor(colors.grey)
        c.rect(self.LEFT_MARGIN, self.current_y - 5, self.RIGHT_MARGIN - self.LEFT_MARGIN, 12, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self.PAGE_WIDTH / 2, self.current_y - 2, "Causas ou Problemas Técnicos Relacionados")
        self.current_y -= 20

        if "causa" in dados_tecnico:
            c.setFont("Helvetica", 11)
            causas = [ "Configuração de sistema", "Entrega de equipamentos", "Substituição de equipamentos", "Manutenção de equipamentos", "Garantia de equipamentos", "Vistoria de equipamentos", "Remoção de equipamentos", "Rede e Internet", "Backup de arquivos", "Avaliação de Carência", "Outro" ]

            # Quebra as causas em 3 colunas
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
        # Seção: Procedimentos Realizados
        c.setFillColor(colors.grey)
        c.rect(self.LEFT_MARGIN, self.current_y - 5, self.RIGHT_MARGIN - self.LEFT_MARGIN, 12, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self.PAGE_WIDTH / 2, self.current_y - 2, "Procedimentos Realizados")
        self.current_y -= 20

        c.setFont("Helvetica", 9)
        linhas_procedimentos = dados_final.get("procedimentos_realizados", "")
        
        self.current_y = draw_wrapped_text(
            c=c,
            text=linhas_procedimentos,
            x=self.LEFT_MARGIN,
            y=self.current_y,
            max_width=450,
            font_name="Helvetica",
            font_size=9,
            line_height=12  # espaço entre linhas
        )
        
        c.line(self.LEFT_MARGIN, self.current_y - 2, self.RIGHT_MARGIN, self.current_y - 2)
        self.current_y -= 20

        # Seção: Observações
        c.setFillColor(colors.grey)
        c.rect(self.LEFT_MARGIN, self.current_y - 5, self.RIGHT_MARGIN - self.LEFT_MARGIN, 12, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self.PAGE_WIDTH / 2, self.current_y - 2, "Observações")
        self.current_y -= 20

        c.setFont("Helvetica", 9)
        linhas_observacoes = dados_final.get("observacoes", "")
        
        self.current_y = draw_wrapped_text(
            c=c,
            text=linhas_observacoes,
            x=self.LEFT_MARGIN,
            y=self.current_y,
            max_width=450,
            font_name="Helvetica",
            font_size=9,
            line_height=12  # espaço entre linhas
        )

        c.line(self.LEFT_MARGIN, self.current_y - 2, self.RIGHT_MARGIN, self.current_y - 2)
        self.current_y -= 50

    def escrever_assinaturas_e_rodape(self):
        c = self.c

        # Seção: Aceite do Serviço Técnico
        c.setFillColor(colors.grey)
        c.rect(self.LEFT_MARGIN, self.current_y - 5, self.RIGHT_MARGIN - self.LEFT_MARGIN, 12, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self.PAGE_WIDTH / 2, self.current_y - 2, "Aceite do Serviço Técnico")
        self.current_y -= 55

        # Linhas de assinatura
        c.setFont("Helvetica", 9)
        linha_y = self.current_y

        # Linhas
        largura_linha = 180
        espacamento = 80
        c.line(self.LEFT_MARGIN, linha_y, self.LEFT_MARGIN + largura_linha, linha_y)
        c.line(self.RIGHT_MARGIN - largura_linha, linha_y, self.RIGHT_MARGIN, linha_y)

        # Legendas
        c.drawCentredString(self.LEFT_MARGIN + largura_linha / 2, linha_y - 12, "Responsável Técnico")
        c.drawCentredString(self.RIGHT_MARGIN - largura_linha / 2, linha_y - 12, "Unidade Escolar")

        self.current_y = linha_y - 50

        # Inserção do rodapé com imagem
        from reportlab.platypus import Image

        try:
            imagem = Image(self.footer)
            largura_imagem = self.PAGE_WIDTH
            altura_imagem = 60  # ajuste se necessário

            c.drawImage(self.footer_image, -1, 0, width=largura_imagem + 1, height=altura_imagem)
        except Exception as e:
            print("Erro ao inserir imagem de rodapé:", e)

    def salvar(self):
        print(f"PDF gerado em: {self.pdf_path}")
        self.c.save()
        return self.filename

@app.route("/", methods=["POST"])
def index():
    json_data = request.get_json()
    rst = Relatorio_servico_tecnico(json_data)
    rst.salvar()

    return jsonify({
        "arquivo_gerado": rst.filename,
        "success": True,
        "url": url_for("enviar_pdf", filename=rst.filename, _external=True)
    })

@app.route('/pdf/<filename>')
def enviar_pdf(filename):
    file_path = os.path.join(Relatorio_servico_tecnico.BASE_EXPORT_DIR, filename)
    if os.path.exists(file_path):
        return send_file(
            file_path,
            mimetype='application/pdf',
            as_attachment=False,
            download_name='relatorio.pdf'
        )
    return jsonify({"error": "Arquivo não encontrado"}), 404

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and file.filename.endswith('.pdf'):
        try:
            # Extract data for renaming from form fields
            numero_oficio_raw = request.form.get('numero_oficio')
            unidade_raw = request.form.get('unidade')

            if not numero_oficio_raw:
                return jsonify({"error": "Missing 'numero_oficio' in form data"}), 400
            if not unidade_raw:
                return jsonify({"error": "Missing 'unidade' in form data"}), 400

            # Process numero_oficio: get the first number before '/'
            numero_oficio_prefix = numero_oficio_raw.split('/')[0].strip()

            # Process unidade: remove specified prefixes
            prefixes_to_remove = [
                "Escola Municipal",
                "Creche Municipal",
                "Centro municipal de educação",
                "casa creche",
                "colegio",
                "escola municipalizada",
                "creche municipalizada"
            ]
            cleaned_unidade = unidade_raw
            for prefix in prefixes_to_remove:
                # Use .lower() for case-insensitive comparison
                if cleaned_unidade.lower().startswith(prefix.lower()):
                    cleaned_unidade = cleaned_unidade[len(prefix):].strip()
                    break # Assuming only one prefix will match

            # Construct the new filename
            new_filename = f"RST - {numero_oficio_prefix} - {cleaned_unidade}.pdf"

            # Save the file temporarily with the new name
            temp_dir = Path(__file__).resolve().parent / "temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)
            temp_filepath = temp_dir / new_filename
            file.save(temp_filepath)

            # Upload to Google Drive with the new name
            drive_url = upload_file_to_drive(str(temp_filepath), new_filename, 'application/pdf')
            
            # Clean up temporary file
            os.remove(temp_filepath)

            return jsonify({"message": "File uploaded successfully to Google Drive", "url": drive_url}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Invalid file type. Only PDF files are allowed."}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
