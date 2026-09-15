import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

from src.db.database import obter_conexao
from src.db.repository import listar_historico
from src.main import (
    detectar_fontes_relatorio,
    processar_lote,
    verificar_pagamentos_lote,
    verificar_parcelamento_lote,
)
from src.models.dae_models import (
    DaeParceladoEncontrado,
    DaeParceladoNaoEncontrado,
    DaePagamentoNaoLocalizado,
    LinhaIcmsAt,
    NotaConciliada,
    NotaNaoEncontrada,
    PagamentoConfirmado,
    ResultadoProcessamento,
)
from src.reports.report_generator import (
    gerar_relatorio_conciliadas,
    gerar_relatorio_conciliadas_pdf,
    gerar_relatorio_icms_at_excel,
    gerar_relatorio_icms_at_pdf,
    gerar_relatorio_nao_encontradas,
    gerar_relatorio_nao_encontradas_pdf,
    gerar_relatorio_pagamentos_excel,
    gerar_relatorio_pagamentos_pdf,
    gerar_relatorio_parcelamento_excel,
    gerar_relatorio_parcelamento_pdf,
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("AuditaDAE — Conciliação de ICMS")
        self.geometry("820x640")
        self.minsize(700, 560)

        self.caminhos_dae: list[str] = []
        self.caminho_relatorio: str | None = None
        self.ultima_conciliacao: list[NotaConciliada] = []
        self.ultima_nao_encontradas: list[NotaNaoEncontrada] = []
        self.ultimas_linhas_icms_at: list[LinhaIcmsAt] = []
        self.buscar_aquisicao_pendente = True
        self.buscar_icms_at_pendente = False
        self.buscar_pagamento_dae_pendente = False
        self.ultimos_pagamentos_confirmados_planilha: list[PagamentoConfirmado] = []
        self.ultimos_pagamentos_nao_localizados_planilha: list[DaePagamentoNaoLocalizado] = []
        self.ultimos_parcelamento_encontrados_planilha: list[DaeParceladoEncontrado] = []
        self.ultimos_parcelamento_nao_encontrados_planilha: list[DaeParceladoNaoEncontrado] = []
        self.caminhos_dae_pagamentos: list[str] = []
        self.caminhos_relatorio_pagamento: list[str] = []
        self.ultimos_pagamentos_confirmados: list[PagamentoConfirmado] = []
        self.ultimos_pagamentos_nao_localizados: list[DaePagamentoNaoLocalizado] = []
        self.caminhos_dae_parcelamento: list[str] = []
        self.caminhos_parcelamento: list[str] = []
        self.ultimos_parcelamento_encontrados: list[DaeParceladoEncontrado] = []
        self.ultimos_parcelamento_nao_encontrados: list[DaeParceladoNaoEncontrado] = []

        self._montar_layout()
        self._atualizar_historico()

    def _montar_layout(self) -> None:
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(16, 8))

        aba_notas = self.tabview.add("Notas")
        aba_pagamentos = self.tabview.add("Pagamentos")
        aba_parcelamento = self.tabview.add("Parcelamento")

        self._montar_aba_notas(aba_notas)
        self._montar_aba_pagamentos(aba_pagamentos)
        self._montar_aba_parcelamento(aba_parcelamento)

        self.barra_progresso = ctk.CTkProgressBar(self, mode="indeterminate")
        self.barra_progresso.pack(fill="x", padx=16, pady=8)

        frame_historico = ctk.CTkFrame(self)
        frame_historico.pack(fill="x", padx=16, pady=(8, 16))
        ctk.CTkLabel(frame_historico, text="Histórico de Conciliações").pack(anchor="w", padx=8, pady=(8, 0))
        self.texto_historico = ctk.CTkTextbox(frame_historico, height=140)
        self.texto_historico.pack(fill="both", padx=8, pady=8)

    def _montar_aba_notas(self, aba) -> None:
        frame_dae = ctk.CTkFrame(aba)
        frame_dae.pack(fill="x", padx=8, pady=(8, 8))
        ctk.CTkLabel(frame_dae, text="DAE/DARF (PDF) — solte 1 ou mais arquivos aqui ou selecione").pack(anchor="w", padx=8, pady=(8, 0))
        self.lista_dae = ctk.CTkTextbox(frame_dae, height=90)
        self.lista_dae.pack(fill="x", padx=8, pady=8)
        self.lista_dae.drop_target_register(DND_FILES)
        self.lista_dae.dnd_bind("<<Drop>>", self._on_drop_dae)
        ctk.CTkButton(frame_dae, text="Selecionar PDF(s) de DAE", command=self._selecionar_daes).pack(padx=8, pady=(0, 8), anchor="w")

        frame_relatorio = ctk.CTkFrame(aba)
        frame_relatorio.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(
            frame_relatorio, text="Relatório de Notas Fiscais (xlsx/xls/csv/pdf) — opcional"
        ).pack(anchor="w", padx=8, pady=(8, 0))
        self.label_relatorio = ctk.CTkLabel(frame_relatorio, text="Nenhum arquivo selecionado")
        self.label_relatorio.pack(fill="x", padx=8, pady=4)
        self.label_relatorio.drop_target_register(DND_FILES)
        self.label_relatorio.dnd_bind("<<Drop>>", self._on_drop_relatorio)
        ctk.CTkButton(frame_relatorio, text="Selecionar Relatório", command=self._selecionar_relatorio).pack(
            padx=8, pady=(0, 8), anchor="w"
        )

        frame_acoes_notas_1 = ctk.CTkFrame(aba, fg_color="transparent")
        frame_acoes_notas_1.pack(fill="x", padx=8, pady=(0, 4))

        self.botao_processar = ctk.CTkButton(frame_acoes_notas_1, text="Processar", command=self._processar)
        self.botao_processar.pack(side="left")

        # Os 3 grupos abaixo só aparecem (pack) depois de "Processar" concluir,
        # e só os pertinentes às fontes escolhidas -- ver _atualizar_grupos_visiveis_notas.
        self.frame_grupo_aquisicao = ctk.CTkFrame(aba, fg_color="transparent")

        frame_aquisicao_linha1 = ctk.CTkFrame(self.frame_grupo_aquisicao, fg_color="transparent")
        frame_aquisicao_linha1.pack(fill="x", pady=(0, 4))

        self.botao_gerar_excel_conciliadas = ctk.CTkButton(
            frame_aquisicao_linha1,
            text="Gerar Relatório Excel (Conciliadas)",
            command=self._gerar_excel_conciliadas,
        )
        self.botao_gerar_excel_conciliadas.pack(side="left")

        self.botao_gerar_pdf = ctk.CTkButton(
            frame_aquisicao_linha1, text="Gerar Relatório PDF (Conciliadas)", command=self._gerar_pdf
        )
        self.botao_gerar_pdf.pack(side="left", padx=(8, 0))

        frame_aquisicao_linha2 = ctk.CTkFrame(self.frame_grupo_aquisicao, fg_color="transparent")
        frame_aquisicao_linha2.pack(fill="x")

        self.botao_gerar_excel_nao_encontradas = ctk.CTkButton(
            frame_aquisicao_linha2,
            text="Gerar Relatório Excel (Não Encontradas)",
            command=self._gerar_excel_nao_encontradas,
        )
        self.botao_gerar_excel_nao_encontradas.pack(side="left")

        self.botao_gerar_pdf_nao_encontradas = ctk.CTkButton(
            frame_aquisicao_linha2,
            text="Gerar Relatório PDF (Não Encontradas)",
            command=self._gerar_pdf_nao_encontradas,
        )
        self.botao_gerar_pdf_nao_encontradas.pack(side="left", padx=(8, 0))

        self.frame_grupo_icms_at = ctk.CTkFrame(aba, fg_color="transparent")

        self.botao_gerar_excel_icms_at = ctk.CTkButton(
            self.frame_grupo_icms_at,
            text="Gerar Relatório Excel (ICMS Antecipação Tributária)",
            command=self._gerar_excel_icms_at,
        )
        self.botao_gerar_excel_icms_at.pack(side="left")

        self.botao_gerar_pdf_icms_at = ctk.CTkButton(
            self.frame_grupo_icms_at,
            text="Gerar Relatório PDF (ICMS Antecipação Tributária)",
            command=self._gerar_pdf_icms_at,
        )
        self.botao_gerar_pdf_icms_at.pack(side="left", padx=(8, 0))

        self.frame_grupo_pagamento_dae = ctk.CTkFrame(aba, fg_color="transparent")

        frame_pagamento_dae_linha1 = ctk.CTkFrame(self.frame_grupo_pagamento_dae, fg_color="transparent")
        frame_pagamento_dae_linha1.pack(fill="x", pady=(0, 4))

        self.botao_gerar_excel_pagamentos_planilha = ctk.CTkButton(
            frame_pagamento_dae_linha1,
            text="Gerar Relatório Excel (Pagamentos via Planilha)",
            command=self._gerar_excel_pagamentos_planilha,
        )
        self.botao_gerar_excel_pagamentos_planilha.pack(side="left")

        self.botao_gerar_pdf_pagamentos_planilha = ctk.CTkButton(
            frame_pagamento_dae_linha1,
            text="Gerar Relatório PDF (Pagamentos via Planilha)",
            command=self._gerar_pdf_pagamentos_planilha,
        )
        self.botao_gerar_pdf_pagamentos_planilha.pack(side="left", padx=(8, 0))

        frame_pagamento_dae_linha2 = ctk.CTkFrame(self.frame_grupo_pagamento_dae, fg_color="transparent")
        frame_pagamento_dae_linha2.pack(fill="x")

        self.botao_gerar_excel_parcelamento_planilha = ctk.CTkButton(
            frame_pagamento_dae_linha2,
            text="Gerar Relatório Excel (Parcelamento via Planilha)",
            command=self._gerar_excel_parcelamento_planilha,
        )
        self.botao_gerar_excel_parcelamento_planilha.pack(side="left")

        self.botao_gerar_pdf_parcelamento_planilha = ctk.CTkButton(
            frame_pagamento_dae_linha2,
            text="Gerar Relatório PDF (Parcelamento via Planilha)",
            command=self._gerar_pdf_parcelamento_planilha,
        )
        self.botao_gerar_pdf_parcelamento_planilha.pack(side="left", padx=(8, 0))

    def _montar_aba_pagamentos(self, aba) -> None:
        frame_dae_pagamentos = ctk.CTkFrame(aba)
        frame_dae_pagamentos.pack(fill="x", padx=8, pady=(8, 8))
        ctk.CTkLabel(
            frame_dae_pagamentos, text="DAE/DARF (PDF) — solte 1 ou mais arquivos aqui ou selecione"
        ).pack(anchor="w", padx=8, pady=(8, 0))
        self.lista_dae_pagamentos = ctk.CTkTextbox(frame_dae_pagamentos, height=90)
        self.lista_dae_pagamentos.pack(fill="x", padx=8, pady=8)
        self.lista_dae_pagamentos.drop_target_register(DND_FILES)
        self.lista_dae_pagamentos.dnd_bind("<<Drop>>", self._on_drop_dae_pagamentos)
        ctk.CTkButton(
            frame_dae_pagamentos, text="Selecionar PDF(s) de DAE", command=self._selecionar_daes_pagamentos
        ).pack(padx=8, pady=(0, 8), anchor="w")

        frame_relatorio_pagamento = ctk.CTkFrame(aba)
        frame_relatorio_pagamento.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(
            frame_relatorio_pagamento,
            text="Relatório(s) de Pagamentos de DAE (PDF) — solte 1 ou mais arquivos aqui ou selecione",
        ).pack(anchor="w", padx=8, pady=(8, 0))
        self.lista_relatorio_pagamento = ctk.CTkTextbox(frame_relatorio_pagamento, height=70)
        self.lista_relatorio_pagamento.pack(fill="x", padx=8, pady=8)
        self.lista_relatorio_pagamento.drop_target_register(DND_FILES)
        self.lista_relatorio_pagamento.dnd_bind("<<Drop>>", self._on_drop_relatorio_pagamento)
        ctk.CTkButton(
            frame_relatorio_pagamento,
            text="Selecionar Relatório(s) de Pagamentos",
            command=self._selecionar_relatorios_pagamento,
        ).pack(padx=8, pady=(0, 8), anchor="w")

        frame_acoes_pagamentos = ctk.CTkFrame(aba, fg_color="transparent")
        frame_acoes_pagamentos.pack(fill="x", padx=8, pady=(0, 8))

        self.botao_verificar_pagamentos = ctk.CTkButton(
            frame_acoes_pagamentos,
            text="Verificar Pagamentos",
            command=self._verificar_pagamentos,
            state="disabled",
        )
        self.botao_verificar_pagamentos.pack(side="left")

        # Só aparecem (pack) depois de "Verificar Pagamentos" concluir com sucesso.
        self.botao_gerar_excel_pagamentos = ctk.CTkButton(
            frame_acoes_pagamentos,
            text="Gerar Relatório de Pagamentos Excel",
            command=self._gerar_excel_pagamentos,
        )

        self.botao_gerar_pdf_pagamentos = ctk.CTkButton(
            frame_acoes_pagamentos,
            text="Gerar Relatório de Pagamentos em PDF",
            command=self._gerar_pdf_pagamentos,
        )

    def _montar_aba_parcelamento(self, aba) -> None:
        frame_dae_parcelamento = ctk.CTkFrame(aba)
        frame_dae_parcelamento.pack(fill="x", padx=8, pady=(8, 8))
        ctk.CTkLabel(
            frame_dae_parcelamento, text="DAE/DARF (PDF) — solte 1 ou mais arquivos aqui ou selecione"
        ).pack(anchor="w", padx=8, pady=(8, 0))
        self.lista_dae_parcelamento = ctk.CTkTextbox(frame_dae_parcelamento, height=90)
        self.lista_dae_parcelamento.pack(fill="x", padx=8, pady=8)
        self.lista_dae_parcelamento.drop_target_register(DND_FILES)
        self.lista_dae_parcelamento.dnd_bind("<<Drop>>", self._on_drop_dae_parcelamento)
        ctk.CTkButton(
            frame_dae_parcelamento, text="Selecionar PDF(s) de DAE", command=self._selecionar_daes_parcelamento
        ).pack(padx=8, pady=(0, 8), anchor="w")

        frame_parcelamento = ctk.CTkFrame(aba)
        frame_parcelamento.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(
            frame_parcelamento,
            text="Relatório(s) de Parcelamento (PDF) — solte 1 ou mais arquivos aqui ou selecione",
        ).pack(anchor="w", padx=8, pady=(8, 0))
        self.lista_parcelamento = ctk.CTkTextbox(frame_parcelamento, height=70)
        self.lista_parcelamento.pack(fill="x", padx=8, pady=8)
        self.lista_parcelamento.drop_target_register(DND_FILES)
        self.lista_parcelamento.dnd_bind("<<Drop>>", self._on_drop_parcelamento)
        ctk.CTkButton(
            frame_parcelamento,
            text="Selecionar Relatório(s) de Parcelamento",
            command=self._selecionar_parcelamentos,
        ).pack(padx=8, pady=(0, 8), anchor="w")

        frame_acoes_parcelamento = ctk.CTkFrame(aba, fg_color="transparent")
        frame_acoes_parcelamento.pack(fill="x", padx=8, pady=(0, 8))

        self.botao_verificar_parcelamento = ctk.CTkButton(
            frame_acoes_parcelamento,
            text="Verificar Parcelamentos",
            command=self._verificar_parcelamento,
            state="disabled",
        )
        self.botao_verificar_parcelamento.pack(side="left")

        # Só aparecem (pack) depois de "Verificar Parcelamentos" concluir com sucesso.
        self.botao_gerar_excel_parcelamento = ctk.CTkButton(
            frame_acoes_parcelamento,
            text="Gerar Relatório de Parcelamento Excel",
            command=self._gerar_excel_parcelamento,
        )

        self.botao_gerar_pdf_parcelamento = ctk.CTkButton(
            frame_acoes_parcelamento,
            text="Gerar Relatório de Parcelamento PDF",
            command=self._gerar_pdf_parcelamento,
        )

    def _on_drop_dae(self, evento) -> None:
        caminhos = [c for c in self.tk.splitlist(evento.data) if c.lower().endswith(".pdf")]
        self.caminhos_dae.extend(caminhos)
        self._atualizar_lista_dae()

    def _selecionar_daes(self) -> None:
        caminhos = filedialog.askopenfilenames(title="Selecionar PDFs de DAE", filetypes=[("PDF", "*.pdf")])
        if caminhos:
            self.caminhos_dae.extend(caminhos)
            self._atualizar_lista_dae()

    def _atualizar_lista_dae(self) -> None:
        self.lista_dae.delete("1.0", "end")
        self.lista_dae.insert("1.0", "\n".join(self.caminhos_dae))

    def _on_drop_relatorio(self, evento) -> None:
        caminhos = self.tk.splitlist(evento.data)
        if caminhos:
            self.caminho_relatorio = caminhos[0]
            self.label_relatorio.configure(text=self.caminho_relatorio)

    def _selecionar_relatorio(self) -> None:
        caminho = filedialog.askopenfilename(
            title="Selecionar Relatório",
            filetypes=[("Planilhas e PDF", "*.xlsx *.xls *.csv *.pdf")],
        )
        if caminho:
            self.caminho_relatorio = caminho
            self.label_relatorio.configure(text=caminho)

    def _on_drop_dae_pagamentos(self, evento) -> None:
        caminhos = [c for c in self.tk.splitlist(evento.data) if c.lower().endswith(".pdf")]
        self.caminhos_dae_pagamentos.extend(caminhos)
        self._atualizar_lista_dae_pagamentos()
        self._atualizar_estado_botao_pagamentos()

    def _selecionar_daes_pagamentos(self) -> None:
        caminhos = filedialog.askopenfilenames(title="Selecionar PDFs de DAE", filetypes=[("PDF", "*.pdf")])
        if caminhos:
            self.caminhos_dae_pagamentos.extend(caminhos)
            self._atualizar_lista_dae_pagamentos()
            self._atualizar_estado_botao_pagamentos()

    def _atualizar_lista_dae_pagamentos(self) -> None:
        self.lista_dae_pagamentos.delete("1.0", "end")
        self.lista_dae_pagamentos.insert("1.0", "\n".join(self.caminhos_dae_pagamentos))

    def _on_drop_relatorio_pagamento(self, evento) -> None:
        caminhos = [c for c in self.tk.splitlist(evento.data) if c.lower().endswith(".pdf")]
        self.caminhos_relatorio_pagamento.extend(caminhos)
        self._atualizar_lista_relatorio_pagamento()
        self._atualizar_estado_botao_pagamentos()

    def _selecionar_relatorios_pagamento(self) -> None:
        caminhos = filedialog.askopenfilenames(
            title="Selecionar Relatório(s) de Pagamentos",
            filetypes=[("PDF", "*.pdf")],
        )
        if caminhos:
            self.caminhos_relatorio_pagamento.extend(caminhos)
            self._atualizar_lista_relatorio_pagamento()
            self._atualizar_estado_botao_pagamentos()

    def _atualizar_lista_relatorio_pagamento(self) -> None:
        self.lista_relatorio_pagamento.delete("1.0", "end")
        self.lista_relatorio_pagamento.insert("1.0", "\n".join(self.caminhos_relatorio_pagamento))

    def _atualizar_estado_botao_pagamentos(self) -> None:
        habilitado = bool(self.caminhos_dae_pagamentos) and bool(self.caminhos_relatorio_pagamento)
        self.botao_verificar_pagamentos.configure(state="normal" if habilitado else "disabled")

    def _on_drop_dae_parcelamento(self, evento) -> None:
        caminhos = [c for c in self.tk.splitlist(evento.data) if c.lower().endswith(".pdf")]
        self.caminhos_dae_parcelamento.extend(caminhos)
        self._atualizar_lista_dae_parcelamento()
        self._atualizar_estado_botao_parcelamento()

    def _selecionar_daes_parcelamento(self) -> None:
        caminhos = filedialog.askopenfilenames(title="Selecionar PDFs de DAE", filetypes=[("PDF", "*.pdf")])
        if caminhos:
            self.caminhos_dae_parcelamento.extend(caminhos)
            self._atualizar_lista_dae_parcelamento()
            self._atualizar_estado_botao_parcelamento()

    def _atualizar_lista_dae_parcelamento(self) -> None:
        self.lista_dae_parcelamento.delete("1.0", "end")
        self.lista_dae_parcelamento.insert("1.0", "\n".join(self.caminhos_dae_parcelamento))

    def _on_drop_parcelamento(self, evento) -> None:
        caminhos = [c for c in self.tk.splitlist(evento.data) if c.lower().endswith(".pdf")]
        self.caminhos_parcelamento.extend(caminhos)
        self._atualizar_lista_parcelamento()
        self._atualizar_estado_botao_parcelamento()

    def _selecionar_parcelamentos(self) -> None:
        caminhos = filedialog.askopenfilenames(
            title="Selecionar Relatório(s) de Parcelamento",
            filetypes=[("PDF", "*.pdf")],
        )
        if caminhos:
            self.caminhos_parcelamento.extend(caminhos)
            self._atualizar_lista_parcelamento()
            self._atualizar_estado_botao_parcelamento()

    def _atualizar_lista_parcelamento(self) -> None:
        self.lista_parcelamento.delete("1.0", "end")
        self.lista_parcelamento.insert("1.0", "\n".join(self.caminhos_parcelamento))

    def _atualizar_estado_botao_parcelamento(self) -> None:
        habilitado = bool(self.caminhos_dae_parcelamento) and bool(self.caminhos_parcelamento)
        self.botao_verificar_parcelamento.configure(state="normal" if habilitado else "disabled")

    def _perguntar_fontes_relatorio(self, fontes_disponiveis: list[str]) -> list[str] | None:
        janela = ctk.CTkToplevel(self)
        janela.title("Selecionar Busca(s)")
        janela.geometry("420x220")
        janela.transient(self)
        janela.grab_set()

        ctk.CTkLabel(
            janela,
            text="A planilha selecionada contém mais de uma origem de busca.\nEscolha o que deseja processar:",
            justify="left",
        ).pack(padx=16, pady=(16, 8), anchor="w")

        var_aquisicao = ctk.BooleanVar(value="aquisicao" in fontes_disponiveis)
        var_icms_at = ctk.BooleanVar(value=False)
        var_pagamento_dae = ctk.BooleanVar(value=False)

        if "aquisicao" in fontes_disponiveis:
            ctk.CTkCheckBox(janela, text="Aquisição (Notas Fiscais)", variable=var_aquisicao).pack(
                anchor="w", padx=24, pady=4
            )
        if "icms_at" in fontes_disponiveis:
            ctk.CTkCheckBox(
                janela, text="ICMS Antecipação Tributária (apuração mensal)", variable=var_icms_at
            ).pack(anchor="w", padx=24, pady=4)
        if "pagamento_dae" in fontes_disponiveis:
            ctk.CTkCheckBox(
                janela, text="Pagamentos/Parcelamentos (planilha DAE)", variable=var_pagamento_dae
            ).pack(anchor="w", padx=24, pady=4)

        resultado: list[str] = []

        def _confirmar() -> None:
            escolhidas = []
            if var_aquisicao.get():
                escolhidas.append("aquisicao")
            if var_icms_at.get():
                escolhidas.append("icms_at")
            if var_pagamento_dae.get():
                escolhidas.append("pagamento_dae")
            if not escolhidas:
                messagebox.showwarning("AuditaDAE", "Selecione ao menos uma opção.")
                return
            resultado.extend(escolhidas)
            janela.destroy()

        def _cancelar() -> None:
            janela.destroy()

        frame_botoes = ctk.CTkFrame(janela, fg_color="transparent")
        frame_botoes.pack(pady=16)
        ctk.CTkButton(frame_botoes, text="Confirmar", command=_confirmar).pack(side="left", padx=8)
        ctk.CTkButton(frame_botoes, text="Cancelar", command=_cancelar).pack(side="left", padx=8)

        janela.wait_window()
        return resultado if resultado else None

    def _processar(self) -> None:
        if not self.caminhos_dae:
            messagebox.showwarning("AuditaDAE", "Selecione ao menos um PDF de DAE.")
            return

        self.buscar_aquisicao_pendente = True
        self.buscar_icms_at_pendente = False
        self.buscar_pagamento_dae_pendente = False

        if self.caminho_relatorio is not None:
            fontes = detectar_fontes_relatorio(self.caminho_relatorio)
            if len(fontes) > 1:
                escolha = self._perguntar_fontes_relatorio(fontes)
                if escolha is None:
                    return
                self.buscar_aquisicao_pendente = "aquisicao" in escolha
                self.buscar_icms_at_pendente = "icms_at" in escolha
                self.buscar_pagamento_dae_pendente = "pagamento_dae" in escolha

        self.botao_processar.configure(state="disabled")
        self.barra_progresso.start()
        threading.Thread(target=self._processar_em_background, daemon=True).start()

    def _processar_em_background(self) -> None:
        try:
            resultado = processar_lote(
                self.caminhos_dae,
                self.caminho_relatorio,
                buscar_aquisicao=self.buscar_aquisicao_pendente,
                buscar_icms_at=self.buscar_icms_at_pendente,
                buscar_pagamento_dae=self.buscar_pagamento_dae_pendente,
            )
            self.after(0, self._processar_concluido, resultado, None)
        except Exception as erro:
            self.after(0, self._processar_concluido, None, erro)

    def _processar_concluido(
        self,
        resultado: ResultadoProcessamento | None,
        erro: Exception | None,
    ) -> None:
        self.barra_progresso.stop()
        self.botao_processar.configure(state="normal")
        if erro is not None:
            messagebox.showerror("AuditaDAE", f"Falha ao processar: {erro}")
            return

        self.ultima_conciliacao = resultado.conciliadas
        self.ultima_nao_encontradas = resultado.nao_encontradas
        self.ultimas_linhas_icms_at = resultado.linhas_icms_at
        self.ultimos_pagamentos_confirmados_planilha = resultado.pagamentos_confirmados
        self.ultimos_pagamentos_nao_localizados_planilha = resultado.pagamentos_nao_localizados
        self.ultimos_parcelamento_encontrados_planilha = resultado.parcelamento_encontrados
        self.ultimos_parcelamento_nao_encontrados_planilha = resultado.parcelamento_nao_encontrados

        self.buscar_aquisicao_pendente = self.caminho_relatorio is not None and self.buscar_aquisicao_pendente
        self._atualizar_grupos_visiveis_notas()

        if self.caminho_relatorio is None:
            messagebox.showinfo(
                "AuditaDAE",
                "DAE(s) processado(s) com sucesso.\n\n"
                "Nenhum relatório de notas fiscais foi selecionado — conciliação de notas não realizada.",
            )
            return

        resumo = []
        if self.buscar_aquisicao_pendente:
            resumo.append(
                f"Notas conciliadas: {len(resultado.conciliadas)}\n"
                f"Notas não encontradas: {len(resultado.nao_encontradas)}"
            )
        if self.buscar_icms_at_pendente:
            resumo.append(f"Meses de ICMS Antecipação Tributária processados: {len(resultado.linhas_icms_at)}")
        if self.buscar_pagamento_dae_pendente:
            resumo.append(
                f"Pagamentos confirmados (planilha): {len(resultado.pagamentos_confirmados)}\n"
                f"Pagamentos não localizados (planilha): {len(resultado.pagamentos_nao_localizados)}\n"
                f"Parcelamentos encontrados (planilha): {len(resultado.parcelamento_encontrados)}\n"
                f"Parcelamentos não encontrados (planilha): {len(resultado.parcelamento_nao_encontrados)}"
            )

        messagebox.showinfo("AuditaDAE", "Processamento concluído.\n\n" + "\n\n".join(resumo))
        self._atualizar_historico()

    def _atualizar_grupos_visiveis_notas(self) -> None:
        grupos = [
            (self.frame_grupo_aquisicao, self.buscar_aquisicao_pendente),
            (self.frame_grupo_icms_at, self.buscar_icms_at_pendente),
            (self.frame_grupo_pagamento_dae, self.buscar_pagamento_dae_pendente),
        ]
        for frame, _ in grupos:
            frame.pack_forget()
        for frame, visivel in grupos:
            if visivel:
                frame.pack(fill="x", padx=8, pady=(0, 8))

    def _gerar_excel_conciliadas(self) -> None:
        if not self.ultima_conciliacao:
            messagebox.showwarning("AuditaDAE", "Nenhuma nota conciliada para incluir na planilha.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar Relatório Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="relatorio_conciliadas.xlsx",
        )
        if not caminho:
            return

        try:
            gerar_relatorio_conciliadas(self.ultima_conciliacao, Path(caminho))
        except Exception as erro:
            messagebox.showerror("AuditaDAE", f"Falha ao gerar planilha: {erro}")
            return

        messagebox.showinfo("AuditaDAE", f"Relatório Excel gerado em:\n{caminho}")

    def _gerar_pdf(self) -> None:
        if not self.ultima_conciliacao:
            messagebox.showwarning("AuditaDAE", "Nenhuma nota conciliada para incluir no PDF.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar Relatório PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="relatorio_conciliadas.pdf",
        )
        if not caminho:
            return

        try:
            gerar_relatorio_conciliadas_pdf(self.ultima_conciliacao, Path(caminho))
        except Exception as erro:
            messagebox.showerror("AuditaDAE", f"Falha ao gerar PDF: {erro}")
            return

        messagebox.showinfo("AuditaDAE", f"Relatório PDF gerado em:\n{caminho}")

    def _gerar_pdf_nao_encontradas(self) -> None:
        if not self.ultima_nao_encontradas:
            messagebox.showwarning("AuditaDAE", "Nenhuma nota não encontrada para incluir no PDF.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar Relatório PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="relatorio_nao_encontradas.pdf",
        )
        if not caminho:
            return

        try:
            gerar_relatorio_nao_encontradas_pdf(self.ultima_nao_encontradas, Path(caminho))
        except Exception as erro:
            messagebox.showerror("AuditaDAE", f"Falha ao gerar PDF: {erro}")
            return

        messagebox.showinfo("AuditaDAE", f"Relatório PDF gerado em:\n{caminho}")

    def _gerar_excel_nao_encontradas(self) -> None:
        if not self.ultima_nao_encontradas:
            messagebox.showwarning("AuditaDAE", "Nenhuma nota não encontrada para incluir na planilha.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar Relatório Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="relatorio_nao_encontradas.xlsx",
        )
        if not caminho:
            return

        try:
            gerar_relatorio_nao_encontradas(self.ultima_nao_encontradas, Path(caminho))
        except Exception as erro:
            messagebox.showerror("AuditaDAE", f"Falha ao gerar planilha: {erro}")
            return

        messagebox.showinfo("AuditaDAE", f"Relatório Excel gerado em:\n{caminho}")

    def _gerar_excel_icms_at(self) -> None:
        if not self.ultimas_linhas_icms_at:
            messagebox.showwarning("AuditaDAE", "Nenhum dado de ICMS Antecipação Tributária para incluir na planilha.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar Relatório Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="relatorio_icms_at.xlsx",
        )
        if not caminho:
            return

        try:
            gerar_relatorio_icms_at_excel(self.ultimas_linhas_icms_at, Path(caminho))
        except Exception as erro:
            messagebox.showerror("AuditaDAE", f"Falha ao gerar planilha: {erro}")
            return

        messagebox.showinfo("AuditaDAE", f"Relatório Excel gerado em:\n{caminho}")

    def _gerar_pdf_icms_at(self) -> None:
        if not self.ultimas_linhas_icms_at:
            messagebox.showwarning("AuditaDAE", "Nenhum dado de ICMS Antecipação Tributária para incluir no PDF.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar Relatório PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="relatorio_icms_at.pdf",
        )
        if not caminho:
            return

        try:
            gerar_relatorio_icms_at_pdf(self.ultimas_linhas_icms_at, Path(caminho))
        except Exception as erro:
            messagebox.showerror("AuditaDAE", f"Falha ao gerar PDF: {erro}")
            return

        messagebox.showinfo("AuditaDAE", f"Relatório PDF gerado em:\n{caminho}")

    def _gerar_excel_pagamentos_planilha(self) -> None:
        if not self.ultimos_pagamentos_confirmados_planilha and not self.ultimos_pagamentos_nao_localizados_planilha:
            messagebox.showwarning("AuditaDAE", "Nenhum resultado de pagamentos (planilha) para incluir na planilha.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar Relatório de Pagamentos Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="relatorio_pagamentos_planilha.xlsx",
        )
        if not caminho:
            return

        try:
            gerar_relatorio_pagamentos_excel(
                self.ultimos_pagamentos_confirmados_planilha,
                self.ultimos_pagamentos_nao_localizados_planilha,
                Path(caminho),
            )
        except Exception as erro:
            messagebox.showerror("AuditaDAE", f"Falha ao gerar planilha: {erro}")
            return

        messagebox.showinfo("AuditaDAE", f"Relatório Excel gerado em:\n{caminho}")

    def _gerar_pdf_pagamentos_planilha(self) -> None:
        if not self.ultimos_pagamentos_confirmados_planilha and not self.ultimos_pagamentos_nao_localizados_planilha:
            messagebox.showwarning("AuditaDAE", "Nenhum resultado de pagamentos (planilha) para incluir no PDF.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar Relatório de Pagamentos PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="relatorio_pagamentos_planilha.pdf",
        )
        if not caminho:
            return

        try:
            gerar_relatorio_pagamentos_pdf(
                self.ultimos_pagamentos_confirmados_planilha,
                self.ultimos_pagamentos_nao_localizados_planilha,
                Path(caminho),
            )
        except Exception as erro:
            messagebox.showerror("AuditaDAE", f"Falha ao gerar PDF: {erro}")
            return

        messagebox.showinfo("AuditaDAE", f"Relatório PDF gerado em:\n{caminho}")

    def _gerar_excel_parcelamento_planilha(self) -> None:
        if not self.ultimos_parcelamento_encontrados_planilha and not self.ultimos_parcelamento_nao_encontrados_planilha:
            messagebox.showwarning("AuditaDAE", "Nenhum resultado de parcelamento (planilha) para incluir na planilha.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar Relatório de Parcelamento Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="relatorio_parcelamento_planilha.xlsx",
        )
        if not caminho:
            return

        try:
            gerar_relatorio_parcelamento_excel(
                self.ultimos_parcelamento_encontrados_planilha,
                self.ultimos_parcelamento_nao_encontrados_planilha,
                Path(caminho),
            )
        except Exception as erro:
            messagebox.showerror("AuditaDAE", f"Falha ao gerar planilha: {erro}")
            return

        messagebox.showinfo("AuditaDAE", f"Relatório Excel gerado em:\n{caminho}")

    def _gerar_pdf_parcelamento_planilha(self) -> None:
        if not self.ultimos_parcelamento_encontrados_planilha and not self.ultimos_parcelamento_nao_encontrados_planilha:
            messagebox.showwarning("AuditaDAE", "Nenhum resultado de parcelamento (planilha) para incluir no PDF.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar Relatório de Parcelamento PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="relatorio_parcelamento_planilha.pdf",
        )
        if not caminho:
            return

        try:
            gerar_relatorio_parcelamento_pdf(
                self.ultimos_parcelamento_encontrados_planilha,
                self.ultimos_parcelamento_nao_encontrados_planilha,
                Path(caminho),
            )
        except Exception as erro:
            messagebox.showerror("AuditaDAE", f"Falha ao gerar PDF: {erro}")
            return

        messagebox.showinfo("AuditaDAE", f"Relatório PDF gerado em:\n{caminho}")

    def _verificar_pagamentos(self) -> None:
        if not self.caminhos_dae_pagamentos:
            messagebox.showwarning("AuditaDAE", "Selecione ao menos um PDF de DAE.")
            return
        if not self.caminhos_relatorio_pagamento:
            messagebox.showwarning("AuditaDAE", "Selecione ao menos um relatório de pagamentos.")
            return

        self.botao_verificar_pagamentos.configure(state="disabled")
        self.barra_progresso.start()
        threading.Thread(target=self._verificar_pagamentos_em_background, daemon=True).start()

    def _verificar_pagamentos_em_background(self) -> None:
        try:
            resultado = verificar_pagamentos_lote(self.caminhos_dae_pagamentos, self.caminhos_relatorio_pagamento)
            self.after(0, self._verificar_pagamentos_concluido, resultado, None)
        except Exception as erro:
            self.after(0, self._verificar_pagamentos_concluido, None, erro)

    def _verificar_pagamentos_concluido(
        self,
        resultado: tuple[list[PagamentoConfirmado], list[DaePagamentoNaoLocalizado]] | None,
        erro: Exception | None,
    ) -> None:
        self.barra_progresso.stop()
        self._atualizar_estado_botao_pagamentos()
        if erro is not None:
            messagebox.showerror("AuditaDAE", f"Falha ao verificar pagamentos: {erro}")
            return

        confirmados, nao_localizados = resultado
        self.ultimos_pagamentos_confirmados = confirmados
        self.ultimos_pagamentos_nao_localizados = nao_localizados
        self.botao_gerar_excel_pagamentos.pack(side="left", padx=(8, 0))
        self.botao_gerar_pdf_pagamentos.pack(side="left", padx=(8, 0))

        messagebox.showinfo(
            "AuditaDAE",
            f"Verificação de pagamentos concluída.\n\nPagamentos confirmados: {len(confirmados)}\n"
            f"Não localizados: {len(nao_localizados)}",
        )

    def _gerar_excel_pagamentos(self) -> None:
        if not self.ultimos_pagamentos_confirmados and not self.ultimos_pagamentos_nao_localizados:
            messagebox.showwarning("AuditaDAE", "Nenhum resultado de verificação de pagamentos para incluir na planilha.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar Relatório de Pagamentos Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="relatorio_pagamentos.xlsx",
        )
        if not caminho:
            return

        try:
            gerar_relatorio_pagamentos_excel(
                self.ultimos_pagamentos_confirmados, self.ultimos_pagamentos_nao_localizados, Path(caminho)
            )
        except Exception as erro:
            messagebox.showerror("AuditaDAE", f"Falha ao gerar planilha: {erro}")
            return

        messagebox.showinfo("AuditaDAE", f"Relatório Excel gerado em:\n{caminho}")

    def _gerar_pdf_pagamentos(self) -> None:
        if not self.ultimos_pagamentos_confirmados and not self.ultimos_pagamentos_nao_localizados:
            messagebox.showwarning("AuditaDAE", "Nenhum resultado de verificação de pagamentos para incluir no PDF.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar Relatório de Pagamentos PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="relatorio_pagamentos.pdf",
        )
        if not caminho:
            return

        try:
            gerar_relatorio_pagamentos_pdf(
                self.ultimos_pagamentos_confirmados, self.ultimos_pagamentos_nao_localizados, Path(caminho)
            )
        except Exception as erro:
            messagebox.showerror("AuditaDAE", f"Falha ao gerar PDF: {erro}")
            return

        messagebox.showinfo("AuditaDAE", f"Relatório PDF gerado em:\n{caminho}")

    def _verificar_parcelamento(self) -> None:
        if not self.caminhos_dae_parcelamento:
            messagebox.showwarning("AuditaDAE", "Selecione ao menos um PDF de DAE.")
            return
        if not self.caminhos_parcelamento:
            messagebox.showwarning("AuditaDAE", "Selecione ao menos um relatório de parcelamento.")
            return

        self.botao_verificar_parcelamento.configure(state="disabled")
        self.barra_progresso.start()
        threading.Thread(target=self._verificar_parcelamento_em_background, daemon=True).start()

    def _verificar_parcelamento_em_background(self) -> None:
        try:
            resultado = verificar_parcelamento_lote(self.caminhos_dae_parcelamento, self.caminhos_parcelamento)
            self.after(0, self._verificar_parcelamento_concluido, resultado, None)
        except Exception as erro:
            self.after(0, self._verificar_parcelamento_concluido, None, erro)

    def _verificar_parcelamento_concluido(
        self,
        resultado: tuple[list[DaeParceladoEncontrado], list[DaeParceladoNaoEncontrado]] | None,
        erro: Exception | None,
    ) -> None:
        self.barra_progresso.stop()
        self._atualizar_estado_botao_parcelamento()
        if erro is not None:
            messagebox.showerror("AuditaDAE", f"Falha ao verificar parcelamentos: {erro}")
            return

        encontrados, nao_encontrados = resultado
        self.ultimos_parcelamento_encontrados = encontrados
        self.ultimos_parcelamento_nao_encontrados = nao_encontrados
        self.botao_gerar_excel_parcelamento.pack(side="left", padx=(8, 0))
        self.botao_gerar_pdf_parcelamento.pack(side="left", padx=(8, 0))

        messagebox.showinfo(
            "AuditaDAE",
            f"Verificação de parcelamentos concluída.\n\nDAEs encontrados: {len(encontrados)}\n"
            f"Não encontrados: {len(nao_encontrados)}",
        )

    def _gerar_excel_parcelamento(self) -> None:
        if not self.ultimos_parcelamento_encontrados and not self.ultimos_parcelamento_nao_encontrados:
            messagebox.showwarning("AuditaDAE", "Nenhum resultado de verificação de parcelamento para incluir na planilha.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar Relatório de Parcelamento Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="relatorio_parcelamento.xlsx",
        )
        if not caminho:
            return

        try:
            gerar_relatorio_parcelamento_excel(
                self.ultimos_parcelamento_encontrados, self.ultimos_parcelamento_nao_encontrados, Path(caminho)
            )
        except Exception as erro:
            messagebox.showerror("AuditaDAE", f"Falha ao gerar planilha: {erro}")
            return

        messagebox.showinfo("AuditaDAE", f"Relatório Excel gerado em:\n{caminho}")

    def _gerar_pdf_parcelamento(self) -> None:
        if not self.ultimos_parcelamento_encontrados and not self.ultimos_parcelamento_nao_encontrados:
            messagebox.showwarning("AuditaDAE", "Nenhum resultado de verificação de parcelamento para incluir no PDF.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar Relatório de Parcelamento PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="relatorio_parcelamento.pdf",
        )
        if not caminho:
            return

        try:
            gerar_relatorio_parcelamento_pdf(
                self.ultimos_parcelamento_encontrados, self.ultimos_parcelamento_nao_encontrados, Path(caminho)
            )
        except Exception as erro:
            messagebox.showerror("AuditaDAE", f"Falha ao gerar PDF: {erro}")
            return

        messagebox.showinfo("AuditaDAE", f"Relatório PDF gerado em:\n{caminho}")

    def _atualizar_historico(self) -> None:
        conexao = obter_conexao()
        try:
            registros = listar_historico(conexao, limite=50)
        finally:
            conexao.close()

        self.texto_historico.delete("1.0", "end")
        for registro in registros:
            linha = f"{registro.data_processamento:%d/%m/%Y %H:%M} — NF {registro.numero_nf} — {registro.status}\n"
            self.texto_historico.insert("end", linha)


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
