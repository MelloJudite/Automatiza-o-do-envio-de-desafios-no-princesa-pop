import queue
import random
import threading
import time
import traceback
import unicodedata
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox

from selenium.webdriver.common.by import By
from selenium.webdriver.common.selenium_manager import SeleniumManager
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxWebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


COR_ROSA = "#FFB5C0"
COR_ROSA_ESCURO = "#D96B7B"
COR_BRANCO = "#FFFFFF"
COR_FUNDO = "#FFF6F8"
COR_CAMPO = "#FFE3E8"
COR_BORDA = "#F4A3AF"
COR_TEXTO = "#4B2C34"
RAIO_BORDA = 18
LARGURA_MAX_FORMULARIO = 700


def desenhar_retangulo_arredondado(canvas, x1, y1, x2, y2, raio, **kwargs):
    pontos = [
        x1 + raio,
        y1,
        x2 - raio,
        y1,
        x2,
        y1,
        x2,
        y1 + raio,
        x2,
        y2 - raio,
        x2,
        y2,
        x2 - raio,
        y2,
        x1 + raio,
        y2,
        x1,
        y2,
        x1,
        y2 - raio,
        x1,
        y1 + raio,
        x1,
        y1,
    ]
    return canvas.create_polygon(pontos, smooth=True, splinesteps=24, **kwargs)


class RoundedFrame(tk.Frame):
    def __init__(
        self,
        master,
        background=COR_FUNDO,
        fill=COR_BRANCO,
        radius=RAIO_BORDA,
        padding=16,
        outline="",
        **kwargs,
    ):
        super().__init__(master, bg=background, **kwargs)
        self.background = background
        self.fill = fill
        self.radius = radius
        self.outline = outline

        if isinstance(padding, tuple):
            self.padx, self.pady = padding
        else:
            self.padx = padding
            self.pady = padding

        self.canvas = tk.Canvas(
            self,
            bg=background,
            bd=0,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.inner = tk.Frame(self.canvas, bg=fill)
        self.window_id = self.canvas.create_window(
            self.padx,
            self.pady,
            anchor="nw",
            window=self.inner,
        )
        self.shape_id = None

        self.canvas.bind("<Configure>", self._redraw)
        self.inner.bind("<Configure>", self._sync_size)

    def _sync_size(self, _event=None):
        width = self.inner.winfo_reqwidth() + self.padx * 2
        height = self.inner.winfo_reqheight() + self.pady * 2
        self.canvas.configure(width=width, height=height)

    def _redraw(self, _event=None):
        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())
        self.canvas.delete("shape")
        self.shape_id = desenhar_retangulo_arredondado(
            self.canvas,
            1,
            1,
            width - 1,
            height - 1,
            self.radius,
            fill=self.fill,
            outline=self.outline,
            tags="shape",
        )
        self.canvas.tag_lower(self.shape_id)
        self.canvas.coords(self.window_id, self.padx, self.pady)
        self.canvas.itemconfigure(
            self.window_id,
            width=max(1, width - self.padx * 2),
            height=max(1, height - self.pady * 2),
        )


class RoundedButton(tk.Canvas):
    def __init__(
        self,
        master,
        text,
        command,
        background=COR_FUNDO,
        fill=COR_ROSA,
        active_fill=COR_ROSA_ESCURO,
        disabled_fill="#F8D1D8",
        foreground=COR_TEXTO,
        radius=16,
        padx=22,
        pady=10,
        **kwargs,
    ):
        super().__init__(
            master,
            bg=background,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            **kwargs,
        )
        self.text = text
        self.command = command
        self.fill = fill
        self.active_fill = active_fill
        self.disabled_fill = disabled_fill
        self.foreground = foreground
        self.radius = radius
        self.padx = padx
        self.pady = pady
        self.state = "normal"
        self.hover = False
        self.font = tkfont.Font(family="Segoe UI", size=10, weight="bold")

        self.bind("<Configure>", self._draw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_click)
        self._resize()

    def _resize(self):
        width = self.font.measure(self.text) + self.padx * 2
        height = self.font.metrics("linespace") + self.pady * 2
        tk.Canvas.configure(self, width=width, height=height)

    def _draw(self, _event=None):
        self.delete("all")
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        fill = self.active_fill if self.hover and self.state != "disabled" else self.fill
        texto = self.foreground

        if self.state == "disabled":
            fill = self.disabled_fill
            texto = "#9B6D75"

        desenhar_retangulo_arredondado(
            self,
            1,
            1,
            width - 1,
            height - 1,
            self.radius,
            fill=fill,
            outline="",
        )
        self.create_text(
            width / 2,
            height / 2,
            text=self.text,
            fill=texto,
            font=self.font,
        )

    def _on_enter(self, _event=None):
        self.hover = True
        self._draw()

    def _on_leave(self, _event=None):
        self.hover = False
        self._draw()

    def _on_click(self, _event=None):
        if self.state != "disabled" and self.command:
            self.command()

    def configure(self, cnf=None, **kwargs):
        if cnf:
            kwargs.update(cnf)

        if "text" in kwargs:
            self.text = kwargs.pop("text")
            self._resize()

        if "command" in kwargs:
            self.command = kwargs.pop("command")

        if "state" in kwargs:
            self.state = kwargs.pop("state")
            self.configure(cursor="arrow" if self.state == "disabled" else "hand2")

        if kwargs:
            tk.Canvas.configure(self, **kwargs)

        self._draw()

    config = configure


