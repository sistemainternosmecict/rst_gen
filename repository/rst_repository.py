from datetime import datetime
import json
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


class Rst_repository:
    def __init__(self):
        self.db_url: str = os.getenv("LOCAL_DB_URL")

        if not self.db_url:
            raise ValueError("A variável LOCAL_DB_URL precisa estar configurada no .env")

        self.engine = create_engine(self.db_url, pool_pre_ping=True, pool_recycle=3600)

    def registrar_novo_documento_banco(self, payload_completo) -> dict:
        if hasattr(payload_completo, "model_dump"):
            dict_payload = payload_completo.model_dump()
        elif hasattr(payload_completo, "dict"):
            dict_payload = payload_completo.dict()
        elif isinstance(payload_completo, dict):
            dict_payload = payload_completo.copy()
        else:
            dict_payload = dict(payload_completo)

        if isinstance(dict_payload.get("rst_causas"), (list, dict)):
            dict_payload["rst_causas"] = json.dumps(dict_payload["rst_causas"], ensure_ascii=False)

        if "created_at" not in dict_payload or not dict_payload["created_at"]:
            dict_payload["created_at"] = datetime.now().isoformat()

        colunas = [
            "created_at",
            "rst_data_chamado",
            "rst_unidade_escolar",
            "rst_email_unidade",
            "rst_bairro",
            "rst_distrito",
            "rst_nome_solicitante",
            "rst_cargo_solicitante",
            "rst_matricula_solicitante",
            "rst_nome_tecnico",
            "rst_data_atendimento",
            "rst_procedimentos",
            "rst_causas",
            "rst_assinatura_solicitante",
            "rst_assinatura_tecnico",
            "rst_task_id",
            "rst_link_arquivo_drive",
            "rst_doc_hash",
            "rst_numero_oficio",
            "rst_observacoes",
            "rst_user_id",
        ]

        dados_inserir = {k: dict_payload.get(k) for k in colunas if k in dict_payload}

        colunas_sql = ", ".join(dados_inserir.keys())
        params_sql = ", ".join([f":{k}" for k in dados_inserir.keys()])
        query = text(f"INSERT INTO tb_rst_docs ({colunas_sql}) VALUES ({params_sql})")

        try:
            with self.engine.begin() as conn:
                result = conn.execute(query, dados_inserir)
                inserted_id = result.lastrowid

                query_select = text("SELECT * FROM tb_rst_docs WHERE id = :id")
                registro = conn.execute(query_select, {"id": inserted_id}).mappings().first()

                if registro:
                    retorno = dict(registro)
                    if isinstance(retorno.get("rst_causas"), str):
                        try:
                            retorno["rst_causas"] = json.loads(retorno["rst_causas"])
                        except Exception:
                            pass
                    print(f"Sucesso: Documento com Hash {dict_payload.get('rst_doc_hash')} inserido na tb_rst_docs (ID: {inserted_id}).")
                    return retorno

            return {}

        except Exception as e:
            print(f"Erro crítico ao persistir dados na tabela tb_rst_docs: {e}")
            raise e

    def obter_dados_documento(self, hash: str) -> dict:
        try:
            query = text("SELECT * FROM tb_rst_docs WHERE rst_doc_hash = :hash")
            with self.engine.connect() as conn:
                registro = conn.execute(query, {"hash": hash}).mappings().first()

                if registro:
                    retorno = dict(registro)
                    if isinstance(retorno.get("rst_causas"), str):
                        try:
                            retorno["rst_causas"] = json.loads(retorno["rst_causas"])
                        except Exception:
                            pass
                    print(f"Sucesso: Registro encontrado para o hash {hash}")
                    return retorno

            print(f"Aviso: Nenhum registro encontrado para o hash {hash}")
            return {}

        except Exception as e:
            print(f"Erro ao buscar dados por hash na tabela tb_rst_docs: {e}")
            raise e

