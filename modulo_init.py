    def __init__(self, dados, qr_code_url=None):
        self.image_path = self.resource_path("header.png")
        self.footer = self.resource_path("footer.png")
        self.qr_code_url = qr_code_url
        
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