class RoundedEntry(tk.Frame):
    def __init__(
        self,
        master,
        textvariable,
        show=None,
        background=COR_BRANCO,
        fill=COR_CAMPO,
        radius=14,
        **kwargs,
    ):
        super().__init__(master, bg=background, **kwargs)
        self.fill = fill
        self.radius = radius
        self.canvas = tk.Canvas(
            self,
            bg=background,
            bd=0,
            highlightthickness=0,
            height=38,
        )
        self.canvas.pack(fill="both", expand=True)
        self.entry = tk.Entry(
            self.canvas,
            textvariable=textvariable,
            show=show,
            bg=fill,
            fg=COR_TEXTO,
            insertbackground=COR_TEXTO,
            relief="flat",
            font=("Segoe UI", 11),
        )
        self.window_id = self.canvas.create_window(14, 8, anchor="nw", window=self.entry)
        self.canvas.bind("<Configure>", self._redraw)
        self.canvas.bind("<Button-1>", lambda _event: self.entry.focus_set())

    def _redraw(self, _event=None):
        width = max(1, self.canvas.winfo_width())
        height = max(38, self.canvas.winfo_height())
        self.canvas.delete("shape")
        shape_id = desenhar_retangulo_arredondado(
            self.canvas,
            1,
            1,
            width - 1,
            height - 1,
            self.radius,
            fill=self.fill,
            outline=COR_BORDA,
            tags="shape",
        )
        self.canvas.tag_lower(shape_id)
        self.canvas.coords(self.window_id, 14, 8)
        self.canvas.itemconfigure(
            self.window_id,
            width=max(1, width - 28),
            height=max(1, height - 16),
        )

    def focus_set(self):
        self.entry.focus_set()


class RoundedProgressBar(tk.Canvas):
    def __init__(
        self,
        master,
        variable,
        maximum=100,
        background=COR_BRANCO,
        fill=COR_ROSA,
        trough=COR_CAMPO,
        height=18,
        radius=9,
        **kwargs,
    ):
        super().__init__(
            master,
            bg=background,
            bd=0,
            highlightthickness=0,
            height=height,
            **kwargs,
        )
        self.variable = variable
        self.maximum = maximum
        self.fill = fill
        self.trough = trough
        self.height = height
        self.radius = radius
        self.mode = "determinate"
        self.running = False
        self.phase = 0
        self.after_id = None
        self.variable.trace_add("write", lambda *_args: self._draw())
        self.bind("<Configure>", self._draw)

    def _draw(self, _event=None):
        self.delete("all")
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        desenhar_retangulo_arredondado(
            self,
            1,
            1,
            width - 1,
            height - 1,
            self.radius,
            fill=self.trough,
            outline="",
        )

        if self.mode == "indeterminate":
            segment = max(60, width * 0.35)
            x1 = (self.phase % (width + segment)) - segment
            x2 = min(width - 1, x1 + segment)
            x1 = max(1, x1)
        else:
            value = min(max(self.variable.get(), 0), self.maximum)
            x1 = 1
            x2 = max(1, width * (value / self.maximum))

        if x2 > x1:
            desenhar_retangulo_arredondado(
                self,
                x1,
                1,
                x2,
                height - 1,
                self.radius,
                fill=self.fill,
                outline="",
            )

    def configure(self, cnf=None, **kwargs):
        if cnf:
            kwargs.update(cnf)

        if "mode" in kwargs:
            self.mode = kwargs.pop("mode")

        if kwargs:
            tk.Canvas.configure(self, **kwargs)

        self._draw()

    config = configure

    def start(self, interval=12):
        self.running = True
        self._tick(interval)

    def _tick(self, interval):
        if not self.running:
            return

        self.phase += 8
        self._draw()
        self.after_id = self.after(interval, lambda: self._tick(interval))

    def stop(self):
        self.running = False
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None


