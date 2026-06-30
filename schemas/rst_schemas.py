from typing import List, Optional
from pydantic import BaseModel, Field

class RSTCreate(BaseModel):
    rst_data_chamado: str = Field(..., description="Data do chamado, ex: DD/MM/AAAA")
    rst_unidade_escolar: str = Field(..., min_length=2)
    rst_email_unidade: str
    rst_bairro: str
    rst_distrito: str
    rst_nome_solicitante: str
    rst_cargo_solicitante: str
    rst_matricula_solicitante: str
    rst_nome_tecnico: str
    rst_data_atendimento: str
    rst_procedimentos: str
    rst_numero_oficio: str
    rst_observacoes: Optional[str] = None
    rst_causas: List[str] = Field(default_factory=list)
    rst_assinatura_solicitante: str
    rst_assinatura_tecnico: str
    rst_task_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "rst_data_chamado": "25/06/2026",
                "rst_unidade_escolar": "Unidade de teste",
                "rst_email_unidade": "unidade@smec.saquarema.rj.gov.br",
                "rst_bairro": "Bacaxá",
                "rst_distrito": "Bacaxá",
                "rst_nome_solicitante": "Diretor tal",
                "rst_cargo_solicitante": "Diretor",
                "rst_matricula_solicitante": "321",
                "rst_nome_tecnico": "Fulano de tal",
                "rst_data_atendimento": "25/06/2026",
                "rst_procedimentos": "Procedimentos tal",
                "rst_numero_oficio": "50/2026",
                "rst_observacoes": "Observações inseridas de exemplo.",
                "rst_causas": ["Garantia de equipamentos", "Configuração de sistema"],
                "rst_assinatura_solicitante": "teste",
                "rst_assinatura_tecnico": "thyez",
                "rst_task_id": "id da task"
            }
        }

class RSTDatabasePreSend(RSTCreate):
    rst_link_arquivo_drive: str
    rst_doc_hash: str
