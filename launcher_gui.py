"""
ClassicFoot Desktop Launcher
Janela própria com visual retrô (estilo terminal/DOS), sem terminal externo.
"""
from __future__ import annotations

import os
import queue
import re
import subprocess
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk


ANSI_TOKEN = re.compile(r"(\x1b\[[0-9;]*[A-Za-z])")
CHILD_ARG = "--classicfoot-child"


class ClassicFootLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ClassicFoot")
        self.geometry("1480x900")
        self.minsize(1180, 700)
        self.resizable(False, False)
        self.configure(bg="#000000")

        self.proc: subprocess.Popen[str] | None = None
        self.stdout_queue: queue.Queue[str] = queue.Queue()
        self._ansi_pending = ""
        self._style_tags: dict[str, str] = {}
        self._fg = "#7CFF7C"
        self._bg: str | None = None
        self._bold = True
        self._dim = False
        self._screen_was_cleared = False
        self._runs: list[tuple[str, str]] = []
        self._needs_redraw = False
        self._typed_buffer = ""
        self._build_ui()
        self._start_game_process()
        self.after(25, self._pump_stdout)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind_all("<Key>", self._on_keypress)

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("CF.TFrame", background="#000000")
        style.configure("CF.TEntry", fieldbackground="#001000", foreground="#00FF66")

        container.configure(style="CF.TFrame")

        text_wrap = ttk.Frame(container, style="CF.TFrame")
        text_wrap.pack(fill=tk.BOTH, expand=True)

        y_scroll = tk.Scrollbar(text_wrap, orient=tk.VERTICAL, bg="#001500")
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll = tk.Scrollbar(text_wrap, orient=tk.HORIZONTAL, bg="#001500")
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.screen = tk.Text(
            text_wrap,
            wrap=tk.NONE,
            bg="#000000",
            fg="#00FF66",
            insertbackground="#00FF66",
            font=("Menlo", 14),
            padx=8,
            pady=8,
            relief=tk.FLAT,
            xscrollcommand=x_scroll.set,
            yscrollcommand=y_scroll.set,
        )
        self.screen.pack(fill=tk.BOTH, expand=True)
        x_scroll.config(command=self.screen.xview)
        y_scroll.config(command=self.screen.yview)
        self.screen.configure(state=tk.DISABLED)

        self._setup_tags()

        self.screen.focus_set()

    def _setup_tags(self):
        self._style_tags.clear()
        self._reset_style()

    def _reset_style(self):
        self._fg = "#7CFF7C"
        self._bg = None
        self._bold = True
        self._dim = False

    def _estimate_terminal_size(self) -> tuple[int, int]:
        self.update_idletasks()
        f = tkfont.Font(font=self.screen.cget("font"))
        char_w = max(8, int(f.measure("M")))
        line_h = max(14, int(f.metrics("linespace")))
        px_w = max(900, self.screen.winfo_width())
        px_h = max(560, self.screen.winfo_height())
        cols = max(96, min(140, (px_w // char_w) - 8))
        lines = max(30, min(60, (px_h // line_h) - 2))
        return cols, lines

    def _style_tag(self) -> str:
        fg = self._fg
        bg = self._bg
        if fg.lower() == "#111111" and bg is None:
            fg = "#D8D8D8"
        if bg is not None and fg.lower() == bg.lower():
            fg = "#FFFFFF" if bg.lower() != "#ffffff" else "#000000"
        key = f"{fg}|{bg or 'none'}|{'b' if self._bold else 'n'}|{'d' if self._dim else 'n'}"
        tag = self._style_tags.get(key)
        if tag:
            return tag
        tag = f"style_{len(self._style_tags)+1}"
        self._style_tags[key] = tag
        if self._dim:
            self.screen.tag_configure(tag, foreground=fg, background=(bg or "#000000"))
        else:
            self.screen.tag_configure(tag, foreground=fg, background=(bg or "#000000"))
        return tag

    def _start_game_process(self):
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["TERM"] = "xterm-256color"
        env["CLASSICFOOT_EMBEDDED"] = "1"
        cols, lines = self._estimate_terminal_size()
        env["CLASSICFOOT_COLS"] = str(cols)
        env["COLUMNS"] = str(cols)
        env["LINES"] = str(lines)

        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]

        if getattr(sys, "frozen", False):
            cmd = [sys.executable, CHILD_ARG]
        else:
            cmd = [sys.executable, "-u", "main.py"]

        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=env,
            creationflags=creationflags,
        )

        t = threading.Thread(target=self._reader_worker, daemon=True)
        t.start()

    def _reader_worker(self):
        if not self.proc or not self.proc.stdout:
            return
        try:
            while True:
                chunk = self.proc.stdout.read(1)
                if chunk == "":
                    break
                self.stdout_queue.put(chunk)
        finally:
            self.stdout_queue.put("\n\n[ClassicFoot finalizado]\n")

    def _send_input(self, text: str):
        if not self.proc or not self.proc.stdin:
            return
        try:
            self.proc.stdin.write(text + "\n")
            self.proc.stdin.flush()
        except Exception:
            pass

    def _redraw_runs(self):
        self.screen.configure(state=tk.NORMAL)
        self.screen.delete("1.0", tk.END)
        for tag, txt in self._runs:
            self.screen.insert(tk.END, txt, (tag,))
        self.screen.configure(state=tk.DISABLED)
        self.screen.yview_moveto(1.0)

    def _append_typed_char(self, ch: str):
        tag = self._style_tag()
        if self._runs and self._runs[-1][0] == tag:
            t, txt = self._runs[-1]
            self._runs[-1] = (t, txt + ch)
        else:
            self._runs.append((tag, ch))
        self._needs_redraw = True

    def _remove_last_typed_char(self):
        if not self._runs:
            return
        tag, txt = self._runs[-1]
        if not txt:
            return
        txt = txt[:-1]
        if txt:
            self._runs[-1] = (tag, txt)
        else:
            self._runs.pop()
        self._needs_redraw = True

    def _on_keypress(self, event):
        if not self.proc or self.proc.poll() is not None:
            return

        keysym = event.keysym
        if keysym in ("Return", "KP_Enter"):
            to_send = self._typed_buffer
            self._append_typed_char("\n")
            self._typed_buffer = ""
            self._send_input(to_send)
            if self._needs_redraw:
                self._redraw_runs()
                self._needs_redraw = False
            return "break"

        if keysym == "BackSpace":
            if self._typed_buffer:
                self._typed_buffer = self._typed_buffer[:-1]
                self._remove_last_typed_char()
                if self._needs_redraw:
                    self._redraw_runs()
                    self._needs_redraw = False
            return "break"

        if keysym in ("Escape",):
            self._typed_buffer = ""
            return "break"

        # Ignora teclas especiais/modificadoras.
        ch = event.char or ""
        if len(ch) == 1 and ch.isprintable():
            self._typed_buffer += ch
            self._append_typed_char(ch)
            if self._needs_redraw:
                self._redraw_runs()
                self._needs_redraw = False
            return "break"

        return None

    def _pump_stdout(self):
        fragments = []
        while True:
            try:
                fragments.append(self.stdout_queue.get_nowait())
            except queue.Empty:
                break
        if fragments:
            self._append_ansi("".join(fragments))
        self.after(25, self._pump_stdout)

    def _append_ansi(self, content: str):
        content = self._ansi_pending + content
        self._ansi_pending = ""
        esc_idx = content.rfind("\x1b[")
        if esc_idx != -1:
            tail = content[esc_idx:]
            if not re.match(r"^\x1b\[[0-9;]*[A-Za-z]$", tail):
                self._ansi_pending = tail
                content = content[:esc_idx]

        parts = ANSI_TOKEN.split(content)
        for part in parts:
            if not part:
                continue
            if part.startswith("\x1b[") and part.endswith(("m", "J", "H")):
                self._handle_ansi_code(part)
                continue
            part = part.replace("\r", "")
            if not part:
                continue
            tag = self._style_tag()
            if self._runs and self._runs[-1][0] == tag:
                prev_tag, prev_txt = self._runs[-1]
                self._runs[-1] = (prev_tag, prev_txt + part)
            else:
                self._runs.append((tag, part))
            self._needs_redraw = True

        if self._needs_redraw:
            self._redraw_runs()
            if self._screen_was_cleared:
                self.screen.yview_moveto(0.0)
                self.screen.xview_moveto(0.0)
                self._screen_was_cleared = False
            self._needs_redraw = False
        self.screen.configure(state=tk.DISABLED)

    def _handle_ansi_code(self, seq: str):
        if seq.endswith("J"):
            # Clear screen.
            self._runs = []
            self._needs_redraw = True
            self._screen_was_cleared = True
            return
        if seq.endswith("H"):
            # Cursor home: ignorado (clear já reposiciona visualmente).
            return
        if not seq.endswith("m"):
            return
        values = seq[2:-1] or "0"
        codes = [int(v) if v.isdigit() else 0 for v in values.split(";")]
        fg_normal = {
            30: "#111111",
            31: "#C63B3B",
            32: "#2ECF5E",
            33: "#D6AF3B",
            34: "#447EDB",
            35: "#B74ADB",
            36: "#36C8CF",
            37: "#D8D8D8",
        }
        fg_bright = {
            90: "#7A7A7A",
            91: "#FF8080",
            92: "#7CFF7C",
            93: "#FFF29A",
            94: "#9BC1FF",
            95: "#F2B2FF",
            96: "#9CFFFF",
            97: "#FFFFFF",
        }
        bg_normal = {
            40: "#000000",
            41: "#7C1F1F",
            42: "#0D6F27",
            43: "#7A6300",
            44: "#173A86",
            45: "#692B7F",
            46: "#0C5E63",
            47: "#BBBBBB",
        }
        bg_bright = {
            100: "#444444",
            101: "#CC3C3C",
            102: "#2FAA3A",
            103: "#B28E12",
            104: "#2F5BB4",
            105: "#8A42A1",
            106: "#1A8A91",
            107: "#FFFFFF",
        }

        for code in codes:
            if code == 0:
                self._reset_style()
                continue
            if code == 1:
                self._bold = True
                self._dim = False
                continue
            if code == 2:
                self._dim = True
                self._bold = False
                continue
            if code == 22:
                self._dim = False
                self._bold = False
                continue
            if code == 39:
                self._fg = "#7CFF7C"
                continue
            if code == 49:
                self._bg = None
                continue
            if code in fg_normal:
                self._fg = fg_normal[code]
                continue
            if code in fg_bright:
                self._fg = fg_bright[code]
                self._bold = True
                self._dim = False
                continue
            if code in bg_normal:
                self._bg = bg_normal[code]
                continue
            if code in bg_bright:
                self._bg = bg_bright[code]
                continue
            if code == 7:  # reverse
                cur_fg = self._fg
                self._fg = self._bg or "#000000"
                self._bg = cur_fg

    def _on_close(self):
        try:
            if self.proc and self.proc.poll() is None:
                self.proc.terminate()
        except Exception:
            pass
        self.destroy()


def main():
    if CHILD_ARG in sys.argv:
        import main as game_main
        game_main.main()
        return

    app = ClassicFootLauncher()
    app.mainloop()


if __name__ == "__main__":
    main()
