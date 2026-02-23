from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import os, sys
from reportlab.pdfgen import canvas
from flask import Flask, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["*"])

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

class Relatorio_servico_tecnico:
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
        self.filename = f"RST_gerado.pdf"
        self.export_dir = os.path.join(os.getcwd(), "")
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
        self.current_y -= -5
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
        self.current_y -= -5
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
        self.current_y -= -5
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
    #print(json_data)
    rst = Relatorio_servico_tecnico(json_data)
    rst.salvar()

    resposta_json = {
        "arquivo_gerado":rst.filename,
        "success":True
    }

    if resposta_json["success"]:
        return redirect(url_for("enviar_pdf"))
    return jsonify(resposta_json)

@app.route('/pdf')
def enviar_pdf():
    return send_file(
        'RST_gerado.pdf',
        mimetype='application/pdf',
        as_attachment=False,        # True = download, False = abrir no browser
        download_name='relatorio.pdf'
    )

if __name__ == "__main__":
    app.run(debug=True)
