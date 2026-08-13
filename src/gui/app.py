import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

from src.db.database import obter_conexao
from src.db.repository import listar_historico
from src.main import processar_lote, verificar_pagamentos_lote
from src.models.dae_models import (
    DaeDocumento,
    DaePagamentoNaoLocalizado,
    NotaConciliada,
    NotaNaoEncontrada,
    PagamentoConfirmado,
)
from src.reports.report_generator import (
    gerar_relatorio_conciliadas_pdf,
    gerar_relatorio_nao_encontradas_pdf,
    gerar_relatorio_pagamentos_pdf,
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("AuditaDAE — Conciliação de ICMS")
        self.geometry("720x560")

        self.caminhos_dae: list[str] = []
        self.caminho_relatorio: str | None = None
        self.ultima_conciliacao: list[NotaConciliada] = []
        self.ultima_nao_encontradas: list[NotaNaoEncontrada] = []
        self.ultimos_daes: list[DaeDocumento] = []
        self.caminho_relatorio_pagamento: str | None = None
        self.ultimos_pagamentos_confirmados: list[PagamentoConfirmado] = []
        self.ultimos_pagamentos_nao_localizados: list[DaePagamentoNaoLocalizado] = []

        self._montar_layout()
        self._atualizar_historico()

    def _montar_layout(self) -> None:
        frame_dae = ctk.CTkFrame(self)
        frame_dae.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(frame_dae, text="DAE/DARF (PDF) — solte 1 ou mais arquivos aqui ou selecione").pack(anchor="w", padx=8, pady=(8, 0))
        self.lista_dae = ctk.CTkTextbox(frame_dae, height=90)
        self.lista_dae.pack(fill="x", padx=8, pady=8)
        self.lista_dae.drop_target_register(DND_FILES)
        self.lista_dae.dnd_bind("<<Drop>>", self._on_drop_dae)
        ctk.CTkButton(frame_dae, text="Selecionar PDF(s) de DAE", command=self._selecionar_daes).pack(padx=8, pady=(0, 8), anchor="w")

        frame_relatorio = ctk.CTkFrame(self)
        frame_relatorio.pack(fill="x", padx=16, pady=8)
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

        frame_relatorio_pagamento = ctk.CTkFrame(self)
        frame_relatorio_pagamento.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(frame_relatorio_pagamento, text="Relatório de Pagamentos de DAE (PDF)").pack(
            anchor="w", padx=8, pady=(8, 0)
        )
        self.label_relatorio_pagamento = ctk.CTkLabel(frame_relatorio_pagamento, text="Nenhum arquivo selecionado")
        self.label_relatorio_pagamento.pack(fill="x", padx=8, pady=4)
        ctk.CTkButton(
            frame_relatorio_pagamento,
            text="Selecionar Relatório de Pagamentos",
            command=self._selecionar_relatorio_pagamento,
        ).pack(padx=8, pady=(0, 8), anchor="w")

        self.barra_progresso = ctk.CTkProgressBar(self, mode="indeterminate")
        self.barra_progresso.pack(fill="x", padx=16, pady=8)

        frame_acoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_acoes.pack(fill="x", padx=16, pady=(0, 8))

        self.botao_processar = ctk.CTkButton(frame_acoes, text="Processar", command=self._processar)
        self.botao_processar.pack(side="left")

        self.botao_gerar_pdf = ctk.CTkButton(
            frame_acoes, text="Gerar Relatório PDF (Conciliadas)", command=self._gerar_pdf, state="disabled"
        )
        self.botao_gerar_pdf.pack(side="left", padx=(8, 0))

        self.botao_gerar_pdf_nao_encontradas = ctk.CTkButton(
            frame_acoes,
            text="Gerar Relatório PDF (Não Encontradas)",
            command=self._gerar_pdf_nao_encontradas,
            state="disabled",
        )
        self.botao_gerar_pdf_nao_encontradas.pack(side="left", padx=(8, 0))

        self.botao_verificar_pagamentos = ctk.CTkButton(
            frame_acoes,
            text="Verificar Pagamentos",
            command=self._verificar_pagamentos,
            state="disabled",
        )
        self.botao_verificar_pagamentos.pack(side="left", padx=(8, 0))

        self.botao_gerar_pdf_pagamentos = ctk.CTkButton(
            frame_acoes,
            text="Gerar Relatório de Pagamentos em PDF",
            command=self._gerar_pdf_pagamentos,
            state="disabled",
        )
        self.botao_gerar_pdf_pagamentos.pack(side="left", padx=(8, 0))

        frame_historico = ctk.CTkFrame(self)
        frame_historico.pack(fill="both", expand=True, padx=16, pady=(8, 16))
        ctk.CTkLabel(frame_historico, text="Histórico de Conciliações").pack(anchor="w", padx=8, pady=(8, 0))
        self.texto_historico = ctk.CTkTextbox(frame_historico)
        self.texto_historico.pack(fill="both", expand=True, padx=8, pady=8)

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

    def _selecionar_relatorio_pagamento(self) -> None:
        caminho = filedialog.askopenfilename(
            title="Selecionar Relatório de Pagamentos",
            filetypes=[("PDF", "*.pdf")],
        )
        if caminho:
            self.caminho_relatorio_pagamento = caminho
            self.label_relatorio_pagamento.configure(text=caminho)
            self._atualizar_estado_botao_pagamentos()

    def _atualizar_estado_botao_pagamentos(self) -> None:
        habilitado = bool(self.ultimos_daes) and bool(self.caminho_relatorio_pagamento)
        self.botao_verificar_pagamentos.configure(state="normal" if habilitado else "disabled")

    def _processar(self) -> None:
        if not self.caminhos_dae:
            messagebox.showwarning("AuditaDAE", "Selecione ao menos um PDF de DAE.")
            return

        self.botao_processar.configure(state="disabled")
        self.barra_progresso.start()
        threading.Thread(target=self._processar_em_background, daemon=True).start()

    def _processar_em_background(self) -> None:
        try:
            resultado = processar_lote(self.caminhos_dae, self.caminho_relatorio)
            self.after(0, self._processar_concluido, resultado, None)
        except Exception as erro:
            self.after(0, self._processar_concluido, None, erro)

    def _processar_concluido(
        self,
        resultado: tuple[Path | None, Path | None, list[NotaConciliada], list[NotaNaoEncontrada], list[DaeDocumento]]
        | None,
        erro: Exception | None,
    ) -> None:
        self.barra_progresso.stop()
        self.botao_processar.configure(state="normal")
        if erro is not None:
            messagebox.showerror("AuditaDAE", f"Falha ao processar: {erro}")
            return

        caminho_conciliadas, caminho_nao_encontradas, conciliadas, nao_encontradas, daes = resultado
        self.ultima_conciliacao = conciliadas
        self.ultima_nao_encontradas = nao_encontradas
        self.ultimos_daes = daes
        self._atualizar_estado_botao_pagamentos()

        if caminho_conciliadas is None:
            self.botao_gerar_pdf.configure(state="disabled")
            self.botao_gerar_pdf_nao_encontradas.configure(state="disabled")
            messagebox.showinfo(
                "AuditaDAE",
                "DAE(s) processado(s) com sucesso.\n\n"
                "Nenhum relatório de notas fiscais foi selecionado — conciliação de notas não realizada.",
            )
            return

        self.botao_gerar_pdf.configure(state="normal")
        self.botao_gerar_pdf_nao_encontradas.configure(state="normal")

        messagebox.showinfo(
            "AuditaDAE",
            f"Processamento concluído.\n\nRelatório de conciliadas: {caminho_conciliadas}\n"
            f"Relatório de não encontradas: {caminho_nao_encontradas}",
        )
        self._atualizar_historico()

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

    def _verificar_pagamentos(self) -> None:
        if not self.ultimos_daes:
            messagebox.showwarning("AuditaDAE", "Processe ao menos um DAE antes de verificar pagamentos.")
            return
        if not self.caminho_relatorio_pagamento:
            messagebox.showwarning("AuditaDAE", "Selecione o relatório de pagamentos.")
            return

        self.botao_verificar_pagamentos.configure(state="disabled")
        self.barra_progresso.start()
        threading.Thread(target=self._verificar_pagamentos_em_background, daemon=True).start()

    def _verificar_pagamentos_em_background(self) -> None:
        try:
            resultado = verificar_pagamentos_lote(self.ultimos_daes, self.caminho_relatorio_pagamento)
            self.after(0, self._verificar_pagamentos_concluido, resultado, None)
        except Exception as erro:
            self.after(0, self._verificar_pagamentos_concluido, None, erro)

    def _verificar_pagamentos_concluido(
        self,
        resultado: tuple[Path, Path, list[PagamentoConfirmado], list[DaePagamentoNaoLocalizado]] | None,
        erro: Exception | None,
    ) -> None:
        self.barra_progresso.stop()
        self._atualizar_estado_botao_pagamentos()
        if erro is not None:
            messagebox.showerror("AuditaDAE", f"Falha ao verificar pagamentos: {erro}")
            return

        caminho_confirmados, caminho_nao_localizados, confirmados, nao_localizados = resultado
        self.ultimos_pagamentos_confirmados = confirmados
        self.ultimos_pagamentos_nao_localizados = nao_localizados
        self.botao_gerar_pdf_pagamentos.configure(state="normal")

        messagebox.showinfo(
            "AuditaDAE",
            f"Verificação de pagamentos concluída.\n\nPagamentos confirmados: {caminho_confirmados}\n"
            f"Não localizados: {caminho_nao_localizados}",
        )

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
