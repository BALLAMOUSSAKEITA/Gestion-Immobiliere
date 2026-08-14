"""
Génère le Guide d'utilisation complet de Gestion Immo (PDF + maquettes UI).
Usage: python docs/generate_user_guide.py
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Palette (identique à globals.css) ──────────────────────────────────────
RAUSCH = (255, 56, 92)
HOF = (34, 34, 34)
FOGGY = (106, 106, 106)
BEBE = (235, 235, 235)
FAINT = (247, 247, 247)
WHITE = (255, 255, 255)
SUCCESS = (0, 138, 5)
WARNING = (217, 119, 6)

DOCS_DIR = Path(__file__).resolve().parent
ASSETS_DIR = DOCS_DIR / "guide_assets"
OUTPUT_PDF = DOCS_DIR / "Guide_Utilisation_Gestion_Immo.pdf"

SCREEN_W, SCREEN_H = 1200, 750


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _rounded_rect(draw: ImageDraw.ImageDraw, xy, radius: int, fill, outline=None, width: int = 1):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _sidebar(draw: ImageDraw.ImageDraw, items: list[tuple[str, bool]], title: str = "Gestion Immo"):
    draw.rectangle([0, 0, 220, SCREEN_H], fill=WHITE)
    draw.line([220, 0, 220, SCREEN_H], fill=BEBE, width=1)
    draw.text((20, 24), title, font=_font(16, True), fill=HOF)
    draw.text((20, 48), "Tableau de bord", font=_font(11), fill=FOGGY)
    y = 90
    for label, active in items:
        if active:
            _rounded_rect(draw, (12, y, 208, y + 36), 8, FAINT, RAUSCH, 2)
        draw.text((36, y + 10), label, font=_font(13, active), fill=HOF if active else FOGGY)
        y += 42


def _header_bar(draw: ImageDraw.ImageDraw, page_title: str, user: str = "Admin Familial"):
    draw.rectangle([220, 0, SCREEN_W, 64], fill=WHITE)
    draw.line([220, 64, SCREEN_W, 64], fill=BEBE, width=1)
    draw.text((240, 20), page_title, font=_font(20, True), fill=HOF)
    _rounded_rect(draw, (SCREEN_W - 200, 16, SCREEN_W - 24, 48), 20, FAINT)
    draw.text((SCREEN_W - 180, 24), user, font=_font(12), fill=FOGGY)


def _kpi_card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, title: str, value: str, sub: str = ""):
    _rounded_rect(draw, (x, y, x + w, y + h), 12, WHITE, BEBE, 1)
    draw.text((x + 16, y + 14), title, font=_font(12), fill=FOGGY)
    draw.text((x + 16, y + 38), value, font=_font(22, True), fill=HOF)
    if sub:
        draw.text((x + 16, y + 68), sub, font=_font(11), fill=SUCCESS if "+" in sub else FOGGY)


def mock_login() -> Path:
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), FAINT)
    draw = ImageDraw.Draw(img)
    _rounded_rect(draw, (380, 120, 820, 580), 16, WHITE, BEBE, 1)
    draw.text((480, 160), "Gestion Immo", font=_font(24, True), fill=HOF)
    draw.text((480, 195), "Connexion à votre espace", font=_font(13), fill=FOGGY)
    draw.text((420, 250), "Adresse e-mail", font=_font(12), fill=HOF)
    _rounded_rect(draw, (420, 270, 780, 310), 8, FAINT, BEBE, 1)
    draw.text((432, 282), "admin@gestion-immo.local", font=_font(13), fill=FOGGY)
    draw.text((420, 330), "Mot de passe", font=_font(12), fill=HOF)
    _rounded_rect(draw, (420, 350, 780, 390), 8, FAINT, BEBE, 1)
    draw.text((432, 362), "••••••••••", font=_font(13), fill=FOGGY)
    _rounded_rect(draw, (420, 430, 780, 475), 8, HOF)
    draw.text((555, 443), "Se connecter", font=_font(14, True), fill=WHITE)
    draw.text((480, 510), "Mot de passe oublié ?", font=_font(12), fill=RAUSCH)
    path = ASSETS_DIR / "01_login.png"
    img.save(path)
    return path


def mock_dashboard() -> Path:
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), FAINT)
    draw = ImageDraw.Draw(img)
    nav = [
        ("Tableau de bord", True),
        ("Immeubles", False),
        ("Logements", False),
        ("Locataires", False),
        ("Baux", False),
        ("Paiements", False),
        ("Impayés", False),
        ("Reçus", False),
        ("Dépenses", False),
    ]
    _sidebar(draw, nav)
    _header_bar(draw, "Tableau de bord", "Admin Familial")
    cards = [
        ("Immeubles", "4", "+1 ce mois"),
        ("Taux d'occupation", "87 %", "32 / 37 logements"),
        ("Loyers encaissés", "48 500 000 GNF", "Mars 2026"),
        ("Impayés", "3 200 000 GNF", "5 locataires"),
    ]
    x = 240
    for title, val, sub in cards:
        _kpi_card(draw, x, 84, 220, 95, title, val, sub)
        x += 235
    _rounded_rect(draw, (240, 200, 720, 520), 12, WHITE, BEBE, 1)
    draw.text((260, 218), "Revenus vs Dépenses", font=_font(14, True), fill=HOF)
    for i, h in enumerate([120, 90, 150, 110, 180, 140]):
        bx = 280 + i * 65
        draw.rectangle([bx, 480 - h, bx + 35, 480], fill=RAUSCH if i % 2 == 0 else HOF)
    _rounded_rect(draw, (740, 200, 1160, 520), 12, WHITE, BEBE, 1)
    draw.text((760, 218), "Alertes", font=_font(14, True), fill=HOF)
    alerts = [
        ("Bail expirant", "M. Diallo — Apt 3B", WARNING),
        ("Impayé 2 mois", "Mme Camara — Magasin 1", RAUSCH),
        ("Réparation en cours", "Plomberie — Immeuble A", FOGGY),
    ]
    y = 260
    for title, detail, color in alerts:
        draw.ellipse([760, y + 4, 772, y + 16], fill=color)
        draw.text((782, y), title, font=_font(12, True), fill=HOF)
        draw.text((782, y + 18), detail, font=_font(11), fill=FOGGY)
        y += 55
    path = ASSETS_DIR / "02_dashboard.png"
    img.save(path)
    return path


def mock_buildings() -> Path:
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), FAINT)
    draw = ImageDraw.Draw(img)
    _sidebar(draw, [("Tableau de bord", False), ("Immeubles", True), ("Logements", False), ("Locataires", False)])
    _header_bar(draw, "Immeubles")
    _rounded_rect(draw, (SCREEN_W - 180, 78, SCREEN_W - 40, 118), 8, HOF)
    draw.text((SCREEN_W - 165, 90), "+ Nouveau", font=_font(12, True), fill=WHITE)
    rows = [
        ("IMM-001", "Résidence Kaloum", "Kaloum", "12 logements", "87 %"),
        ("IMM-002", "Tour Dixinn", "Dixinn", "8 logements", "75 %"),
        ("IMM-003", "Centre Matam", "Matam", "5 magasins", "100 %"),
    ]
    y = 140
    _rounded_rect(draw, (240, y, 1160, y + 40), 8, BEBE)
    draw.text((260, y + 12), "Code", font=_font(11, True), fill=FOGGY)
    draw.text((360, y + 12), "Nom", font=_font(11, True), fill=FOGGY)
    draw.text((580, y + 12), "Commune", font=_font(11, True), fill=FOGGY)
    draw.text((740, y + 12), "Logements", font=_font(11, True), fill=FOGGY)
    draw.text((920, y + 12), "Occupation", font=_font(11, True), fill=FOGGY)
    y += 50
    for code, name, commune, units, occ in rows:
        _rounded_rect(draw, (240, y, 1160, y + 52), 8, WHITE, BEBE, 1)
        draw.text((260, y + 16), code, font=_font(12), fill=HOF)
        draw.text((360, y + 16), name, font=_font(12, True), fill=HOF)
        draw.text((580, y + 16), commune, font=_font(12), fill=FOGGY)
        draw.text((740, y + 16), units, font=_font(12), fill=FOGGY)
        draw.text((920, y + 16), occ, font=_font(12, True), fill=SUCCESS)
        y += 60
    path = ASSETS_DIR / "03_immeubles.png"
    img.save(path)
    return path


def mock_tenants() -> Path:
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), FAINT)
    draw = ImageDraw.Draw(img)
    _sidebar(draw, [("Locataires", True), ("Baux", False), ("Paiements", False)])
    _header_bar(draw, "Locataires")
    _rounded_rect(draw, (240, 84, 480, 124), 8, WHITE, BEBE, 1)
    draw.text((255, 98), "Rechercher un locataire...", font=_font(12), fill=FOGGY)
    cards_data = [
        ("Amadou Diallo", "Apt 3B — Kaloum", "Actif", "650 000 GNF/mois"),
        ("Fatoumata Camara", "Magasin 1 — Matam", "Actif", "1 200 000 GNF/mois"),
        ("Ibrahima Bah", "Bureau 2 — Dixinn", "En attente", "800 000 GNF/mois"),
    ]
    x, y = 240, 140
    for name, unit, status, rent in cards_data:
        _rounded_rect(draw, (x, y, x + 280, y + 160), 12, WHITE, BEBE, 1)
        draw.ellipse([x + 16, y + 16, x + 64, y + 64], fill=BEBE)
        draw.text((x + 80, y + 20), name, font=_font(14, True), fill=HOF)
        draw.text((x + 80, y + 44), unit, font=_font(11), fill=FOGGY)
        color = SUCCESS if status == "Actif" else WARNING
        _rounded_rect(draw, (x + 80, y + 68, x + 140, y + 90), 12, (*color, 30) if len(color) == 3 else FAINT)
        draw.text((x + 90, y + 72), status, font=_font(10, True), fill=color)
        draw.text((x + 16, y + 120), rent, font=_font(13, True), fill=HOF)
        x += 300
    path = ASSETS_DIR / "04_locataires.png"
    img.save(path)
    return path


def mock_payments() -> Path:
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), FAINT)
    draw = ImageDraw.Draw(img)
    _sidebar(draw, [("Paiements", True), ("Impayés", False), ("Reçus", False)])
    _header_bar(draw, "Paiements")
    _rounded_rect(draw, (SCREEN_W - 200, 78, SCREEN_W - 40, 118), 8, HOF)
    draw.text((SCREEN_W - 178, 90), "+ Enregistrer", font=_font(12, True), fill=WHITE)
    rows = [
        ("15/03/2026", "Amadou Diallo", "650 000 GNF", "Orange Money", "Validé"),
        ("14/03/2026", "Fatoumata Camara", "1 200 000 GNF", "Espèces", "Validé"),
        ("12/03/2026", "Ibrahima Bah", "400 000 GNF", "Wave", "En attente"),
    ]
    y = 140
    headers = ["Date", "Locataire", "Montant", "Mode", "Statut"]
    xs = [260, 400, 620, 820, 980]
    for i, h in enumerate(headers):
        draw.text((xs[i], y), h, font=_font(11, True), fill=FOGGY)
    y += 30
    for date_s, tenant, amount, mode, status in rows:
        _rounded_rect(draw, (240, y, 1160, y + 48), 8, WHITE, BEBE, 1)
        draw.text((260, y + 16), date_s, font=_font(12), fill=FOGGY)
        draw.text((400, y + 16), tenant, font=_font(12), fill=HOF)
        draw.text((620, y + 16), amount, font=_font(12, True), fill=HOF)
        draw.text((820, y + 16), mode, font=_font(12), fill=FOGGY)
        sc = SUCCESS if status == "Validé" else WARNING
        draw.text((980, y + 16), status, font=_font(12, True), fill=sc)
        y += 56
    path = ASSETS_DIR / "05_paiements.png"
    img.save(path)
    return path


def mock_tenant_portal() -> Path:
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), FAINT)
    draw = ImageDraw.Draw(img)
    _sidebar(draw, [
        ("Tableau de bord", True),
        ("Mon logement", False),
        ("Mon contrat", False),
        ("Paiements", False),
        ("Reçus", False),
        ("Réparations", False),
    ], title="Espace Locataire")
    _header_bar(draw, "Mon espace", "Amadou Diallo")
    _kpi_card(draw, 240, 84, 280, 100, "Mon loyer", "650 000 GNF", "Échéance : 5 avril")
    _kpi_card(draw, 540, 84, 280, 100, "Solde impayé", "0 GNF", "À jour")
    _kpi_card(draw, 840, 84, 280, 100, "Dernier paiement", "650 000 GNF", "15 mars 2026")
    _rounded_rect(draw, (240, 210, 700, 520), 12, WHITE, BEBE, 1)
    draw.text((260, 228), "Mon logement", font=_font(14, True), fill=HOF)
    _rounded_rect(draw, (260, 260, 680, 420), 8, BEBE)
    draw.text((280, 440), "Appartement 3B — Résidence Kaloum", font=_font(13, True), fill=HOF)
    draw.text((280, 462), "2 chambres • 1 salon • Kaloum, Conakry", font=_font(11), fill=FOGGY)
    _rounded_rect(draw, (720, 210, 1160, 520), 12, WHITE, BEBE, 1)
    draw.text((740, 228), "Actions rapides", font=_font(14, True), fill=HOF)
    actions = ["Télécharger mon reçu", "Signaler une panne", "Contacter le gestionnaire"]
    y = 270
    for action in actions:
        _rounded_rect(draw, (740, y, 1140, y + 44), 8, FAINT, BEBE, 1)
        draw.text((756, y + 13), action, font=_font(12), fill=HOF)
        y += 56
    path = ASSETS_DIR / "06_espace_locataire.png"
    img.save(path)
    return path


def mock_public_listings() -> Path:
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), FAINT)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, SCREEN_W, 64], fill=WHITE)
    draw.text((40, 20), "Gestion Immo", font=_font(18, True), fill=HOF)
    for label, x in [("Annonces", 800), ("Contact", 920), ("Connexion", 1060)]:
        draw.text((x, 24), label, font=_font(12, label == "Connexion"), fill=RAUSCH if label == "Connexion" else FOGGY)
    draw.text((40, 90), "Logements disponibles", font=_font(24, True), fill=HOF)
    listings = [
        ("Appartement 2 ch.", "Kaloum", "550 000 GNF/mois"),
        ("Magasin commercial", "Matam", "900 000 GNF/mois"),
        ("Bureau équipé", "Dixinn", "750 000 GNF/mois"),
    ]
    x = 40
    for title, loc, price in listings:
        _rounded_rect(draw, (x, 150, x + 360, 520), 12, WHITE, BEBE, 1)
        _rounded_rect(draw, (x + 12, 162, x + 348, 340), 8, BEBE)
        draw.text((x + 20, 360), title, font=_font(15, True), fill=HOF)
        draw.text((x + 20, 385), loc, font=_font(12), fill=FOGGY)
        draw.text((x + 20, 420), price, font=_font(14, True), fill=RAUSCH)
        _rounded_rect(draw, (x + 20, 460, x + 200, 500), 8, HOF)
        draw.text((x + 48, 472), "Demander visite", font=_font(11, True), fill=WHITE)
        x += 380
    path = ASSETS_DIR / "07_annonces.png"
    img.save(path)
    return path


def mock_repairs_kanban() -> Path:
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), FAINT)
    draw = ImageDraw.Draw(img)
    _sidebar(draw, [("Réparations", True)])
    _header_bar(draw, "Réparations")
    columns = [
        ("Nouvelle", RAUSCH, ["Fuite robinet — Apt 2A"]),
        ("En cours", WARNING, ["Peinture hall — IMM-001", "Électricité — Bureau 2"]),
        ("Terminée", SUCCESS, ["Serrure remplacée — Magasin 1"]),
    ]
    x = 240
    for col_name, color, cards in columns:
        draw.text((x + 10, 84), col_name, font=_font(13, True), fill=HOF)
        _rounded_rect(draw, (x, 110, x + 290, SCREEN_H - 40), 12, BEBE)
        y = 130
        for card in cards:
            _rounded_rect(draw, (x + 12, y, x + 278, y + 80), 8, WHITE, BEBE, 1)
            draw.rectangle([x + 12, y, x + 18, y + 80], fill=color)
            draw.text((x + 28, y + 16), card, font=_font(11, True), fill=HOF)
            draw.text((x + 28, y + 40), "Urgence : moyenne", font=_font(10), fill=FOGGY)
            y += 92
        x += 310
    path = ASSETS_DIR / "08_reparations.png"
    img.save(path)
    return path


def mock_validations() -> Path:
    img = Image.new("RGB", (SCREEN_W, SCREEN_H), FAINT)
    draw = ImageDraw.Draw(img)
    _sidebar(draw, [("Validations", True), ("Utilisateurs", False), ("Historique", False)])
    _header_bar(draw, "Validations en attente", "Super Admin")
    requests = [
        ("Suppression locataire", "Gestionnaire — M. Bah", "Il y a 2 h"),
        ("Modification loyer", "Admin — Bail #B-042", "Il y a 5 h"),
        ("Validation dépense", "45 000 000 GNF — Rénovation", "Hier"),
    ]
    y = 100
    for action, detail, when in requests:
        _rounded_rect(draw, (240, y, 1160, y + 90), 12, WHITE, BEBE, 1)
        draw.text((260, y + 16), action, font=_font(14, True), fill=HOF)
        draw.text((260, y + 42), detail, font=_font(12), fill=FOGGY)
        draw.text((260, y + 64), when, font=_font(10), fill=FOGGY)
        _rounded_rect(draw, (980, y + 28, 1060, y + 58), 8, SUCCESS)
        draw.text((992, y + 36), "Approuver", font=_font(10, True), fill=WHITE)
        _rounded_rect(draw, (1070, y + 28, 1140, y + 58), 8, FAINT, RAUSCH, 1)
        draw.text((1085, y + 36), "Rejeter", font=_font(10, True), fill=RAUSCH)
        y += 100
    path = ASSETS_DIR / "09_validations.png"
    img.save(path)
    return path


def generate_mock_screenshots() -> dict[str, Path]:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "login": mock_login(),
        "dashboard": mock_dashboard(),
        "buildings": mock_buildings(),
        "tenants": mock_tenants(),
        "payments": mock_payments(),
        "tenant_portal": mock_tenant_portal(),
        "listings": mock_public_listings(),
        "repairs": mock_repairs_kanban(),
        "validations": mock_validations(),
    }


def _rl_image(path: Path, width: float) -> RLImage:
    aspect = SCREEN_H / SCREEN_W
    return RLImage(str(path), width=width, height=width * aspect)


def _caption(text: str, styles) -> Paragraph:
    return Paragraph(f'<i>{text}</i>', styles["Caption"])


def _section(title: str, styles) -> list:
    return [Paragraph(title, styles["Heading1"]), Spacer(1, 6 * mm)]


def _subsection(title: str, styles) -> list:
    return [Paragraph(title, styles["Heading2"]), Spacer(1, 4 * mm)]


def _body(text: str, styles) -> Paragraph:
    return Paragraph(text, styles["Body"])


def _bullet_list(items: list[str], styles) -> list:
    return [Paragraph(f"• {item}", styles["Bullet"]) for item in items]


def _steps(steps: list[str], styles) -> list:
    return [Paragraph(f"<b>{i}.</b> {step}", styles["Body"]) for i, step in enumerate(steps, 1)]


def _role_table(styles) -> Table:
    data = [
        ["Rôle", "Accès principal", "Restrictions clés"],
        ["Super Administrateur", "Tout le système", "Seul à valider les actions sensibles"],
        ["Administrateur familial", "Gestion patrimoine", "Suppressions soumises à validation"],
        ["Propriétaire", "Consultation de ses biens", "Lecture seule"],
        ["Gestionnaire", "Locataires, paiements, dépenses", "Pas de vue financière globale"],
        ["Locataire", "Espace locataire", "Uniquement ses données"],
        ["Visiteur", "Annonces publiques", "Aucune donnée privée"],
    ]
    t = Table(data, colWidths=[4 * cm, 5.5 * cm, 6 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222222")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ebebeb")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f7")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def build_pdf(screens: dict[str, Path]) -> Path:
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Guide d'utilisation — Gestion Immo",
        author="Gestion Immobilière",
    )

    base = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle("Title", parent=base["Title"], fontSize=26, textColor=colors.HexColor("#222222"), spaceAfter=12, alignment=TA_CENTER),
        "Subtitle": ParagraphStyle("Subtitle", parent=base["Normal"], fontSize=13, textColor=colors.HexColor("#6a6a6a"), alignment=TA_CENTER, spaceAfter=20),
        "Heading1": ParagraphStyle("H1", parent=base["Heading1"], fontSize=18, textColor=colors.HexColor("#222222"), spaceBefore=14, spaceAfter=8),
        "Heading2": ParagraphStyle("H2", parent=base["Heading2"], fontSize=13, textColor=colors.HexColor("#222222"), spaceBefore=10, spaceAfter=6),
        "Body": ParagraphStyle("Body", parent=base["Normal"], fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=6),
        "Bullet": ParagraphStyle("Bullet", parent=base["Normal"], fontSize=10, leading=14, leftIndent=12, spaceAfter=3),
        "Caption": ParagraphStyle("Caption", parent=base["Normal"], fontSize=9, textColor=colors.HexColor("#6a6a6a"), alignment=TA_CENTER, spaceAfter=10),
        "TOC": ParagraphStyle("TOC", parent=base["Normal"], fontSize=11, leading=16, leftIndent=0),
    }

    story: list = []
    img_w = 16 * cm

    # ── Page de garde ──
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph("Guide d'utilisation", styles["Title"]))
    story.append(Paragraph("Gestion Immo", styles["Title"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Application de gestion immobilière", styles["Subtitle"]))
    story.append(Paragraph("Patrimoine • Locataires • Finances • Portails", styles["Subtitle"]))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(f"Version 1.0 — {date.today().strftime('%d/%m/%Y')}", styles["Subtitle"]))
    story.append(PageBreak())

    # ── Table des matières ──
    story.extend(_section("Table des matières", styles))
    toc = [
        "1. Introduction",
        "2. Prérequis et accès",
        "3. Les rôles utilisateurs",
        "4. Connexion et navigation",
        "5. Portail public (visiteurs)",
        "6. Tableau de bord staff",
        "7. Gestion du patrimoine (immeubles & logements)",
        "8. Locataires et baux",
        "9. Paiements, reçus et impayés",
        "10. Dépenses",
        "11. Réparations",
        "12. Documents",
        "13. Rapports financiers",
        "14. Validations et audit",
        "15. Notifications",
        "16. Espace locataire",
        "17. Administration (super admin)",
        "18. Profil et sécurité",
        "19. FAQ et dépannage",
    ]
    story.extend([Paragraph(line, styles["TOC"]) for line in toc])
    story.append(PageBreak())

    # ── 1. Introduction ──
    story.extend(_section("1. Introduction", styles))
    story.append(_body(
        "<b>Gestion Immo</b> est une application web de gestion de patrimoine immobilier, "
        "conçue pour les familles et gestionnaires en Guinée. Elle centralise la gestion des "
        "immeubles, logements, locataires, baux, paiements de loyer, impayés, dépenses, "
        "réparations, documents et rapports financiers. Les montants sont exprimés en "
        "<b>francs guinéens (GNF)</b>.",
        styles,
    ))
    story.append(_body(
        "La plateforme propose trois espaces distincts : un <b>portail public</b> pour les visiteurs, "
        "un <b>tableau de bord professionnel</b> pour le personnel (administrateurs, propriétaires, "
        "gestionnaires) et un <b>espace locataire</b> dédié aux locataires connectés.",
        styles,
    ))
    story.append(Spacer(1, 4 * mm))

    # ── 2. Prérequis ──
    story.extend(_section("2. Prérequis et accès", styles))
    story.extend(_subsection("2.1 Accès à l'application", styles))
    story.extend(_bullet_list([
        "Navigateur web récent (Chrome, Firefox, Edge, Safari)",
        "Connexion Internet stable",
        "Identifiants fournis par l'administrateur (e-mail + mot de passe)",
        "URL de l'application fournie par votre organisation",
    ], styles))
    story.append(Spacer(1, 4 * mm))
    story.extend(_subsection("2.2 Comptes de démonstration (environnement de test)", styles))
    story.append(_body(
        "En environnement de développement, des comptes de démonstration sont disponibles "
        "(mot de passe : <b>Demo123!</b>) : famille@, gestionnaire@, proprietaire@, locataire@, "
        "visiteur@ gestion-immo.local. Le super administrateur par défaut est "
        "<b>admin@gestion-immo.local</b> / <b>Admin123!</b>",
        styles,
    ))
    story.append(PageBreak())

    # ── 3. Rôles ──
    story.extend(_section("3. Les rôles utilisateurs", styles))
    story.append(_body(
        "Chaque utilisateur possède un rôle qui détermine les menus visibles et les actions autorisées. "
        "Des permissions granulaires peuvent être configurées individuellement par le super administrateur.",
        styles,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(_role_table(styles))
    story.append(PageBreak())

    # ── 4. Connexion ──
    story.extend(_section("4. Connexion et navigation", styles))
    story.extend(_subsection("4.1 Se connecter", styles))
    story.extend(_steps([
        "Accédez à la page <b>/login</b> ou cliquez sur « Connexion » depuis la page d'accueil.",
        "Saisissez votre adresse e-mail et votre mot de passe.",
        "Cliquez sur « Se connecter ».",
        "Vous êtes redirigé automatiquement selon votre rôle : staff → tableau de bord, locataire → espace locataire, visiteur → annonces.",
    ], styles))
    story.append(Spacer(1, 6 * mm))
    story.append(_rl_image(screens["login"], img_w))
    story.append(_caption("Figure 1 — Écran de connexion", styles))
    story.extend(_subsection("4.2 Navigation générale", styles))
    story.extend(_bullet_list([
        "<b>Barre latérale (sidebar)</b> : accès aux modules principaux, repliable sur desktop.",
        "<b>Cloche de notifications</b> : alertes en temps réel (loyers, impayés, réparations…).",
        "<b>Profil</b> : accessible via le menu utilisateur (/profil).",
        "<b>Déconnexion</b> : bouton en bas de la sidebar ou page /logout.",
    ], styles))
    story.append(PageBreak())

    # ── 5. Portail public ──
    story.extend(_section("5. Portail public (visiteurs)", styles))
    story.append(_body(
        "Sans connexion, les visiteurs peuvent consulter les logements disponibles, voir les photos "
        "et le loyer, et envoyer une demande de visite ou un message via le formulaire de contact.",
        styles,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(_rl_image(screens["listings"], img_w))
    story.append(_caption("Figure 2 — Liste des annonces publiques", styles))
    story.extend(_subsection("5.1 Demander une visite", styles))
    story.extend(_steps([
        "Parcourez les annonces sur /annonces.",
        "Cliquez sur un logement pour voir le détail (/annonces/[id]).",
        "Remplissez le formulaire (nom, téléphone, date souhaitée, message).",
        "Le gestionnaire reçoit la demande dans /dashboard/demandes-visite.",
    ], styles))
    story.append(PageBreak())

    # ── 6. Dashboard ──
    story.extend(_section("6. Tableau de bord staff", styles))
    story.append(_body(
        "Le tableau de bord (/dashboard) affiche une vue d'ensemble du patrimoine : KPIs, graphiques "
        "revenus/dépenses, taux d'occupation, alertes (impayés, baux expirants, réparations). "
        "Les propriétaires voient les données de leurs biens ; les gestionnaires n'accèdent pas "
        "aux indicateurs financiers globaux.",
        styles,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(_rl_image(screens["dashboard"], img_w))
    story.append(_caption("Figure 3 — Tableau de bord avec indicateurs et alertes", styles))
    story.extend(_subsection("6.1 Indicateurs disponibles", styles))
    story.extend(_bullet_list([
        "Nombre d'immeubles et de logements (appartements, magasins, bureaux)",
        "Taux d'occupation global et par immeuble",
        "Loyers attendus vs encaissés sur la période",
        "Total des impayés et nombre de locataires concernés",
        "Dépenses et bénéfice net",
        "Baux expirant dans les 30 prochains jours",
        "Réparations en cours",
    ], styles))
    story.append(PageBreak())

    # ── 7. Patrimoine ──
    story.extend(_section("7. Gestion du patrimoine", styles))
    story.extend(_subsection("7.1 Immeubles", styles))
    story.append(_body(
        "La section Immeubles (/dashboard/immeubles) permet de créer, modifier et consulter "
        "chaque bâtiment : code, nom, adresse, commune, quartier, photo, propriétaire et gestionnaire.",
        styles,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(_rl_image(screens["buildings"], img_w))
    story.append(_caption("Figure 4 — Liste des immeubles", styles))
    story.extend(_subsection("7.2 Créer un immeuble", styles))
    story.extend(_steps([
        "Cliquez sur « + Nouveau » ou accédez à /dashboard/immeubles/nouveau.",
        "Renseignez les informations (code unique, adresse, commune, quartier).",
        "Assignez un propriétaire et un gestionnaire si nécessaire.",
        "Ajoutez une photo et enregistrez.",
    ], styles))
    story.extend(_subsection("7.3 Logements", styles))
    story.append(_body(
        "Chaque logement (/dashboard/logements) est rattaché à un immeuble. Types : appartement, "
        "magasin, bureau. États : libre, occupé, réservé, en réparation. Depuis la fiche logement, "
        "vous pouvez définir le loyer, la caution, ajouter des photos, consulter l'historique des "
        "locataires et libérer le logement.",
        styles,
    ))
    story.append(PageBreak())

    # ── 8. Locataires et baux ──
    story.extend(_section("8. Locataires et baux", styles))
    story.extend(_subsection("8.1 Gestion des locataires", styles))
    story.append(_body(
        "La fiche locataire comprend : identité, téléphones, profession, pièce d'identité, contact "
        "d'urgence, photo. Vous pouvez créer un compte utilisateur locataire depuis sa fiche.",
        styles,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(_rl_image(screens["tenants"], img_w))
    story.append(_caption("Figure 5 — Liste des locataires", styles))
    story.extend(_subsection("8.2 Créer un locataire et un bail", styles))
    story.extend(_steps([
        "Créez d'abord l'immeuble et les logements concernés.",
        "Allez sur /dashboard/locataires/nouveau et remplissez la fiche.",
        "Créez le bail via /dashboard/baux/nouveau en sélectionnant le locataire et le logement.",
        "Le logement passe automatiquement à l'état « occupé ».",
        "Depuis le bail, générez les périodes de loyer et uploadez le contrat signé.",
    ], styles))
    story.extend(_subsection("8.3 Modifier ou résilier un bail", styles))
    story.extend(_bullet_list([
        "Modification du loyer : soumise à validation du super administrateur.",
        "Résiliation : accessible depuis /dashboard/baux/[id].",
        "Alertes automatiques pour les baux expirant bientôt.",
    ], styles))
    story.append(PageBreak())

    # ── 9. Paiements ──
    story.extend(_section("9. Paiements, reçus et impayés", styles))
    story.extend(_subsection("9.1 Enregistrer un paiement", styles))
    story.append(_body(
        "Modes acceptés : espèces, Orange Money, Wave, virement bancaire. Les paiements partiels "
        "et l'allocation sur plusieurs mois sont supportés.",
        styles,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(_rl_image(screens["payments"], img_w))
    story.append(_caption("Figure 6 — Liste et enregistrement des paiements", styles))
    story.extend(_steps([
        "Accédez à /dashboard/paiements/nouveau.",
        "Sélectionnez le locataire, le montant et le mode de paiement.",
        "Indiquez les mois couverts par le paiement.",
        "Joignez une preuve de paiement (capture, reçu) si nécessaire.",
        "Validez : un reçu PDF est généré automatiquement.",
    ], styles))
    story.extend(_subsection("9.2 Reçus", styles))
    story.extend(_bullet_list([
        "Consultation : /dashboard/recus",
        "Téléchargement PDF depuis la fiche reçu",
        "Envoi par e-mail ou lien WhatsApp au locataire",
        "Numérotation automatique des reçus",
    ], styles))
    story.extend(_subsection("9.3 Impayés", styles))
    story.append(_body(
        "Les impayés sont détectés automatiquement (synchronisation planifiée). Consultez "
        "/dashboard/impayes pour voir les retards par locataire, mois et montant. Résolvez "
        "un impayé après enregistrement du paiement correspondant.",
        styles,
    ))
    story.append(PageBreak())

    # ── 10. Dépenses ──
    story.extend(_section("10. Dépenses", styles))
    story.append(_body(
        "Enregistrez les dépenses par catégorie (réparation, peinture, plomberie, électricité, "
        "gardiennage, taxes…), immeuble, logement ou propriétaire. Joignez un justificatif.",
        styles,
    ))
    story.extend(_subsection("10.1 Workflow de validation", styles))
    story.extend(_steps([
        "Le gestionnaire enregistre une dépense (/dashboard/depenses/nouvelle).",
        "La dépense passe en statut « en attente de validation ».",
        "Le super administrateur valide ou rejette via /dashboard/depenses/validation.",
        "Une trace est conservée dans le journal d'audit.",
    ], styles))
    story.append(PageBreak())

    # ── 11. Réparations ──
    story.extend(_section("11. Réparations", styles))
    story.append(_body(
        "Les réparations peuvent être déclarées par le staff ou par le locataire. Chaque demande "
        "a un niveau d'urgence (faible, moyen, élevé) et suit un workflow en kanban.",
        styles,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(_rl_image(screens["repairs"], img_w))
    story.append(_caption("Figure 7 — Vue kanban des réparations", styles))
    story.extend(_subsection("11.1 Statuts", styles))
    story.extend(_bullet_list([
        "Nouvelle → Analyse → Technicien affecté → En cours → Terminée / Annulée",
        "Pièces jointes : photos, vidéos, documents",
        "Le locataire suit l'avancement depuis son espace",
    ], styles))
    story.append(PageBreak())

    # ── 12. Documents ──
    story.extend(_section("12. Documents", styles))
    story.append(_body(
        "La bibliothèque documentaire (/dashboard/documents) centralise contrats, pièces d'identité, "
        "reçus, états des lieux, actes et autres fichiers. Fonctionnalités : upload, prévisualisation, "
        "téléchargement et partage par lien sécurisé (/documents/shared/[token]).",
        styles,
    ))
    story.extend(_subsection("12.1 Types de documents", styles))
    story.extend(_bullet_list([
        "Contrats de bail",
        "Pièces d'identité des locataires",
        "Reçus de loyer",
        "États des lieux",
        "Factures et justificatifs de dépenses",
        "Documents administratifs (actes, autorisations…)",
    ], styles))
    story.append(PageBreak())

    # ── 13. Rapports ──
    story.extend(_section("13. Rapports financiers", styles))
    story.append(_body(
        "Générez des rapports depuis /dashboard/rapports/generer : journalier, hebdomadaire, "
        "mensuel ou annuel. Filtrez par immeuble, propriétaire, locataire ou gestionnaire. "
        "Export disponible en PDF et Excel.",
        styles,
    ))
    story.extend(_steps([
        "Accédez à Rapports → Générer un rapport.",
        "Choisissez le type et la période.",
        "Appliquez les filtres souhaités.",
        "Générez et consultez le rapport (/dashboard/rapports/[id]).",
        "Téléchargez en PDF ou Excel.",
    ], styles))
    story.append(PageBreak())

    # ── 14. Validations ──
    story.extend(_section("14. Validations et audit", styles))
    story.append(_body(
        "Certaines actions sensibles nécessitent l'approbation du super administrateur : "
        "suppression de paiement, modification de montant, suppression de locataire, changement "
        "de propriétaire, modification de contrat, validation de dépense importante, annulation "
        "de reçu, suppression de document.",
        styles,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(_rl_image(screens["validations"], img_w))
    story.append(_caption("Figure 8 — File d'attente des validations (super admin)", styles))
    story.extend(_subsection("14.1 Suivi des demandes", styles))
    story.extend(_bullet_list([
        "Staff : /dashboard/mes-demandes pour suivre ses propres demandes",
        "Super admin : /dashboard/validations pour approuver ou rejeter",
        "Historique complet : /dashboard/historique (super admin uniquement)",
    ], styles))
    story.append(PageBreak())

    # ── 15. Notifications ──
    story.extend(_section("15. Notifications", styles))
    story.append(_body(
        "Les notifications in-app sont accessibles via la cloche en haut à droite. "
        "Configurez vos préférences sur /dashboard/parametres/notifications : choix des "
        "événements (loyer exigible, retard, bail expirant, réparation, paiement, reçu, dépense, "
        "document…) et des canaux (in-app, e-mail, WhatsApp).",
        styles,
    ))
    story.append(PageBreak())

    # ── 16. Espace locataire ──
    story.extend(_section("16. Espace locataire", styles))
    story.append(_body(
        "Les locataires connectés accèdent à /espace-locataire avec un menu dédié : "
        "mon logement, mon contrat, paiements, reçus, impayés, réparations, documents, messages et notifications.",
        styles,
    ))
    story.append(Spacer(1, 6 * mm))
    story.append(_rl_image(screens["tenant_portal"], img_w))
    story.append(_caption("Figure 9 — Tableau de bord de l'espace locataire", styles))
    story.extend(_subsection("16.1 Actions du locataire", styles))
    story.extend(_bullet_list([
        "Consulter son logement et son contrat de bail",
        "Voir l'historique des paiements et télécharger les reçus PDF",
        "Vérifier les éventuels impayés",
        "Signaler une panne (/espace-locataire/reparations/nouvelle)",
        "Lire les messages et avis du gestionnaire",
        "Télécharger les documents partagés",
    ], styles))
    story.append(PageBreak())

    # ── 17. Administration ──
    story.extend(_section("17. Administration (super admin)", styles))
    story.extend(_subsection("17.1 Gestion des utilisateurs", styles))
    story.extend(_bullet_list([
        "Créer, modifier, désactiver des utilisateurs (/dashboard/utilisateurs)",
        "Attribuer un rôle (super_admin, admin_familial, proprietaire, gestionnaire, locataire, visiteur)",
        "Réinitialiser un mot de passe",
        "Configurer des permissions granulaires (/dashboard/utilisateurs/[id]/permissions)",
    ], styles))
    story.extend(_subsection("17.2 Profils propriétaires", styles))
    story.append(_body(
        "La section Propriétaires (/dashboard/proprietaires) permet de gérer les membres de la "
        "famille et leurs affectations aux immeubles.",
        styles,
    ))
    story.extend(_subsection("17.3 Demandes de visite", styles))
    story.append(_body(
        "Traitez les demandes de visite des visiteurs depuis /dashboard/demandes-visite : "
        "confirmer, reprogrammer, annuler ou marquer comme terminée.",
        styles,
    ))
    story.append(PageBreak())

    # ── 18. Profil ──
    story.extend(_section("18. Profil et sécurité", styles))
    story.extend(_subsection("18.1 Modifier son profil", styles))
    story.extend(_steps([
        "Accédez à /profil depuis le menu utilisateur.",
        "Consultez vos informations de compte (nom, e-mail, rôle).",
        "Pour changer le mot de passe, saisissez l'ancien et le nouveau mot de passe.",
        "Après changement de mot de passe, une reconnexion est requise.",
    ], styles))
    story.extend(_subsection("18.2 Bonnes pratiques de sécurité", styles))
    story.extend(_bullet_list([
        "Utilisez un mot de passe fort (8+ caractères, majuscules, chiffres)",
        "Ne partagez jamais vos identifiants",
        "Déconnectez-vous sur les postes partagés",
        "Signalez toute activité suspecte à l'administrateur",
    ], styles))
    story.append(PageBreak())

    # ── 19. FAQ ──
    story.extend(_section("19. FAQ et dépannage", styles))
    faq = [
        ("Je ne peux pas me connecter.", "Vérifiez e-mail et mot de passe. Contactez l'administrateur pour une réinitialisation."),
        ("Je ne vois pas certains menus.", "Votre rôle détermine les menus visibles. Seul le super admin voit Validations et Utilisateurs."),
        ("Un paiement n'apparaît pas.", "Vérifiez qu'il est validé. Les paiements en attente apparaissent avec ce statut."),
        ("Comment envoyer un reçu au locataire ?", "Ouvrez la fiche reçu et utilisez les boutons Envoyer par e-mail ou WhatsApp."),
        ("Une suppression est bloquée.", "Les suppressions sensibles passent par le workflow de validation super admin."),
        ("Les montants sont en quelle devise ?", "Tous les montants sont en francs guinéens (GNF)."),
        ("Comment signaler une panne ?", "Locataire : Espace locataire → Réparations → Signaler. Staff : Dashboard → Réparations → Nouvelle."),
    ]
    for q, a in faq:
        story.append(Paragraph(f"<b>Q : {q}</b>", styles["Body"]))
        story.append(Paragraph(f"R : {a}", styles["Body"]))
        story.append(Spacer(1, 4 * mm))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        "<i>Document généré automatiquement — Gestion Immo © 2026</i>",
        ParagraphStyle("Footer", parent=styles["Body"], alignment=TA_CENTER, textColor=colors.HexColor("#6a6a6a")),
    ))

    doc.build(story)
    return OUTPUT_PDF


def main():
    print("Génération des maquettes UI...")
    screens = generate_mock_screenshots()
    print(f"  {len(screens)} captures créées dans {ASSETS_DIR}")

    print("Construction du PDF...")
    pdf_path = build_pdf(screens)
    size_kb = pdf_path.stat().st_size // 1024
    print(f"Guide généré : {pdf_path} ({size_kb} Ko)")


if __name__ == "__main__":
    main()
