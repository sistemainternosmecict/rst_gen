from repository.taskflow_repository import Taskflow_repository

class Taskflow_service:
    def inserir_comentario_na_task(self, task_id:str, link_arquivo_drive:str, file_name:str, user_id:str):
        tf_repo = Taskflow_repository()
        tf_repo.inserir_comentario_na_task(task_id, link_arquivo_drive, file_name, user_id)

