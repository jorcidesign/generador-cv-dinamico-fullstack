#!/usr/bin/env python3
"""
CV Generator · Jorge Del Aguila
Uso: python generate_cv.py
"""

import sys
import json
import math
from pathlib import Path
from datetime import datetime

# ── Dependencias externas ────────────────────────────────────────────────────────
try:
    import questionary
    from questionary import Style as QStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    sys.exit("❌  Instala dependencias primero:\n    pip install -r requirements.txt\n")

# ── Rutas ────────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parent
INPUTS_DIR = ROOT / "inputs"
OUTPUT_DIR = ROOT / "output"
DATA_FILE  = INPUTS_DIR / "cv_data.json"

# ── Registro de fuentes Unicode ──────────────────────────────────────────────────
_FONT_CANDIDATES = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",      "CV-Regular"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "CV-Bold"),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "CV-Regular"),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",    "CV-Bold"),
]

def _register_fonts() -> tuple[str, str]:
    registered: set[str] = set()
    for path, name in _FONT_CANDIDATES:
        if name not in registered and Path(path).exists():
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                registered.add(name)
            except Exception:
                pass
    if "CV-Regular" in registered and "CV-Bold" in registered:
        return "CV-Regular", "CV-Bold"
    return "Helvetica", "Helvetica-Bold"

FONT_R, FONT_B = _register_fonts()

# ── Temas de color ──────────────────────────────────────────────────────────────
THEMES = {
    "naranjo":  {"hex": "#E8620A", "pdf": colors.HexColor("#E8620A")},
    "morado":   {"hex": "#7B2D8E", "pdf": colors.HexColor("#7B2D8E")},
    "rojo":     {"hex": "#D32F2F", "pdf": colors.HexColor("#D32F2F")},
    "azul":     {"hex": "#1976D2", "pdf": colors.HexColor("#1976D2")},
}

DARK    = colors.HexColor("#1E1E1E")
GRAY    = colors.HexColor("#555555")
LGRAY   = colors.HexColor("#999999")
DIVIDER = colors.HexColor("#DEDEDE")
SIDEBAR = colors.HexColor("#F5F5F5")

# ── Geometría de página (puntos = 1/72 pulgada) ──────────────────────────────────
PAGE_W, PAGE_H = A4

SB_W    = 172
L_X     = 16
L_W     = SB_W - L_X - 12

MAIN_X  = SB_W + 14
MAIN_W  = PAGE_W - MAIN_X - 18

TOP_Y   = PAGE_H - 22
BOT_Y   = 22

# ── Escala tipográfica ────────────────────────────────────────────────────────────
SZ_NAME = 23
SZ_ROLE = 10.5
SZ_SEC  = 7.5
SZ_LBL  = 8.5
SZ_BODY = 8.0
SZ_SM   = 7.5

LH      = 11.5
LH_S    = 10.5