class BotErroFatal(Exception):
    def __init__(self, mensagem, desafios, rastreamento):
        super().__init__(mensagem)
        self.desafios = desafios
        self.rastreamento = rastreamento


def preparar_dependencias(callback=None):
    def avisar(progresso, mensagem, ocupado=False):
        if callback is not None:
            callback(progresso, mensagem, ocupado)

    avisar(10, "Verificando componentes do executavel...")
    time.sleep(0.2)

    try:
        avisar(35, "Baixando ou reutilizando Firefox e geckodriver...", True)
        caminhos = SeleniumManager().binary_paths(["--browser", "firefox"])
    except Exception:
        avisar(45, "Firefox nao encontrado. Baixando navegador gerenciado...", True)
        caminhos = SeleniumManager().binary_paths(
            [
                "--browser",
                "firefox",
                "--browser-version",
                "esr",
                "--force-browser-download",
            ]
        )

    avisar(85, "Validando arquivos preparados...")

    driver_path = caminhos.get("driver_path", "")
    browser_path = caminhos.get("browser_path", "")

    if not driver_path or not Path(driver_path).is_file():
        raise RuntimeError("Nao foi possivel preparar o geckodriver.")

    if not browser_path or not Path(browser_path).is_file():
        raise RuntimeError("Nao foi possivel preparar o Firefox.")

    avisar(100, "Dependencias prontas.")
    return {"driver_path": driver_path, "browser_path": browser_path}


def criar_driver_firefox(dependencias):
    service = None
    options = FirefoxOptions()

    if dependencias:
        driver_path = dependencias.get("driver_path")
        browser_path = dependencias.get("browser_path")

        if driver_path:
            service = FirefoxService(executable_path=driver_path)

        if browser_path:
            options.binary_location = browser_path

    return FirefoxWebDriver(service=service, options=options)


def extrair_numero(texto):
    return int(texto.replace("AP", "").replace(" ", "").strip())


def pegar_ap(texto):
    for linha in texto.split("\n"):
        if "AP" in linha:
            return int(linha.replace("AP", "").replace(" ", ""))
    return None


def normalizar_texto(texto):
    texto_sem_acento = unicodedata.normalize("NFKD", texto)
    texto_ascii = texto_sem_acento.encode("ascii", "ignore").decode("ascii")
    return texto_ascii.lower()


def fechar_cookies(driver):
    wait = WebDriverWait(driver, 10)

    try:
        botao = wait.until(
            EC.element_to_be_clickable((By.ID, "cookiescript_accept"))
        )

        driver.execute_script("arguments[0].click();", botao)

        wait.until(
            EC.invisibility_of_element_located((By.ID, "cookiescript_buttons"))
        )
        print("Banner de cookies fechado com sucesso.")

    except Exception:
        print("Banner de cookies nao apareceu ou ja foi fechado.")


def verificar_popup(driver):
    try:
        popup = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#notification-center p"))
        )

        texto = normalizar_texto(popup.text)

        if "ja enviou um desafio" in texto:
            return "erro"

        if "lancou um desafio" in texto:
            return "sucesso"

        if "desafio entre estes dois" in texto:
            return "ip"

        if "voce atingiu o limite diario" in texto:
            return "limite"

        return "outro"

    except Exception:
        return None


