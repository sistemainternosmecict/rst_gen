# 📄 API para geração de Relatório de Serviço Técnico (RST)

Uma solução robusta e automatizada para a **geração de documentos PDF**, **registro de metadados em banco de dados** e **validação de autenticidade** de arquivos.

---

## 🚨 BREAKING CHANGE

> [!WARNING]
> **Migração de Banco de Dados: Supabase ➔ MySQL Local via SQLAlchemy**
> 
> O serviço de persistência e consulta da tabela `tb_rst_docs` (utilizado pelo `Rst_repository`) foi totalmente migrado da biblioteca cliente do Supabase para conexão **MySQL local via SQLAlchemy**.
> 
> * **Variáveis Removidas / Descontinuadas:**
>   * `RST_SUPABASE_URL`
>   * `RST_SUPABASE_KEY`
> * **Nova Variável Obrigatória (`.env`):**
>   * `LOCAL_DB_URL`: String de conexão SQLAlchemy para o MySQL local (ex: `mysql+pymysql://usuario:senha@127.0.0.1:3306/nome_banco?charset=utf8mb4`).
> * **Novas Dependências:**
>   * `sqlalchemy`
>   * `pymysql`
>   * `cryptography`
> 
> *Obs.: As credenciais e integrações de `TF_SUPABASE_*` (`Taskflow_repository`) e Google Drive (`Drive_repository`) permanecem inalteradas.*

---

## 🚀 Funcionalidades Principais

* **Geração de RST em PDF:** Criação dinâmica de relatório a partir de templates ou dados de entrada.
* **Persistência de Dados (MySQL Local):** Registro automático de logs, metadados do documento e status na tabela `tb_rst_docs` via SQLAlchemy.
* **Validação de Documentos:** Mecanismo de checagem (via Hash SHA-256 ou QR Code) para garantir a integridade e autenticidade do arquivo gerado.
* **Integração Google Drive & Taskflow:** Envio automatizado dos PDFs gerados ao Google Drive e comentários na respectiva task.

---

## ⚙️ Configuração de Ambiente (`.env`)

Exemplo das variáveis necessárias para execução do projeto:

```env
# Taskflow (Supabase)
TF_SUPABASE_URL=https://<seu-projeto>.supabase.co
TF_SUPABASE_KEY=<sua-key>

# Banco de Dados Local (MySQL - SQLAlchemy)
LOCAL_DB_URL=mysql+pymysql://usuario:senha@127.0.0.1:3306/smecict_2026?charset=utf8mb4

# Credenciais e Serviços
SERVICE_ACCOUNT_PATH=creds.json
API_URL_FOR_MAIL_SEND="https://..."
URL_BASE=https://...
LOCAL_PDF_DIR=rst/
GDRIVE_DIR_ID=<id-pasta-drive>
CORS_ORIGINS=http://localhost:8081,https://...
TEMPLATE_PATH=service/template.pdf
```

---

## 🛠️ Autoria e Propósito

Este sistema foi idealizado e desenvolvido por:

* **Thyéz de Oliveira Monteiro**
  * *Assessor de Informática — Subsecretaria de Tecnologia (SMECICT)*
  * **Atuação:** Desenvolvimento de integrações para sistemas internos e otimização de fluxos de trabalho por meio da criação de sistemas e APIs.

---
💡 *Desenvolvido com foco no benefício, modernização e eficiência dos serviços internos da **SMECICT**.*

