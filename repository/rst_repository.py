from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

class Rst_repository:
    def __init__(self):
        self.url: str = os.getenv("RST_SUPABASE_URL")
        self.key: str = os.getenv("RST_SUPABASE_KEY")

        if not self.url or not self.key:
            raise ValueError("As variáveis RST_SUPABASE_URL e RST_SUPABASE_KEY precisam estar configuradas no .env")
        self.supabase: Client = create_client(self.url, self.key)

    def registrar_novo_documento_banco(self, payload_completo:dict):
        dict_payload = payload_completo.dict()
        try:
            resposta = self.supabase.table("tb_rst_docs").insert(dict_payload).execute()
            if resposta.data:
                print(f"Sucesso: Documento com Hash {dict_payload.get('rst_doc_hash')} inserido na tb_rst_docs.")
                return resposta.data[0]

            return {}

        except Exception as e:
            print(f"Erro crítico ao persistir dados na tabela tb_rst_docs: {e}")
            raise e
