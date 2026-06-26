import json, hashlib
from pydantic import BaseModel

class Ferramentas:
    def calcular_hash_documento(self, dados_doc:dict)->str:
        if isinstance(dados_doc, BaseModel):
            dados_puros = dados_doc.model_dump()
        elif isinstance(dados_doc, dict):
            dados_puros = dados_doc
        else:
            raise TypeError("Os dados precisam ser um dicionário ou um modelo Pydantic.")

        string_consistente = json.dumps(
            dados_puros,
            sort_keys=True,
            separators=(',', ':'),
            ensure_ascii=False
        )

        dados_em_bytes = string_consistente.encode('utf-8')
        hash_objeto = hashlib.sha256(dados_em_bytes)

        return hash_objeto.hexdigest()
