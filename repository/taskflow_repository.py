from dotenv import load_dotenv
from supabase import create_client, Client
import os

load_dotenv()

class Taskflow_repository:
    def __init__(self):
        self.url: str = os.getenv("TF_SUPABASE_URL")
        self.key: str = os.getenv("TF_SUPABASE_KEY")
        if not self.url or not self.key:
            raise ValueError("As variáveis TF_SUPABASE_URL e TF_SUPABASE_KEY precisam estar configuradas no .env")
        self.supabase: Client = create_client(self.url, self.key)

    def inserir_comentario_na_task(self, task_id:str, link_arquivo_drive:str, file_name:str, user_id:str):
        content = f"Relatório de serviço técnico, assinado digitalmente e anexado automaticamente à demanda. Uma cópia do documento foi enviada para a unidade atendida. A validade do documento pode ser verificada por meio do seu codigo QR ou o link da verificação impressos no documento."
        payload = {
            "task_id": task_id,
            "user_id": user_id,
            "content": content
        }
        if file_name:
            payload["file_name"] = file_name
        if link_arquivo_drive:
            payload["file_url"] = link_arquivo_drive

        try:
            resposta = self.supabase.table("comments").insert(payload).execute()
            print("Comentário inserido com sucesso!")
            return resposta.data[0] if resposta.data else {}
        except Exception as e:
            print(f"Erro ao inserir comentário no Supabase: {e}")
            raise e
