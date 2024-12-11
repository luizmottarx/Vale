# teste1.py

import os

class FileProcessor:
    def __init__(self, directory):
        self.directory = directory

    def process_gds_file(self, gds_file):
        try:
            with open(gds_file, 'r', encoding='latin-1') as file:
                lines = file.readlines()

            metadados = {}
            for line in lines[:57]:
                parts = line.strip().split(',')
                if len(parts) == 2 and parts[1].strip():
                    chave = parts[0].strip().strip('"')
                    valor = parts[1].strip().strip('"')
                    metadados[chave] = valor

            return metadados

        except Exception as e:
            print(f"Erro ao processar o arquivo '{gds_file}': {e}")
            return None