import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

from src.version import __version__

GITHUB_API_URL = "https://api.github.com/repos/anderson561/analisedaeicms/releases/latest"
ASSET_NAME = "AuditaDAE-Windows-x64.zip"
NOME_EXECUTAVEL = "AuditaDAE.exe"
NOME_HELPER = "updater_helper.bat"


class UpdaterError(Exception):
    pass


@dataclass
class AtualizacaoDisponivel:
    versao_nova: str
    url_download: str
    notas: str


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def diretorio_instalacao() -> Path:
    """Pasta que contém AuditaDAE.exe — a que precisa ser trocada numa atualização.

    Não confundir com sys._MEIPASS (usado por tesseract_setup.py): aquele é
    _internal/, este é o pai do próprio executável.
    """
    return Path(sys.executable).resolve().parent


def pode_atualizar_automaticamente() -> bool:
    return os.access(diretorio_instalacao(), os.W_OK)


def parse_version(texto: str) -> tuple[int, int, int]:
    texto = texto.strip()
    if texto[:1].lower() == "v":
        texto = texto[1:]
    partes = texto.split(".")
    if len(partes) < 3:
        raise UpdaterError(f"versão mal formada: {texto!r}")

    def _num(parte: str) -> int:
        digitos = ""
        for caractere in parte:
            if not caractere.isdigit():
                break
            digitos += caractere
        if not digitos:
            raise UpdaterError(f"versão mal formada: {texto!r}")
        return int(digitos)

    return (_num(partes[0]), _num(partes[1]), _num(partes[2]))


def versao_mais_nova(atual: str, remota: str) -> bool:
    return parse_version(remota) > parse_version(atual)


def _extrair_info_release(dados: dict) -> AtualizacaoDisponivel | None:
    tag = dados.get("tag_name") or ""
    if not tag or not versao_mais_nova(__version__, tag):
        return None
    asset = next((a for a in dados.get("assets", []) if a.get("name") == ASSET_NAME), None)
    if asset is None:
        return None
    return AtualizacaoDisponivel(
        versao_nova=tag[1:] if tag[:1].lower() == "v" else tag,
        url_download=asset["browser_download_url"],
        notas=dados.get("body") or "",
    )


def verificar_atualizacao_disponivel() -> AtualizacaoDisponivel | None:
    """Consulta o último release do GitHub. Retorna None quando não há
    atualização (inclusive quando o repositório ainda não tem nenhum release
    publicado — HTTP 404, não é considerado falha). Outras falhas (sem
    internet, rate limit, GitHub fora do ar) propagam a exceção."""
    requisicao = urllib.request.Request(
        GITHUB_API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "AuditaDAE-Updater",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=10) as resposta:
            dados = json.loads(resposta.read())
    except urllib.error.HTTPError as erro:
        if erro.code == 404:
            return None
        raise

    return _extrair_info_release(dados)


def preparar_staging() -> Path:
    pai = diretorio_instalacao().parent
    return pai / f".auditadae_update_{os.getpid()}_{int(time.time())}"


def baixar_e_extrair(url: str, staging_pai: Path) -> Path:
    staging_pai.mkdir(parents=True, exist_ok=True)
    caminho_zip = staging_pai / "update.zip"
    urllib.request.urlretrieve(url, caminho_zip)

    if not zipfile.is_zipfile(caminho_zip):
        raise UpdaterError("arquivo baixado não é um zip válido (download corrompido ou incompleto).")

    extraido = staging_pai / "novo"
    with zipfile.ZipFile(caminho_zip) as arquivo_zip:
        arquivo_zip.extractall(extraido)

    if not (extraido / NOME_EXECUTAVEL).exists():
        raise UpdaterError(f"pacote extraído não contém {NOME_EXECUTAVEL} (asset malformado).")

    caminho_zip.unlink(missing_ok=True)
    return extraido


def aplicar_atualizacao(staging_novo: Path) -> None:
    """Dispara o helper (.bat) destacado, que espera este processo encerrar,
    troca a pasta de instalação pela nova versão e relança o app. O chamador
    deve fechar a janela/sair do processo logo em seguida."""
    install_dir = diretorio_instalacao()
    staging_pai = staging_novo.parent

    origem_bat = Path(getattr(sys, "_MEIPASS", install_dir)) / NOME_HELPER
    bat_copiado = staging_pai / NOME_HELPER
    shutil.copy2(origem_bat, bat_copiado)

    comspec = os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe")
    subprocess.Popen(
        [comspec, "/c", str(bat_copiado), str(install_dir), str(staging_novo), str(os.getpid())],
        cwd=str(staging_pai),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def limpar_instalacao_antiga() -> None:
    """Remove o backup de uma atualização anterior (AuditaDAE_old), se existir.
    Chamado pelo próprio app no início, só depois de já ter iniciado com
    sucesso na nova versão -- nunca pelo .bat, que é a rede de segurança caso
    a nova versão não abra."""
    instalacao = diretorio_instalacao()
    backup = instalacao.with_name(instalacao.name + "_old")
    if backup.exists():
        shutil.rmtree(backup, ignore_errors=True)

    for pasta_staging in instalacao.parent.glob(".auditadae_update_*"):
        shutil.rmtree(pasta_staging, ignore_errors=True)