# ── Constructor de estilo para el menú terminal ──────────────────────────────────
def _make_style(hex_color: str) -> QStyle:
    return QStyle([
        ("qmark",       f"fg:{hex_color} bold"),
        ("question",    "bold"),
        ("answer",      f"fg:{hex_color} bold"),
        ("pointer",     f"fg:{hex_color} bold"),
        ("highlighted", f"fg:{hex_color} bold"),
        ("selected",    f"fg:{hex_color}"),
        ("separator",   "fg:#666666"),
    ])

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  Utilidades de dibujo                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _wrap(c: Canvas, text: str, font: str, size: float, max_w: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        test = (cur + " " + word).strip()
        if c.stringWidth(test, font, size) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [""]


def put(c: Canvas, text: str, x: float, y: float,
        font: str | None = None, size: float = SZ_BODY,
        color=DARK, align: str = "left") -> None:
    c.setFont(font or FONT_R, size)
    c.setFillColor(color)
    if align == "right":
        c.drawRightString(x, y, text)
    elif align == "center":
        c.drawCentredString(x, y, text)
    else:
        c.drawString(x, y, text)


def block(c: Canvas, text: str, x: float, y: float, max_w: float,
          font: str | None = None, size: float = SZ_BODY,
          lh: float = LH, color=DARK) -> float:
    f = font or FONT_R
    c.setFont(f, size)
    c.setFillColor(color)
    for line in _wrap(c, text, f, size, max_w):
        c.drawString(x, y, line)
        y -= lh
    return y


def sec_header(c: Canvas, title: str, x: float, y: float,
               width: float, gap: float = 9, accent=DARK) -> float:
    y -= gap
    put(c, title.upper(), x, y, font=FONT_B, size=SZ_SEC, color=accent)
    y -= 4
    c.setStrokeColor(accent)
    c.setLineWidth(0.45)
    c.line(x, y, x + width, y)
    y -= 14
    return y


def circle_photo(c: Canvas, path: Path, cx: float, cy: float, r: float,
                 accent=DARK) -> None:
    k = 0.5522847498
    c.saveState()
    p = c.beginPath()
    p.moveTo(cx, cy + r)
    p.curveTo(cx + r*k, cy + r,   cx + r,   cy + r*k,  cx + r, cy)
    p.curveTo(cx + r,   cy - r*k, cx + r*k, cy - r,    cx,     cy - r)
    p.curveTo(cx - r*k, cy - r,   cx - r,   cy - r*k,  cx - r, cy)
    p.curveTo(cx - r,   cy + r*k, cx - r*k, cy + r,    cx,     cy + r)
    p.close()
    c.clipPath(p, stroke=0, fill=0)
    img   = ImageReader(str(path))
    iw, ih = img.getSize()
    scale  = (r * 2) / min(iw, ih)
    dw, dh = iw * scale, ih * scale
    c.drawImage(img, cx - dw / 2, cy - dh / 2, width=dw, height=dh, mask="auto")
    c.restoreState()
    c.setStrokeColor(accent)
    c.setLineWidth(1.8)
    c.circle(cx, cy, r, stroke=1, fill=0)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  Generador de CV                                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class CVGen:
    def __init__(self, data: dict, orientation: str, photo: Path | None,
                 accent_hex: str, accent_pdf):
        self.d   = data
        self.ori = orientation
        self.photo = photo
        self.accent_hex = accent_hex
        self.accent = accent_pdf

        OUTPUT_DIR.mkdir(exist_ok=True)
        ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"CV_JorgeDelAguila_{orientation.capitalize()}_{ts}.pdf"
        self.out = OUTPUT_DIR / fname
        self.c   = Canvas(str(self.out), pagesize=A4)

        self.ly = TOP_Y
        self.ry = TOP_Y

    def _sidebar_bg(self) -> None:
        self.c.setFillColor(SIDEBAR)
        self.c.rect(0, 0, SB_W, PAGE_H, stroke=0, fill=1)

    # ══════════════════════════════════════════════════════════════
    #  COLUMNA IZQUIERDA
    # ══════════════════════════════════════════════════════════════

    def _sec_l(self, title: str) -> None:
        self.ly = sec_header(self.c, title, L_X, self.ly, L_W, accent=self.accent)

    def _contact(self) -> None:
        self._sec_l("Contacto")
        p = self.d["personal"]
        rows = [
            ("✉", p.get("email", "")),
            ("✆", p.get("phone", "")),
            ("▪", p.get("location", "")),
        ]
        github = p.get("github", "")
        if github:
            rows.append(("▪", github))
        c = self.c
        for icon, text in rows:
            put(c, icon, L_X, self.ly, size=SZ_BODY, color=self.accent)
            icon_w = c.stringWidth(icon, FONT_R, SZ_BODY)
            tx = L_X + icon_w + 4
            tw = L_W - icon_w - 4
            is_link = "@" in text or text.startswith("github") or ".app" in text or ".com" in text
            col = self.accent if is_link else GRAY
            lines = _wrap(c, text, FONT_R, SZ_BODY, tw)
            for line in lines:
                put(c, line, tx, self.ly, size=SZ_BODY, color=col)
                self.ly -= LH_S
            self.ly -= 2

    def _skills(self) -> None:
        self._sec_l("Habilidades")
        skills_data = self.d.get("skills", [])
        if isinstance(skills_data, list):
            self.ly = block(self.c, "  ·  ".join(skills_data),
                            L_X, self.ly, L_W, size=SZ_BODY, lh=LH_S, color=GRAY)
            self.ly -= 5
            return

        groups = skills_data
        if self.ori == "fullstack":
            order = list(groups.keys())
        else:
            order = [self.ori] + [k for k in groups if k != self.ori]

        for key in order:
            grp = groups[key]
            put(self.c, grp["label"], L_X, self.ly, font=FONT_B, size=SZ_LBL, color=DARK)
            self.ly -= LH
            self.ly = block(self.c, ", ".join(grp["items"]),
                            L_X, self.ly, L_W, size=SZ_BODY, lh=LH_S, color=GRAY)
            self.ly -= 5

    def _education(self) -> None:
        self._sec_l("Educación")
        for edu in self.d["education"]:
            self.ly = block(self.c, edu["institution"], L_X, self.ly, L_W, font=FONT_B, size=SZ_LBL, lh=LH_S, color=DARK)
            self.ly = block(self.c, edu["degree"], L_X, self.ly, L_W, size=SZ_BODY, lh=LH_S, color=GRAY)
            period = edu.get("period", "")
            if period:
                put(self.c, period, L_X, self.ly, size=SZ_SM, color=LGRAY)
                self.ly -= LH
            self.ly -= 5

    def _languages(self) -> None:
        langs = self.d.get("languages", [])
        if not langs:
            return
        self._sec_l("Idiomas")
        for lang in langs:
            put(self.c, lang["name"], L_X, self.ly, font=FONT_B, size=SZ_LBL, color=DARK)
            self.ly -= LH
            self.ly = block(self.c, lang["level"], L_X, self.ly, L_W,
                            size=SZ_BODY, lh=LH_S, color=GRAY)
            self.ly -= 5

    def _competencies(self) -> None:
        items = self.d.get("competencies", [])
        if not items:
            return
        self._sec_l("Competencias")
        for item in items:
            put(self.c, "•  " + item, L_X, self.ly, size=SZ_BODY, color=GRAY)
            self.ly -= LH

    def _interests(self) -> None:
        items = self.d.get("interests", [])
        if not items:
            return
        self._sec_l("Intereses")
        text = "  ·  ".join(items)
        self.ly = block(self.c, text, L_X, self.ly, L_W, size=SZ_BODY, lh=LH_S, color=GRAY)

    def _draw_left(self) -> None:
        if self.photo:
            r  = 38
            cx = SB_W / 2
            cy = TOP_Y - r - 10
            circle_photo(self.c, self.photo, cx, cy, r, accent=self.accent)
            self.ly = cy - r - 16
        self._contact()
        self._skills()
        self._education()
        self._languages()
        self._competencies()
        self._interests()

    # ══════════════════════════════════════════════════════════════
    #  COLUMNA DERECHA
    # ══════════════════════════════════════════════════════════════

    def _sec_r(self, title: str) -> None:
        self.ry = sec_header(self.c, title, MAIN_X, self.ry, MAIN_W, accent=self.accent)

    def _header_name(self) -> None:
        p = self.d["personal"]
        put(self.c, p["name"], MAIN_X, self.ry, font=FONT_B, size=SZ_NAME, color=DARK)
        self.ry -= SZ_NAME + 5
        title = p.get("title", "")
        if not title:
            title = p.get("titles", {}).get(self.ori, "")
        self.ry = block(self.c, title, MAIN_X, self.ry, MAIN_W, size=SZ_ROLE, lh=LH, color=self.accent)
        self.ry -= 2
        self.c.setStrokeColor(DIVIDER)
        self.c.setLineWidth(0.5)
        self.c.line(MAIN_X, self.ry, MAIN_X + MAIN_W, self.ry)
        self.ry -= 13

    def _profile(self) -> None:
        text = self.d.get("about") or ""
        if not text:
            text = self.d.get("profiles", {}).get(self.ori, "")
        if not text:
            return
        self._sec_r("Perfil Profesional")
        self.ry = block(self.c, text, MAIN_X, self.ry, MAIN_W, size=SZ_BODY, lh=LH, color=GRAY)
        self.ry -= 8

    def _experience(self) -> None:
        self._sec_r("Experiencia")
        c = self.c
        for exp in self.d["experience"]:
            label = f"{exp['company']}  ·  {exp['role']}"
            label_w = c.stringWidth(label, FONT_B, SZ_BODY + 0.5)
            period_w = c.stringWidth(exp["period"], FONT_R, SZ_SM)
            if label_w + period_w + 10 <= MAIN_W:
                put(c, label, MAIN_X, self.ry, font=FONT_B, size=SZ_BODY + 0.5, color=DARK)
                put(c, exp["period"], MAIN_X + MAIN_W, self.ry,
                    size=SZ_SM, color=LGRAY, align="right")
            else:
                self.ry = block(c, label, MAIN_X, self.ry, MAIN_W,
                                font=FONT_B, size=SZ_BODY + 0.5, lh=LH, color=DARK)
                put(c, exp["period"], MAIN_X + MAIN_W, self.ry,
                    size=SZ_SM, color=LGRAY, align="right")
                self.ry -= LH
            self.ry -= LH + 1
            for bullet in exp["bullets"]:
                self.ry = block(c, "•  " + bullet, MAIN_X + 6, self.ry,
                                MAIN_W - 6, size=SZ_BODY, lh=LH, color=GRAY)
            self.ry -= 10

    def _projects(self) -> None:
        projects = self.d.get("projects", [])
        if not projects:
            return
        self._sec_r("Proyectos Personales")
        c = self.c
        projects = [p for p in projects
                    if self.ori in p.get("tags", ["fullstack"])]
        for proj in projects:
            name_w = c.stringWidth(proj["name"], FONT_B, SZ_BODY + 0.5)
            put(c, proj["name"], MAIN_X, self.ry, font=FONT_B, size=SZ_BODY + 0.5, color=DARK)
            sq_x = MAIN_X + name_w + 5
            sq_y = self.ry + 1.5
            c.setFillColor(self.accent)
            c.rect(sq_x, sq_y, 4, 4, stroke=0, fill=1)
            put(c, proj["url"], sq_x + 7, self.ry, size=SZ_BODY, color=self.accent)
            self.ry -= LH + 1
            self.ry = block(c, proj["description"], MAIN_X, self.ry,
                            MAIN_W, size=SZ_BODY, lh=LH, color=GRAY)
            self.ry -= 10

    def _draw_right(self) -> None:
        self._header_name()
        self._profile()
        self._experience()
        self._projects()

    def run(self) -> Path:
        self._sidebar_bg()
        self._draw_left()
        self._draw_right()
        self.c.save()
        return self.out


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  CLI — menú interactivo                                                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _pick_accent() -> tuple[str, str, object]:
    accent = questionary.select(
        "Color de acento:",
        choices=["Naranjo", "Morado", "Rojo", "Azul"],
        default="Naranjo",
    ).ask()

    key = {
        "Naranjo": "naranjo",
        "Morado":  "morado",
        "Rojo":    "rojo",
        "Azul":    "azul",
    }[accent]

    theme = THEMES[key]
    return key, theme["hex"], theme["pdf"]


def _pick_photo(style: QStyle) -> Path | None:
    has = questionary.confirm(
        "¿Tu CV va con foto de perfil?",
        default=False,
        style=style,
    ).ask()
    if not has:
        return None

    exts   = {".png", ".jpg", ".jpeg", ".webp"}
    photos = [f for f in INPUTS_DIR.iterdir() if f.suffix.lower() in exts]

    if not photos:
        print(f"\n  ⚠  No hay fotos en {INPUTS_DIR}/")
        print("     Coloca tu foto (PNG o JPG) ahí y vuelve a ejecutar.\n")
        return None

    if len(photos) == 1:
        print(f"\n  Foto detectada: {photos[0].name}")
        return photos[0]

    name = questionary.select(
        "Selecciona tu foto:",
        choices=[p.name for p in photos],
        style=style,
    ).ask()
    return next(p for p in photos if p.name == name)


def _pick_orientation(style: QStyle) -> str:
    mapping = {
        "Full Stack  — muestra todo el stack": "fullstack",
        "Frontend    — énfasis en UI / creative coding":  "frontend",
        "Backend     — énfasis en APIs / arquitectura":   "backend",
    }
    choice = questionary.select(
        "¿Este CV está orientado a...?",
        choices=list(mapping.keys()),
        style=style,
    ).ask()
    return mapping[choice]


def main() -> None:
    banner = """
  ╔═══════════════════════════════════════╗
  ║   CV Generator  ·  Jorge Del Aguila   ║
  ║   github.com/jorcidesign              ║
  ╚═══════════════════════════════════════╝
"""
    print(banner)

    if not DATA_FILE.exists():
        sys.exit(f"  ❌  No se encontró {DATA_FILE}\n"
                 f"     Crea el archivo inputs/cv_data.json primero.\n")

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    theme_key, accent_hex, accent_pdf = _pick_accent()
    style = _make_style(accent_hex)

    photo       = _pick_photo(style)
    orientation = _pick_orientation(style)

    print(f"\n  ⚙  Generando PDF [{orientation}]"
          f" {'· con foto' if photo else '· sin foto'} ...")

    gen = CVGen(data, orientation, photo, accent_hex, accent_pdf)
    out = gen.run()

    print(f"  ✅  Listo  →  output/{out.name}\n")


if __name__ == "__main__":
    main()
