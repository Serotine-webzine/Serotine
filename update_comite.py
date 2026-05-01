#!/usr/bin/env python3
"""
update_comite.py — Mise à jour automatique de comite.html depuis membres.csv
=============================================================================
Usage: python update_comite.py membres.csv

Lit membres.csv et met à jour comite.html avec :
  - Une section unique "L'équipe — Membres du projet" regroupant comité ET membres projet
    (les membres du comité reçoivent une pastille "Comité de rédaction")
  - La section "Anciens membres" (cachée par défaut)

Colonnes attendues dans le CSV :
  Nom, Rôle, Biographie, URL, Type, Image

Valeurs valides pour la colonne Type :
  comite            → Comité de rédaction (affiché avec pastille dans la section équipe)
  ancien_membre     → Anciens membres du comité de rédaction
  membre_projet     → Membres du projet (affichés classiquement dans la section équipe)

Exécutez depuis le dossier racine du site (là où se trouve comite.html).
"""

import csv
import os
import re
import sys
from html import escape

# ══════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════

COMITE_FILE   = "comite.html"
VALID_TYPES   = ("comite", "ancien_membre", "membre_projet")
FIELDS        = ("Nom", "Rôle", "Biographie", "URL", "Type", "Image")
DEFAULT_IMAGE = ""  # Laisser vide = initiales affichées à la place

LINK_ICON = "media/link.svg"


# ══════════════════════════════════════════════
#  CSV LOADER + VALIDATOR
# ══════════════════════════════════════════════

def load_membres(csv_path: str) -> dict[str, list[dict]]:
    """
    Parse membres.csv.
    Retourne un dict { type: [membre, ...] } trié par type.
    """
    grouped: dict[str, list] = {t: [] for t in VALID_TYPES}
    warnings = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, skipinitialspace=True)

        # Vérifier les colonnes
        if reader.fieldnames is None:
            print("  ✗ Le fichier CSV est vide.")
            sys.exit(1)

        missing = [c for c in FIELDS if c not in reader.fieldnames]
        if missing:
            print(f"  ✗ Colonnes manquantes dans le CSV : {missing}")
            print(f"    Colonnes trouvées : {list(reader.fieldnames)}")
            sys.exit(1)

        for line_num, row in enumerate(reader, start=2):
            nom  = row.get("Nom", "").strip()
            type_ = row.get("Type", "").strip().lower()

            if not nom:
                warnings.append(f"  ⚠  Ligne {line_num} : colonne 'Nom' vide — ligne ignorée.")
                continue

            if type_ not in VALID_TYPES:
                warnings.append(
                    f"  ⚠  Ligne {line_num} ({nom}) : type inconnu '{type_}' "
                    f"— valeurs attendues : {VALID_TYPES} — ligne ignorée."
                )
                continue

            membre = {
                "nom":   nom,
                "role":  row.get("Rôle", "").strip(),
                "bio":   row.get("Biographie", "").strip(),
                "url":   row.get("URL", "").strip(),
                "type":  type_,
                "image": row.get("Image", "").strip(),
            }
            grouped[type_].append(membre)

    if warnings:
        print(f"\n{'─'*60}")
        print(f"⚠  {len(warnings)} avertissement(s) CSV :")
        for w in warnings:
            print(w)
        print(f"{'─'*60}\n")

    total = sum(len(v) for v in grouped.values())
    print(f"  ✓ {total} membres chargés  "
          f"({len(grouped['comite'])} comité, "
          f"{len(grouped['ancien_membre'])} anciens, "
          f"{len(grouped['membre_projet'])} projet)")
    return grouped


# ══════════════════════════════════════════════
#  HTML CARD GENERATOR
# ══════════════════════════════════════════════

def icon_for_url(url: str) -> str:
    """Retourne toujours l'icône de lien générique."""
    return LINK_ICON


def initials(nom: str) -> str:
    """Retourne les initiales (max 2 lettres) pour l'avatar de remplacement."""
    parts = nom.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return nom[:2].upper()


def render_avatar(membre: dict) -> str:
    """Génère le bloc avatar : photo si dispo, sinon icône par défaut."""
    img = membre["image"]
    if img:
        return (
            f'<div class="member-avatar">'
            f'<img src="{escape(img)}" alt="{escape(membre["nom"])}" '
            f'class="member-photo" loading="lazy"></div>'
        )
    return (
        f'<div class="member-avatar">'
        f'<img src="media/icon_rond.png" alt="{escape(membre["nom"])}" '
        f'class="member-photo" loading="lazy"></div>'
    )


