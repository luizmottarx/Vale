# teste2.py

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
            dict: Dicionário de metadados completos com abreviações.
        """
        try:
            db_manager = DatabaseManager()
            metadados_completos = {}

            # Obter o mapa completo de metadados para abreviação
            metadados_map = db_manager.get_metadados_map()  # {metadado_completo: abreviacao}

            # Iterar sobre os metadados lidos e mapear para abreviações
            for metadado_completo, valor in metadados.items():
                abreviacao = metadados_map.get(metadado_completo)
                if abreviacao:
                    metadados_completos[abreviacao] = valor
                else:
                    # Se não houver mapeamento, manter a chave original
                    metadados_completos[metadado_completo] = valor

            return metadados_completos

        except Exception as e:
            print(f"Erro ao processar o estágio dos dados: {e}")
            return metadados
