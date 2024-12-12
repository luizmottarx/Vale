# teste2.py

import os
from teste1 import FileProcessor
from testeBD import DatabaseManager

class StageProcessor:
    @staticmethod
    def process_stage_data(directory, gds_file, metadados):
        """
        Processa os metadados do arquivo .gds sem alterar as chaves.
        Utiliza o mapeamento de metadados definido em testeBD.py.

        Args:
            directory (str): Diretório onde o arquivo .gds está localizado.
            gds_file (str): Nome do arquivo .gds.
            metadados (dict): Dicionário de metadados lidos do arquivo.

        Returns:
            dict: Dicionário de metadados completos sem alteração nas chaves.
        """
        try:
            db_manager = DatabaseManager()
            metadados_completos = {}

            # Obter o mapa completo de metadados para abreviação
            metadados_map = db_manager.get_metadados_map()  # {metadado_completo: abreviacao}

            # Iterar sobre os metadados lidos do arquivo e mapear para abreviação
            for metadado_completo, valor in metadados.items():
                if metadado_completo in metadados_map:
                    abreviacao = metadados_map[metadado_completo]
                    metadados_completos[abreviacao] = valor
                else:
                    # Se o metadado não estiver na tabela metadadostable, pode optar por ignorar ou incluir
                    # Aqui, vamos incluir com a chave original
                    metadados_completos[metadado_completo] = valor

            return metadados_completos

        except Exception as e:
            print(f"Erro ao processar o estágio dos dados: {e}")
            return metadados
