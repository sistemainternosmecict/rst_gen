import os
import hashlib
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_file, url_for, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path
from modulo import Relatorio_servico_tecnico
from supabase import create_client, Client

app = Flask(__name__)
# Mantendo as origens que foram adicionadas remotamente, mas permitindo flexibilidade se necessário
CORS(app, origins=["*"]) 

load_dotenv()

# Configuração Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def calcular_hash(data, signature):
    """Gera o hash SHA-256 combinando os dados e a assinatura"""
    # Use sort_keys=True para garantir consistência
    bloco_string = f"{json.dumps(data, sort_keys=True)}{signature}"
    return hashlib.sha256(bloco_string.encode('utf-8')).hexdigest()

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/assinar_documento', methods=['POST'])
def assinar_documento():
    print(request)
    dados_front = request.json
    print(dados_front)
    dados_servico = dados_front
    assinatura_rep = dados_front.get('assinatura')
    
    # 1. Calcular o Hash do documento
    current_hash = calcular_hash(
        data=dados_servico,
        signature=assinatura_rep
    )
    
    # 2. Salvar no Banco de Dados
    novo_documento = {
        "timestamp": datetime.utcnow().isoformat(),
        "document_data": dados_servico,
        "signature": assinatura_rep,
        "current_hash": current_hash
    }
    
    supabase.table("documentos_assinados").insert(novo_documento).execute()
    
    # 3. Gerar PDF com QR Code
    # Use request.host_url para obter a base URL correta
    validation_url = f"{request.host_url.rstrip('/')}/validar_documento_por_hash/{current_hash}"
    rst = Relatorio_servico_tecnico(dados_servico, qr_code_url=validation_url)
    rst.salvar()
    
    return jsonify({"status": "Documento assinado!", "hash_validacao": current_hash, "pdf_url": url_for("enviar_pdf", filename=rst.filename, _external=True)}), 201

@app.route('/verificar_integridade', methods=['GET'])
def verificar_integridade():
    # Esta rota pode precisar de ajuste dependendo de como a verificação de integridade será feita agora
    # Sem blockchain, a verificação individual é feita pela rota /validar_documento_por_hash/<hash>
    return jsonify({"status": "OK", "mensagem": "Verificação de integridade agora deve ser feita individualmente por hash."}), 200

@app.route('/validar_documento_por_hash/<string:hash>', methods=['GET'])
def validar_documento_por_hash(hash):
    hash_para_validar = hash
    if not hash_para_validar:
        return "Hash não fornecido", 400
        
    response = supabase.table("documentos_assinados").select("*").eq("current_hash", hash_para_validar).execute()
    documento = response.data
    
    if not documento:
        return render_template('validar.html', status='ERRO', mensagem='Documento não encontrado ou hash inválido.'), 404
        
    doc = documento[0]
    
    # Garantir que dados_documento seja um dicionário
    dados = doc['document_data']
    if isinstance(dados, str):
        try:
            dados = json.loads(dados)
        except json.JSONDecodeError:
            # Se não for JSON válido, converter para dicionário simples para evitar erro no template
            dados = {"conteudo": dados}
            
    return render_template('validar.html', status='OK', mensagem='Documento íntegro e original.', dados_documento=dados)

@app.route("/", methods=["POST"])
def index():
    json_data = request.get_json()
    
    # Se houver assinatura, usa, caso contrário, hash apenas dos dados
    assinatura = json_data.get('assinatura', "")
    
    # Calcular o Hash do documento
    current_hash = calcular_hash(
        data=json_data,
        signature=assinatura
    )
    
    # Salvar no Banco de Dados
    novo_documento = {
        "timestamp": datetime.utcnow().isoformat(),
        "document_data": json_data,
        "signature": assinatura,
        "current_hash": current_hash
    }
    
    supabase.table("documentos_assinados").insert(novo_documento).execute()
    
    # Gerar URL de validação e o PDF
    validation_url = f"{request.host_url.rstrip('/')}/validar_documento_por_hash/{current_hash}"
    rst = Relatorio_servico_tecnico(json_data, qr_code_url=validation_url)
    rst.salvar()

    return jsonify({
        "arquivo_gerado": rst.filename,
        "success": True,
        "hash_validacao": current_hash,
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
            drive_url = Relatorio_servico_tecnico.upload_file_to_drive(str(temp_filepath), new_filename, 'application/pdf')
            
            # Clean up temporary file
            os.remove(temp_filepath)

            return jsonify({"message": "File uploaded successfully to Google Drive", "url": drive_url}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Invalid file type. Only PDF files are allowed."}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
