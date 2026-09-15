import io
import json
import subprocess
import urllib.error
import zipfile
from pathlib import Path

import pytest

from src import updater


# --- parse_version / versao_mais_nova ---------------------------------

@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("1.2.3", (1, 2, 3)),
        ("v1.2.3", (1, 2, 3)),
        ("V1.2.3", (1, 2, 3)),
        ("1.2.3-beta", (1, 2, 3)),
        ("2.10.0", (2, 10, 0)),
        (" v1.0.0 ", (1, 0, 0)),
    ],
)
def test_parse_version_aceita_variacoes(texto, esperado):
    assert updater.parse_version(texto) == esperado


def test_parse_version_rejeita_texto_mal_formado():
    with pytest.raises(updater.UpdaterError):
        updater.parse_version("nao-e-versao")


@pytest.mark.parametrize(
    "atual, remota, esperado",
    [
        ("1.0.0", "1.0.1", True),
        ("1.0.0", "1.1.0", True),
        ("1.0.0", "2.0.0", True),
        ("1.0.0", "1.0.0", False),
        ("1.2.0", "1.1.9", False),
        ("1.0.0", "v1.0.1", True),
    ],
)
def test_versao_mais_nova(atual, remota, esperado):
    assert updater.versao_mais_nova(atual, remota) is esperado


# --- _extrair_info_release ---------------------------------------------

def _release_json(tag, assets=None, body="notas da versão"):
    return {
        "tag_name": tag,
        "body": body,
        "assets": assets if assets is not None else [],
    }


def test_extrair_info_release_normal(monkeypatch):
    monkeypatch.setattr(updater, "__version__", "1.0.0", raising=False)
    dados = _release_json(
        "v1.1.0",
        assets=[
            {"name": "Source code (zip)", "browser_download_url": "http://x/source.zip"},
            {"name": updater.ASSET_NAME, "browser_download_url": "http://x/AuditaDAE-Windows-x64.zip"},
        ],
    )
    resultado = updater._extrair_info_release(dados)
    assert resultado is not None
    assert resultado.versao_nova == "1.1.0"
    assert resultado.url_download == "http://x/AuditaDAE-Windows-x64.zip"
    assert resultado.notas == "notas da versão"


def test_extrair_info_release_sem_asset_correto_retorna_none():
    dados = _release_json(
        "v99.0.0",
        assets=[{"name": "outro-arquivo.zip", "browser_download_url": "http://x/outro.zip"}],
    )
    assert updater._extrair_info_release(dados) is None


def test_extrair_info_release_tag_igual_ou_mais_antiga_retorna_none():
    dados = _release_json(
        "v1.0.0",
        assets=[{"name": updater.ASSET_NAME, "browser_download_url": "http://x/a.zip"}],
    )
    assert updater._extrair_info_release(dados) is None


# --- verificar_atualizacao_disponivel (HTTP mockado) --------------------

class _RespostaFalsa:
    def __init__(self, payload: dict):
        self._corpo = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._corpo

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_verificar_atualizacao_disponivel_sucesso(monkeypatch):
    dados = _release_json(
        "v9.9.9",
        assets=[{"name": updater.ASSET_NAME, "browser_download_url": "http://x/a.zip"}],
    )
    monkeypatch.setattr(updater.urllib.request, "urlopen", lambda *a, **k: _RespostaFalsa(dados))
    resultado = updater.verificar_atualizacao_disponivel()
    assert resultado is not None
    assert resultado.versao_nova == "9.9.9"


def test_verificar_atualizacao_disponivel_404_retorna_none(monkeypatch):
    def _levanta(*_a, **_k):
        raise urllib.error.HTTPError("url", 404, "not found", {}, None)

    monkeypatch.setattr(updater.urllib.request, "urlopen", _levanta)
    assert updater.verificar_atualizacao_disponivel() is None


@pytest.mark.parametrize("codigo", [403, 500])
def test_verificar_atualizacao_disponivel_erro_http_propaga(monkeypatch, codigo):
    def _levanta(*_a, **_k):
        raise urllib.error.HTTPError("url", codigo, "erro", {}, None)

    monkeypatch.setattr(updater.urllib.request, "urlopen", _levanta)
    with pytest.raises(urllib.error.HTTPError):
        updater.verificar_atualizacao_disponivel()


def test_verificar_atualizacao_disponivel_urlerror_propaga(monkeypatch):
    def _levanta(*_a, **_k):
        raise urllib.error.URLError("sem rede")

    monkeypatch.setattr(updater.urllib.request, "urlopen", _levanta)
    with pytest.raises(urllib.error.URLError):
        updater.verificar_atualizacao_disponivel()


# --- is_frozen / diretorio_instalacao / pode_atualizar_automaticamente --

def test_is_frozen_reflete_sys_frozen(monkeypatch):
    monkeypatch.setattr(updater.sys, "frozen", True, raising=False)
    assert updater.is_frozen() is True
    monkeypatch.setattr(updater.sys, "frozen", False, raising=False)
    assert updater.is_frozen() is False


def test_diretorio_instalacao_e_o_pai_do_executavel(monkeypatch, tmp_path):
    executavel = tmp_path / "AuditaDAE.exe"
    monkeypatch.setattr(updater.sys, "executable", str(executavel), raising=False)
    assert updater.diretorio_instalacao() == tmp_path


