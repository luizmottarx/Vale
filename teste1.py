# teste1.py

import os
from testeBD import DatabaseManager

class FileProcessor:
    def __init__(self, directory):
        self.directory = directory
        self.db_manager = DatabaseManager()
        self.metadados_map = self.db_manager.get_metadados_map()

    def process_gds_file(self, gds_file):
        """
        Lê o arquivo .gds e extrai metadados das linhas que aparecem
        antes do cabeçalho "Stage Number". Substitui as chaves
        pelos abbreviations em self.metadados_map, caso existam.
        """
        try:
            with open(gds_file, 'r', encoding='latin-1') as file:
                lines = file.readlines()

            # 1) Encontrar a linha do cabeçalho (que contém "Stage Number")
            header_index = None
            for i, line in enumerate(lines):
                if "Stage Number" in line:
                    header_index = i
                    break

            # Se não encontrar a linha "Stage Number", assume que não há tabela
            # e consideramos o arquivo inteiro como "metadados".
            if header_index is None:
                header_index = len(lines)

            # 2) Extrair metadados apenas das linhas acima do cabeçalho
            metadata_lines = lines[:header_index]

            metadados = {}
            for line in metadata_lines:
                # Cada linha de metadados supõe ter o formato "Chave,Valor"
                parts = line.strip().split(',')
                if len(parts) == 2 and parts[1].strip():
                    chave_completa = parts[0].strip().strip('"')
                    valor = parts[1].strip().strip('"')

                    # Verificar se existe abreviação no dicionário do BD
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
