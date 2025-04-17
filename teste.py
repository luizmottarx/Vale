# teste.py
import csv
import os
import shutil
import tempfile
import re
from typing import Iterable

__all__ = ["fix_gds"]

# ------------------------------------------------------------------ #
# utilidades internas
# ------------------------------------------------------------------ #
_num_re = re.compile(r"""^[\s"'+-]*\d{1,3}(?:\.\d{3})*(?:,\d+)?$""")

def _é_numérico(token: str) -> bool:
    """
    Heurística:  se o campo contém só sinais, dígitos, pontos de milhar
    OU vírgula decimal -> consideramos número.
    """
    return bool(_num_re.match(token))

def _corrige_linha(campos: Iterable[str]) -> list[str]:
    corrigidos = []
    for campo in campos:
        t = campo.strip()
        if _é_numérico(t) and "," in t:
            t = t.replace(".", "")      # remove ponto de milhar, se houver
            t = t.replace(",", ".")     # vírgula decimal -> ponto
        corrigidos.append(t)
    return corrigidos

# ------------------------------------------------------------------ #
# função pública
# ------------------------------------------------------------------ #
def fix_gds(path_original: str) -> str:
    """
    – Se o arquivo já estiver no padrão inglês, nada é feito.  
    – Caso contenha vírgula decimal, converte cada campo numérico
      (metadados **e** tabela) para ponto, mantendo o próprio arquivo.

    Retorna sempre o mesmo caminho recebido (`path_original`).
    """
    # 1) Lê rapidamente – se não encontrar “, \d” dentro de aspas,
    #    presumimos que já está OK
    with open(path_original, "r", encoding="latin-1") as f:
        texto = f.read()
    if '"'.encode() not in texto.encode() and "," not in texto:
        return path_original                # nada por fazer
    if not re.search(r'"\d+,\d+', texto):
        return path_original

    # 2) processa linha‑a‑linha criando ficheiro temporário
    dir_ = os.path.dirname(path_original)
    tmp_fd, tmp_name = tempfile.mkstemp(dir=dir_, suffix=".gds_tmp")
    os.close(tmp_fd)

    with \
        open(path_original, "r",  encoding="latin-1", newline="") as src, \
        open(tmp_name,      "w",  encoding="latin-1", newline="") as dst:

        leitor = csv.reader(src, delimiter=",", quotechar='"')
        gravar = csv.writer(dst,  delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)

        for row in leitor:
            gravar.writerow(_corrige_linha(row))

    # 3) move o temp para o lugar do original (backup opcional)
    # shutil.copy2(path_original, path_original + ".bak")   # se quiser
    shutil.move(tmp_name, path_original)
    return path_original
