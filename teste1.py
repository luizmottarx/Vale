# teste1.py

import os
from testeBD import DatabaseManager

class FileProcessor:
    def __init__(self, directory):
        self.directory = directory
        self.db_manager = DatabaseManager()
        self.metadados_map = self.db_manager.get_metadados_map()

    def process_gds_file(self, gds_file):
        try:
            with open(gds_file, 'r', encoding='latin-1') as file:
                lines = file.readlines()

            metadados = {}
            for line in lines[:57]:
                parts = line.strip().split(',')
                if len(parts) == 2 and parts[1].strip():
                    chave_completa = parts[0].strip().strip('"')
                    valor = parts[1].strip().strip('"')
                    abreviacao = self.metadados_map.get(chave_completa)
                    if abreviacao:
                        metadados[abreviacao] = valor
                    else:
                        # Se não houver mapeamento, manter a chave original
                        metadados[chave_completa] = valor

            return metadados

        except Exception as e:
            print(f"Erro ao processar o arquivo '{gds_file}': {e}")
            return None