def executar_bot(email_login, senha_login, dependencias=None):
    if not email_login or not senha_login:
        raise ValueError("Informe email e senha para iniciar.")

    driver = None
    i = 0

    try:
        driver = criar_driver_firefox(dependencias)
        wait = WebDriverWait(driver, 15)

        driver.get("https://www.princesapop.com")

        email = wait.until(
            EC.presence_of_element_located((By.ID, "email_connexion_mabimbo"))
        )
        email.send_keys(email_login)

        senha = driver.find_element(By.ID, "password_connexion_mabimbo")
        senha.send_keys(senha_login)

        senha.submit()
        print("Login efetuado com sucesso.")

        fechar_cookies(driver)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".left img")))

        driver.find_element(By.CSS_SELECTOR, ".left img").click()

        while i < 100:
            stats = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".stats"))
            ).text
            span = wait.until(
                EC.presence_of_element_located((By.XPATH, "//span[@name='ba']"))
            ).text

            valor_stats = pegar_ap(stats)
            valor_span = extrair_numero(span)

            if valor_stats is None:
                print("Erro ao pegar AP, pulando...")
                time.sleep(2)
                continue

            if valor_span > valor_stats:
                print("Princesa elegivel a desafio.")
                try:
                    wait.until(
                        EC.invisibility_of_element_located((By.ID, "notification-center"))
                    )
                except Exception:
                    pass

                wait.until(
                    EC.element_to_be_clickable((By.LINK_TEXT, "Enviar um desafio"))
                ).click()
                time.sleep(random.uniform(1, 2))

                wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "#btn-challenge-without-stake > .btn")
                    )
                ).click()
                time.sleep(random.uniform(1, 2))

                try:
                    wait.until(
                        EC.visibility_of_element_located(
                            (By.CSS_SELECTOR, "#notification-center p")
                        )
                    )
                except Exception:
                    pass

                resultado_popup = verificar_popup(driver)

                if resultado_popup == "erro":
                    print("Ja desafiou anteriormente, pulando princesa...")
                elif resultado_popup == "sucesso":
                    print("Desafio enviado com sucesso, passando princesa...")
                    i += 1
                    print(f"Faltam {100 - i} princesas para serem desafiadas hoje.")
                elif resultado_popup == "ip":
                    print("Essa princesa ja foi desafiada nesse mesmo IP, pulando princesa...")
                elif resultado_popup == "limite":
                    print("Voce atingiu o limite diario de desafios, encerrando o programa.")
                    break
                else:
                    print("Popup inesperado")

                wait.until(
                    EC.invisibility_of_element_located((By.ID, "notification-center"))
                )

                wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".left img"))
                ).click()

            else:
                print("Princesa nao elegivel a desafio, voce perderia.")
                wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".left img"))
                ).click()

            time.sleep(random.uniform(2, 5))

            if i % 10 == 0 and i != 0:
                time.sleep(random.uniform(10, 20))

        print(f"Encerrando programa, {i} princesas desafiadas")
        return i

    except Exception as erro:
        raise BotErroFatal(str(erro), i, traceback.format_exc()) from erro

    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


class QueueWriter:
    def __init__(self, fila):
        self.fila = fila

    def write(self, texto):
        if texto:
            self.fila.put(texto)

    def flush(self):
        pass


class InterfaceApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.fila_logs = queue.Queue()
        self.fila_dependencias = queue.Queue()
        self.thread_bot = None
        self.thread_dependencias = None
        self.dependencias = None
        self.barra_dependencias_ocupada = False

        self.title("Princesa Pop - Desafios")
        self.geometry("760x560")
        self.minsize(640, 480)
        self.configure(bg=COR_FUNDO)

        self.email_var = tk.StringVar()
        self.senha_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.dep_status_var = tk.StringVar(value="Aguardando inicio...")
        self.dep_progress_var = tk.DoubleVar(value=0)
        self.encerramento_titulo_var = tk.StringVar()
        self.encerramento_resumo_var = tk.StringVar()

        self._configurar_estilo()
        self._montar_layout()
        self._mostrar_tela_boas_vindas()
        self.after(100, self._processar_dependencias)
        self.after(100, self._processar_logs)

    def _configurar_estilo(self):
        pass

    def _montar_layout(self):
        self.container = tk.Frame(self, bg=COR_FUNDO, padx=42, pady=60)
        self.container.pack(fill="both", expand=True)

        self.tela_boas_vindas = tk.Frame(self.container, bg=COR_FUNDO)
        self.tela_dependencias = tk.Frame(self.container, bg=COR_FUNDO)
        self.tela_login = tk.Frame(self.container, bg=COR_FUNDO)
        self.tela_mensagens = tk.Frame(self.container, bg=COR_FUNDO)
        self.tela_encerramento = tk.Frame(self.container, bg=COR_FUNDO)

        self._montar_tela_boas_vindas()
        self._montar_tela_dependencias()
        self._montar_tela_login()
        self._montar_tela_mensagens()
        self._montar_tela_encerramento()

    def _montar_tela_boas_vindas(self):
        titulo = tk.Label(
            self.tela_boas_vindas,
            text="Bot de desafios do Princesa pop",
            bg=COR_FUNDO,
            fg=COR_TEXTO,
            justify="center",
            wraplength=650,
            font=("Segoe UI", 26, "bold"),
        )
        titulo.pack(anchor="center", fill="x")

        mensagem = tk.Label(
            self.tela_boas_vindas,
            text=
                "Esse bot foi feito com propósito de facilitar a subida de níveis no jogo, não abuse dele pois pode causar banimento.\n\n"
                "Feito por Judite Mello.",
            bg=COR_FUNDO,
            fg=COR_TEXTO,
            justify="center",
            wraplength=620,
            font=("Segoe UI", 13),
        )
        mensagem.pack(anchor="center", pady=(30, 44))

        self._criar_botao(
            self.tela_boas_vindas,
            "Avançar",
            self._iniciar_preparacao_dependencias,
        ).pack(anchor="center")

    def _montar_tela_dependencias(self):
        titulo = tk.Label(
            self.tela_dependencias,
            text="Preparando dependencias",
            bg=COR_FUNDO,
            fg=COR_TEXTO,
            justify="center",
            wraplength=650,
            font=("Segoe UI", 22, "bold"),
        )
        titulo.pack(anchor="center", fill="x")

        mensagem = tk.Label(
            self.tela_dependencias,
            text=(
                "Baixando dependências para o funcionamento do programa."
            ),
            bg=COR_FUNDO,
            fg=COR_TEXTO,
            justify="center",
            wraplength=620,
            font=("Segoe UI", 10),
        )
        mensagem.pack(anchor="center", pady=(16, 34))

        painel_container = self._criar_painel(self.tela_dependencias, padding=(18, 18))
        painel_container.pack(fill="x", pady=(12, 0))
        self._limitar_largura(
            painel_container,
            self.tela_dependencias,
            LARGURA_MAX_FORMULARIO,
        )
        painel = painel_container.inner

        status = tk.Label(
            painel,
            textvariable=self.dep_status_var,
            bg=COR_BRANCO,
            fg=COR_TEXTO,
            justify="center",
            font=("Segoe UI", 10, "bold"),
        )
        status.pack(anchor="center", pady=(0, 12))

        self.barra_dependencias = RoundedProgressBar(
            painel,
            variable=self.dep_progress_var,
            maximum=100,
            background=COR_BRANCO,
        )
        self.barra_dependencias.pack(fill="x")

    def _montar_tela_login(self):
        titulo = tk.Label(
            self.tela_login,
            text="Preencha com seu login do princesa pop",
            bg=COR_FUNDO,
            fg=COR_TEXTO,
            justify="center",
            wraplength=650,
            font=("Segoe UI", 22, "bold"),
        )
        titulo.pack(anchor="center", fill="x")

        formulario_container = self._criar_painel(self.tela_login, padding=(22, 22))
        formulario_container.pack(fill="x", pady=(36, 0))
        self._limitar_largura(
            formulario_container,
            self.tela_login,
            LARGURA_MAX_FORMULARIO,
        )
        formulario = formulario_container.inner

        self._criar_label(formulario, "Email").pack(anchor="w", padx=(4, 0), pady=(0, 8))
        email_entry = self._criar_entry(formulario, self.email_var)
        email_entry.pack(fill="x", pady=(0, 22))

        self._criar_label(formulario, "Senha").pack(anchor="w", padx=(4, 0), pady=(0, 8))
        senha_entry = self._criar_entry(formulario, self.senha_var, show="*")
        senha_entry.pack(fill="x")

        acoes = tk.Frame(self.tela_login, bg=COR_FUNDO)
        acoes.pack(fill="x", pady=30)

        self.botao_iniciar = self._criar_botao(
            acoes,
            "Iniciar",
            self._iniciar_bot,
        )
        self.botao_iniciar.pack(anchor="center")

    def _montar_tela_mensagens(self):
        cabecalho = tk.Frame(self.tela_mensagens, bg=COR_FUNDO)
        cabecalho.pack(fill="x")

        subtitulo = tk.Label(
            cabecalho,
            text="Acompanhe por aqui ou pelo firefox",
            bg=COR_FUNDO,
            fg=COR_TEXTO,
            justify="center",
            font=("Segoe UI", 13),
        )
        subtitulo.pack(anchor="center", pady=(0, 18))

        status = tk.Label(
            cabecalho,
            textvariable=self.status_var,
            bg=COR_FUNDO,
            fg=COR_TEXTO,
            justify="center",
            font=("Segoe UI", 10),
        )
        status.pack(anchor="center", pady=(0, 26))

        logs_container = self._criar_painel(self.tela_mensagens, padding=(12, 12))
        logs_container.pack(fill="both", expand=True)
        logs_frame = logs_container.inner

        self.logs_texto = tk.Text(
            logs_frame,
            bg=COR_BRANCO,
            fg=COR_TEXTO,
            insertbackground=COR_TEXTO,
            relief="flat",
            wrap="word",
            height=12,
            font=("Consolas", 10),
        )
        self.logs_texto.pack(side="left", fill="both", expand=True)
        self.logs_texto.configure(state="disabled")

        scroll = tk.Scrollbar(
            logs_frame,
            command=self.logs_texto.yview,
            relief="flat",
            bd=0,
            width=12,
            bg=COR_ROSA,
            activebackground=COR_ROSA_ESCURO,
            troughcolor=COR_CAMPO,
        )
        scroll.pack(side="right", fill="y")
        self.logs_texto.configure(yscrollcommand=scroll.set)

    def _montar_tela_encerramento(self):
        titulo = tk.Label(
            self.tela_encerramento,
            textvariable=self.encerramento_titulo_var,
            bg=COR_FUNDO,
            fg=COR_TEXTO,
            justify="center",
            wraplength=650,
            font=("Segoe UI", 22, "bold"),
        )
        titulo.pack(anchor="center", fill="x")

        resumo = tk.Label(
            self.tela_encerramento,
            textvariable=self.encerramento_resumo_var,
            bg=COR_FUNDO,
            fg=COR_TEXTO,
            justify="center",
            wraplength=650,
            font=("Segoe UI", 12),
        )
        resumo.pack(anchor="center", pady=(20, 32))

        detalhes_container = self._criar_painel(self.tela_encerramento, padding=(12, 12))
        detalhes_container.pack(fill="both", expand=True)
        detalhes_frame = detalhes_container.inner

        self.encerramento_detalhes = tk.Text(
            detalhes_frame,
            bg=COR_BRANCO,
            fg=COR_TEXTO,
            relief="flat",
            wrap="word",
            height=10,
            font=("Consolas", 10),
        )
        self.encerramento_detalhes.pack(side="left", fill="both", expand=True)
        self.encerramento_detalhes.configure(state="disabled")

        scroll = tk.Scrollbar(
            detalhes_frame,
            command=self.encerramento_detalhes.yview,
            relief="flat",
            bd=0,
            width=12,
            bg=COR_ROSA,
            activebackground=COR_ROSA_ESCURO,
            troughcolor=COR_CAMPO,
        )
        scroll.pack(side="right", fill="y")
        self.encerramento_detalhes.configure(yscrollcommand=scroll.set)

        acoes = tk.Frame(self.tela_encerramento, bg=COR_FUNDO)
        acoes.pack(fill="x", pady=(18, 0))

        botoes = tk.Frame(acoes, bg=COR_FUNDO)
        botoes.pack(anchor="center")

        self.botao_final_acao = self._criar_botao(
            botoes,
            "Novo login",
            self._voltar_para_login,
        )
        self.botao_final_acao.pack(side="left")

        self._criar_botao(botoes, "Fechar", self.destroy).pack(side="left", padx=(12, 0))

    def _ocultar_telas(self):
        for tela in (
            self.tela_boas_vindas,
            self.tela_dependencias,
            self.tela_login,
            self.tela_mensagens,
            self.tela_encerramento,
        ):
            tela.pack_forget()

    def _mostrar_tela_boas_vindas(self):
        self._ocultar_telas()
        self.tela_boas_vindas.pack(fill="both", expand=True)

    def _mostrar_tela_dependencias(self):
        self._ocultar_telas()
        self.tela_dependencias.pack(fill="both", expand=True)

    def _mostrar_tela_login(self):
        self._ocultar_telas()
        self.botao_iniciar.configure(state="normal", text="Iniciar")
        self.status_var.set("")
        self.tela_login.pack(fill="both", expand=True)

    def _mostrar_tela_mensagens(self):
        self._ocultar_telas()
        self.tela_mensagens.pack(fill="both", expand=True)

    def _mostrar_tela_encerramento(self, sucesso, desafios=0, erro=None):
        self._ocultar_telas()

        if sucesso:
            self.encerramento_titulo_var.set("Execucao concluida")
            self.encerramento_resumo_var.set(f"Desafios lancados: {desafios}")
            detalhes = "Programa finalizado sem erro fatal."
            self.botao_final_acao.configure(text="Novo login", command=self._voltar_para_login)
        else:
            self.encerramento_titulo_var.set("Erro fatal")
            self.encerramento_resumo_var.set(
                f"Desafios lancados antes do erro: {desafios}"
            )
            detalhes = erro or "Erro fatal nao especificado."

            if self.dependencias:
                self.botao_final_acao.configure(
                    text="Voltar ao login",
                    command=self._voltar_para_login,
                )
            else:
                self.botao_final_acao.configure(
                    text="Tentar novamente",
                    command=self._iniciar_preparacao_dependencias,
                )

        self._preencher_detalhes_encerramento(detalhes)
        self.tela_encerramento.pack(fill="both", expand=True)

    def _preencher_detalhes_encerramento(self, detalhes):
        self.encerramento_detalhes.configure(state="normal")
        self.encerramento_detalhes.delete("1.0", "end")
        self.encerramento_detalhes.insert("end", detalhes)
        self.encerramento_detalhes.see("1.0")
        self.encerramento_detalhes.configure(state="disabled")

    def _criar_label(self, parent, texto):
        return tk.Label(
            parent,
            text=texto,
            bg=COR_BRANCO,
            fg=COR_TEXTO,
            justify="center",
            font=("Segoe UI", 10, "bold"),
        )

    def _criar_entry(self, parent, variavel, show=None):
        return RoundedEntry(
            parent,
            textvariable=variavel,
            show=show,
            background=COR_BRANCO,
            fill=COR_CAMPO,
        )

    def _criar_botao(self, parent, texto, comando):
        return RoundedButton(
            parent,
            text=texto,
            command=comando,
            background=COR_FUNDO,
        )

    def _criar_painel(self, parent, padding=16):
        return RoundedFrame(
            parent,
            background=COR_FUNDO,
            fill=COR_BRANCO,
            radius=RAIO_BORDA,
            padding=padding,
        )

    def _limitar_largura(self, widget, parent, largura_maxima):
        def ajustar(_event=None):
            largura_disponivel = max(parent.winfo_width(), 1)
            margem = max((largura_disponivel - largura_maxima) // 2, 0)
            widget.pack_configure(padx=margem)

        parent.bind("<Configure>", ajustar, add="+")
        self.after(50, ajustar)

    def _iniciar_preparacao_dependencias(self):
        if self.thread_dependencias and self.thread_dependencias.is_alive():
            return

        self._mostrar_tela_dependencias()
        self.dep_progress_var.set(0)
        self.dep_status_var.set("Iniciando preparacao...")
        self._parar_barra_dependencias()

        if self.dependencias:
            self.dep_progress_var.set(100)
            self.dep_status_var.set("Dependencias prontas.")
            self.after(500, self._mostrar_tela_login)
            return

        self.thread_dependencias = threading.Thread(
            target=self._rodar_dependencias_em_thread,
            daemon=True,
        )
        self.thread_dependencias.start()

    def _rodar_dependencias_em_thread(self):
        try:
            dependencias = preparar_dependencias(
                lambda progresso, mensagem, ocupado=False: self.fila_dependencias.put(
                    ("PROGRESSO", progresso, mensagem, ocupado)
                )
            )
            self.fila_dependencias.put(("FIM", dependencias))
        except Exception:
            self.fila_dependencias.put(("ERRO", traceback.format_exc()))

    def _processar_dependencias(self):
        while True:
            try:
                evento = self.fila_dependencias.get_nowait()
            except queue.Empty:
                break

            tipo = evento[0]

            if tipo == "PROGRESSO":
                _, progresso, mensagem, ocupado = evento
                self.dep_status_var.set(mensagem)

                if ocupado:
                    self._iniciar_barra_dependencias()
                else:
                    self._parar_barra_dependencias()
                    self.dep_progress_var.set(progresso)

            elif tipo == "FIM":
                _, dependencias = evento
                self.dependencias = dependencias
                self._parar_barra_dependencias()
                self.dep_progress_var.set(100)
                self.dep_status_var.set("Dependencias prontas.")
                self.after(600, self._mostrar_tela_login)

            elif tipo == "ERRO":
                _, erro = evento
                self._parar_barra_dependencias()
                self._mostrar_tela_encerramento(False, desafios=0, erro=erro)

        self.after(100, self._processar_dependencias)

    def _iniciar_barra_dependencias(self):
        if self.barra_dependencias_ocupada:
            return

        self.barra_dependencias.configure(mode="indeterminate")
        self.barra_dependencias.start(12)
        self.barra_dependencias_ocupada = True

    def _parar_barra_dependencias(self):
        if self.barra_dependencias_ocupada:
            self.barra_dependencias.stop()
            self.barra_dependencias_ocupada = False

        self.barra_dependencias.configure(mode="determinate")

    def _iniciar_bot(self):
        email = self.email_var.get().strip()
        senha = self.senha_var.get()

        if not email or not senha:
            messagebox.showwarning("Login incompleto", "Preencha email e senha para iniciar.")
            return

        if not self.dependencias:
            messagebox.showinfo(
                "Dependencias",
                "Prepare as dependencias antes de iniciar o login.",
            )
            self._iniciar_preparacao_dependencias()
            return

        self._limpar_logs()
        self.botao_iniciar.configure(state="disabled", text="Rodando...")
        self.status_var.set("Programa em execucao")
        self._mostrar_tela_mensagens()

        self.thread_bot = threading.Thread(
            target=self._rodar_bot_em_thread,
            args=(email, senha),
            daemon=True,
        )
        self.thread_bot.start()

    def _rodar_bot_em_thread(self, email, senha):
        escritor = QueueWriter(self.fila_logs)
        sucesso = False
        desafios = 0
        erro_fatal = None

        try:
            self.fila_logs.put("Iniciando programa...\n")
            with redirect_stdout(escritor), redirect_stderr(escritor):
                desafios = executar_bot(email, senha, self.dependencias)
            sucesso = True
        except BotErroFatal as erro:
            desafios = erro.desafios
            erro_fatal = erro.rastreamento
            self.fila_logs.put("\nErro fatal durante a execucao:\n")
            self.fila_logs.put(erro.rastreamento)
        except Exception:
            erro_fatal = traceback.format_exc()
            self.fila_logs.put("\nErro fatal durante a execucao:\n")
            self.fila_logs.put(erro_fatal)
        finally:
            self.fila_logs.put("\nProcesso finalizado.\n")
            self.fila_logs.put(("BOT_FIM", sucesso, desafios, erro_fatal))

    def _processar_logs(self):
        while True:
            try:
                mensagem = self.fila_logs.get_nowait()
            except queue.Empty:
                break

            if isinstance(mensagem, tuple) and mensagem[0] == "BOT_FIM":
                _, sucesso, desafios, erro_fatal = mensagem
                self.botao_iniciar.configure(state="normal", text="Iniciar")
                self.status_var.set("Processo finalizado")
                self._mostrar_tela_encerramento(
                    sucesso,
                    desafios=desafios,
                    erro=erro_fatal,
                )
                continue

            self._adicionar_log(mensagem)

        self.after(100, self._processar_logs)

    def _adicionar_log(self, mensagem):
        self.logs_texto.configure(state="normal")
        self.logs_texto.insert("end", mensagem)
        self.logs_texto.see("end")
        self.logs_texto.configure(state="disabled")

    def _limpar_logs(self):
        self.logs_texto.configure(state="normal")
        self.logs_texto.delete("1.0", "end")
        self.logs_texto.configure(state="disabled")

    def _voltar_para_login(self):
        self.status_var.set("")
        self._mostrar_tela_login()


if __name__ == "__main__":
    app = InterfaceApp()
    app.mainloop()
