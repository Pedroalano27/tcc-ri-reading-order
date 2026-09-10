"""
Extrai os ZIPs de diarios oficiais para data/raw/.

Os ZIPs baixados do Google Drive trazem uma pasta raiz chamada "Diarios " --
com um espaco no final, que o Windows nao aceita em nome de diretorio. Sem
saneamento a extracao falha em 100% dos arquivos, com FileNotFoundError.
Este script remove esse nivel redundante e limpa cada componente do caminho.

Uso:
    python src/data/extrair_zips.py <pasta_com_os_zips>
"""
import argparse
import zipfile
import glob
import os
import time

RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CARACTERES_INVALIDOS = '<>:"|?*'


def sanear(caminho, destino):
    """Remove o nivel raiz do ZIP e limpa cada parte do caminho para o Windows."""
    partes = [p for p in caminho.split("/") if p]
    if len(partes) > 1 and partes[0].strip().lower().startswith("di"):
        partes = partes[1:]          # descarta o nivel "Diarios "
    limpas = []
    for p in partes:
        p = p.rstrip(" .")           # Windows rejeita nome terminando em espaco ou ponto
        for c in CARACTERES_INVALIDOS:
            p = p.replace(c, "_")
        if p:
            limpas.append(p)
    return os.path.join(destino, *limpas) if limpas else None


def extrair(origem, destino):
    zips = sorted(glob.glob(os.path.join(origem, "*.zip")))
    if not zips:
        print(f"[!] Nenhum .zip encontrado em {origem}")
        return

    os.makedirs(destino, exist_ok=True)
    erros = []
    total = 0
    t0 = time.time()

    for z in zips:
        nome = os.path.basename(z)
        with zipfile.ZipFile(z) as f:
            for info in f.infolist():
                if info.is_dir():
                    continue
                alvo = sanear(info.filename, destino)
                if not alvo:
                    continue
                try:
                    os.makedirs(os.path.dirname(alvo), exist_ok=True)
                    with f.open(info) as entrada, open(alvo, "wb") as saida:
                        while True:
                            bloco = entrada.read(1024 * 1024)
                            if not bloco:
                                break
                            saida.write(bloco)
                    total += 1
                except Exception as e:
                    erros.append((info.filename, f"{type(e).__name__}: {e}"))
        print(f"[{nome}] concluido - {total} arquivos ({time.time()-t0:.0f}s)", flush=True)

    print(f"\n[OK] {total} arquivos extraidos em {time.time()-t0:.0f}s")
    if erros:
        print(f"\n[!] {len(erros)} ERROS:")
        for fn, e in erros[:20]:
            print(f"  {fn} :: {e}")
    else:
        print("[OK] nenhum erro de extracao")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrai os ZIPs de diarios para data/raw/.")
    parser.add_argument("origem", help="pasta contendo os arquivos .zip")
    parser.add_argument("--dest", default=os.path.join(RAIZ_PROJETO, "data", "raw"),
                        help="destino da extracao (padrao: data/raw do projeto)")
    args = parser.parse_args()
    extrair(args.origem, args.dest)