def render_card(membre: dict, compact: bool = False, show_badge: bool = False) -> str:
    """Génère une carte membre HTML.

    show_badge=True  → affiche la pastille "Comité de rédaction" sous le nom.
    """
    avatar_html = render_avatar(membre)

    badge_html = (
        '<span class="badge-comite">Comité de rédaction</span>'
        if show_badge else ""
    )

    link_html = ""
    if membre["url"]:
        icon = icon_for_url(membre["url"])
        link_html = (
            f'<div class="hero-social">'
            f'<a href="{escape(membre["url"])}" target="_blank" rel="noopener" '
            f'aria-label="Profil de {escape(membre["nom"])}">'
            f'<img src="{icon}" alt="Lien" class="logo-xsmall"></a>'
            f'</div>'
        )

    bio_html = (
        f'<div class="member-bio">{escape(membre["bio"])}</div>'
        if membre["bio"] and not compact else ""
    )

    compact_cls = " compact" if compact else ""
    return f"""\
      <div class="member-card{compact_cls}">
        {avatar_html}
        <div class="member-name">{escape(membre["nom"])}</div>
        {badge_html}
        <div class="member-role">{escape(membre["role"])}</div>
        {bio_html}
        {link_html}
      </div>"""


def render_members_grid(membres: list[dict], compact: bool = False,
                        badge_types: tuple = ()) -> str:
    """
    Génère la grille HTML.
    badge_types : ensemble de valeurs `type` pour lesquelles afficher la pastille.
    """
    cards = "\n".join(
        render_card(m, compact, show_badge=(m["type"] in badge_types))
        for m in membres
    )
    return f'    <div class="members-grid">\n{cards}\n    </div>'


# ══════════════════════════════════════════════
#  SECTION BUILDERS
# ══════════════════════════════════════════════

def build_anciens_section(membres: list[dict]) -> str:
    if not membres:
        return "    <!-- ANCIENS_START -->\n    <!-- ANCIENS_END -->"
    grid = render_members_grid(membres, compact=True)
    return f"""\
    <!-- ANCIENS_START -->
    <details class="anciens-details">
      <summary class="section-title anciens-summary">
        Anciens membres
        <span class="toggle-icon" aria-hidden="true">▾</span>
      </summary>
{grid}
    </details>
    <!-- ANCIENS_END -->"""


def build_projet_section(membres_comite: list[dict], membres_projet: list[dict]) -> str:
    """
    Regroupe comité + membres projet dans une seule section.
    Les membres du comité reçoivent la pastille "Comité de rédaction".
    """
    tous = membres_comite + membres_projet
    if not tous:
        return "    <!-- PROJET_START -->\n    <!-- PROJET_END -->"
    grid = render_members_grid(tous, badge_types=("comite",))
    return f"""\
    <!-- PROJET_START -->
    <h2 class="section-title">L'équipe <small>Membres du projet</small></h2>
{grid}
    <!-- PROJET_END -->"""


# ══════════════════════════════════════════════
#  STYLES À INJECTER
# ══════════════════════════════════════════════

EXTRA_CSS = """\
    /* AVATAR */
    .member-avatar { width: 52px; height: 52px; border-radius: 50%; overflow: hidden; margin-bottom: .75rem; flex-shrink: 0; }
    .member-photo { width: 100%; height: 100%; object-fit: cover; }
    .member-initials {
      display: flex; align-items: center; justify-content: center;
      background: var(--ink); color: var(--paper);
      font-family: 'Playfair Display', serif; font-size: 1.1rem; font-weight: 400;
    }

    /* PASTILLE COMITÉ DE RÉDACTION */
    .badge-comite {
      display: inline-block;
      font-size: .65rem; font-weight: 200; letter-spacing: .04em; text-transform: uppercase;
      border: 1px solid var(--ink);
      border-radius: 3px; padding: .15em .5em;
      margin-bottom: .35rem;
      vertical-align: middle;
    }

    /* CARTE COMPACTE (anciens membres) */
    .member-card.compact { padding: 1rem 1.2rem; }
    .member-card.compact .member-avatar { width: 36px; height: 36px; font-size: .8rem; }

    /* ANCIENS MEMBRES — section dépliable */
    .anciens-details { margin-bottom: 3.5rem; }
    .anciens-details > .members-grid { margin-top: 1.5rem; }
    .anciens-summary {
      cursor: pointer; list-style: none; display: flex;
      align-items: baseline; gap: .75rem;
      margin-bottom: 0 !important;
    }
    .anciens-summary::-webkit-details-marker { display: none; }
    .anciens-summary .toggle-icon { font-size: .9rem; color: var(--muted); transition: transform .25s; }
    .anciens-details[open] .toggle-icon { transform: rotate(180deg); }

    /* CSS INJECTED BY update_comite.py — ne pas supprimer cette ligne */"""