def test_pode_atualizar_automaticamente_usa_permissao_da_pasta(monkeypatch, tmp_path):
    monkeypatch.setattr(updater, "diretorio_instalacao", lambda: tmp_path)
    monkeypatch.setattr(updater.os, "access", lambda *_a, **_k: True)
    assert updater.pode_atualizar_automaticamente() is True
    monkeypatch.setattr(updater.os, "access", lambda *_a, **_k: False)
    assert updater.pode_atualizar_automaticamente() is False


# --- baixar_e_extrair ----------------------------------------------------

def _criar_zip_valido(caminho: Path) -> None:
    with zipfile.ZipFile(caminho, "w") as arquivo:
        arquivo.writestr("AuditaDAE.exe", "conteudo fake do executavel")
        arquivo.writestr("_internal/dummy.txt", "dado")


def test_baixar_e_extrair_sucesso(monkeypatch, tmp_path):
    origem_zip = tmp_path / "origem.zip"
    _criar_zip_valido(origem_zip)

    def _urlretrieve_falso(url, destino):
        Path(destino).write_bytes(origem_zip.read_bytes())

    monkeypatch.setattr(updater.urllib.request, "urlretrieve", _urlretrieve_falso)

    staging_pai = tmp_path / "staging"
    extraido = updater.baixar_e_extrair("http://x/a.zip", staging_pai)

    assert (extraido / "AuditaDAE.exe").exists()
    assert not (staging_pai / "update.zip").exists()


def test_baixar_e_extrair_zip_invalido_levanta_erro(monkeypatch, tmp_path):
    def _urlretrieve_falso(url, destino):
        Path(destino).write_bytes(b"isso nao e um zip")

    monkeypatch.setattr(updater.urllib.request, "urlretrieve", _urlretrieve_falso)

    with pytest.raises(updater.UpdaterError):
        updater.baixar_e_extrair("http://x/a.zip", tmp_path / "staging")


def test_baixar_e_extrair_sem_executavel_levanta_erro(monkeypatch, tmp_path):
    zip_sem_exe = tmp_path / "sem_exe.zip"
    with zipfile.ZipFile(zip_sem_exe, "w") as arquivo:
        arquivo.writestr("outro_arquivo.txt", "dado")

    def _urlretrieve_falso(url, destino):
        Path(destino).write_bytes(zip_sem_exe.read_bytes())

    monkeypatch.setattr(updater.urllib.request, "urlretrieve", _urlretrieve_falso)

    with pytest.raises(updater.UpdaterError):
        updater.baixar_e_extrair("http://x/a.zip", tmp_path / "staging")


# --- aplicar_atualizacao (subprocess mockado) ---------------------------

def test_aplicar_atualizacao_dispara_processo_destacado(monkeypatch, tmp_path):
    install_dir = tmp_path / "AuditaDAE"
    install_dir.mkdir()
    monkeypatch.setattr(updater, "diretorio_instalacao", lambda: install_dir)
    monkeypatch.setattr(updater.sys, "_MEIPASS", str(install_dir), raising=False)

    origem_bat = install_dir / updater.NOME_HELPER
    origem_bat.write_text("@echo off")

    staging_novo = tmp_path / "staging" / "novo"
    staging_novo.mkdir(parents=True)

    chamadas = {}

    def _popen_falso(args, **kwargs):
        chamadas["args"] = args
        chamadas["kwargs"] = kwargs

        class _ProcessoFalso:
            pass

        return _ProcessoFalso()

    monkeypatch.setattr(updater.subprocess, "Popen", _popen_falso)

    updater.aplicar_atualizacao(staging_novo)

    args = chamadas["args"]
    assert str(install_dir) in args
    assert str(staging_novo) in args
    assert chamadas["kwargs"]["cwd"] == str(staging_novo.parent)
    assert (staging_novo.parent / updater.NOME_HELPER).exists()


# --- limpar_instalacao_antiga --------------------------------------------

def test_limpar_instalacao_antiga_remove_backup_existente(monkeypatch, tmp_path):
    install_dir = tmp_path / "AuditaDAE"
    install_dir.mkdir()
    backup = tmp_path / "AuditaDAE_old"
    backup.mkdir()
    (backup / "arquivo.txt").write_text("lixo")

    monkeypatch.setattr(updater, "diretorio_instalacao", lambda: install_dir)

    updater.limpar_instalacao_antiga()

    assert not backup.exists()


def test_limpar_instalacao_antiga_sem_backup_nao_falha(monkeypatch, tmp_path):
    install_dir = tmp_path / "AuditaDAE"
    install_dir.mkdir()
    monkeypatch.setattr(updater, "diretorio_instalacao", lambda: install_dir)

    updater.limpar_instalacao_antiga()


def test_limpar_instalacao_antiga_remove_pastas_de_staging_orfas(monkeypatch, tmp_path):
    install_dir = tmp_path / "AuditaDAE"
    install_dir.mkdir()
    staging_orfao = tmp_path / ".auditadae_update_1234_999"
    staging_orfao.mkdir()
    (staging_orfao / "novo").mkdir()

    monkeypatch.setattr(updater, "diretorio_instalacao", lambda: install_dir)

    updater.limpar_instalacao_antiga()

    assert not staging_orfao.exists()
