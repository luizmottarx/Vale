import os

class FileProcessor:
    def __init__(self, directory):
        self.directory = directory

    def process_gds_file(self, gds_file):
        try:
            with open(gds_file, 'r', encoding='latin-1') as file:
                lines = file.readlines()

            metadados = []
            for line in lines[:57]:
                parts = line.strip().split(',')
                if len(parts) == 2 and parts[1].strip():
                    metadados.append((parts[0].strip().strip('"'), parts[1].strip().strip('"')))

            return {item[0]: item[1] for item in metadados}

        except Exception as e:
            print(f"Erro ao processar o arquivo '{gds_file}': {e}")
            return None