CSS_MARKER = "/* CSS INJECTED BY update_comite.py — ne pas supprimer cette ligne */"


# ══════════════════════════════════════════════
#  INJECTOR
# ══════════════════════════════════════════════

def inject_comite(grouped: dict[str, list], comite_path: str) -> None:
    """Patche comite.html en place avec les sections fusionnées."""
    if not os.path.exists(comite_path):
        print(f"  ✗ {comite_path} introuvable — injection abandonnée.")
        sys.exit(1)

    with open(comite_path, "r", encoding="utf-8") as f:
        html = f.read()

    changed = False

    # ── 1. Injecter / mettre à jour le CSS ──────────────────────────────
    if CSS_MARKER not in html:
        html = html.replace("    /* MEMBER GRID */", EXTRA_CSS + "\n\n    /* MEMBER GRID */", 1)
        if CSS_MARKER not in html:
            # Fallback : insérer avant </style>
            html = html.replace("  </style>", EXTRA_CSS + "\n  </style>", 1)
        print("  ✓ Styles CSS injectés")
        changed = True
    else:
        old_css = re.search(r'/\* AVATAR \*/.*?/\* CSS INJECTED BY update_comite\.py[^\*]*\*/', html, re.DOTALL)
        if old_css:
            html = html[:old_css.start()] + EXTRA_CSS + html[old_css.end():]
            print("  ✓ Styles CSS mis à jour")
            changed = True

    # ── 2. Section comité séparée : supprimée / ignorée ──────────────────
    # comité et projet sont désormais fusionnés dans PROJET_START/END.
    # Si des balises COMITE_START/END subsistent dans le HTML, on les efface.
    match_comite = re.search(r'<!-- COMITE_START -->.*?<!-- COMITE_END -->', html, re.DOTALL)
    if match_comite:
        html = html[:match_comite.start()] + html[match_comite.end():]
        print("  ℹ  Ancienne section COMITE_START/END supprimée (fusionnée dans la section équipe)")
        changed = True

    # ── 3. Injecter section anciens ──────────────────────────────────────
    new_anciens = build_anciens_section(grouped["ancien_membre"])
    match = re.search(r'<!-- ANCIENS_START -->.*?<!-- ANCIENS_END -->', html, re.DOTALL)
    if match:
        html = html[:match.start()] + new_anciens.strip() + html[match.end():]
        print(f"  ✓ Section anciens mise à jour ({len(grouped['ancien_membre'])} membres)")
        changed = True
    else:
        print("  ⚠  Repère ANCIENS_START introuvable — section anciens non injectée.")
        print("     Ajoutez <!-- ANCIENS_START --> et <!-- ANCIENS_END --> dans comite.html")

    # ── 4. Injecter section équipe unifiée (comité + projet) ─────────────
    new_projet = build_projet_section(grouped["comite"], grouped["membre_projet"])
    match = re.search(r'<!-- PROJET_START -->.*?<!-- PROJET_END -->', html, re.DOTALL)
    if match:
        html = html[:match.start()] + new_projet.strip() + html[match.end():]
        nb = len(grouped["comite"]) + len(grouped["membre_projet"])
        print(f"  ✓ Section équipe mise à jour ({nb} membres : "
              f"{len(grouped['comite'])} comité + {len(grouped['membre_projet'])} projet)")
        changed = True
    else:
        print("  ⚠  Repère PROJET_START introuvable — section équipe non injectée.")
        print("     Ajoutez <!-- PROJET_START --> et <!-- PROJET_END --> dans comite.html")

    if changed:
        with open(comite_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"\n  ✅  {comite_path} mis à jour avec succès.")
    else:
        print("\n  ℹ  Aucune modification apportée à comite.html.")


# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("Usage : python update_comite.py membres.csv")
        sys.exit(1)

    csv_path    = sys.argv[1]
    comite_path = sys.argv[2] if len(sys.argv) > 2 else COMITE_FILE

    if not os.path.exists(csv_path):
        print(f"  ✗ Fichier introuvable : {csv_path}")
        sys.exit(1)

    print(f"\n📂  Chargement de {csv_path}…")
    grouped = load_membres(csv_path)

    print(f"\n📄  Mise à jour de {comite_path}…")
    inject_comite(grouped, comite_path)
    print()


if __name__ == "__main__":
    main()
