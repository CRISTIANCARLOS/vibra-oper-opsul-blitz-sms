import json
import os
import re

SCRATCH_DIR = r"C:\Users\CE9X\.gemini\antigravity-cli\brain\8cae6e32-993e-4789-bd1b-881b43fbd9e1\scratch"

USER_BASES_RAW = """
AIBET
AIÇAI
AICAMP
AICAR
AIEMB
AIJEQ
AILAN
AILIS
AIMAB
AIMAC
AIMAP
AIMIR
AIPAF
AIRIB
AIRIN
AISUAP
AITER
ARBAL
ARCAB
ARCAP
ARCAS
AICAR
ARFLO
ARGOV
ARGUAR
ARJEQ
ARJOI
ARJOR
ARJUR
ARLAG
ARLAN
ARLEM
ARMOC
ARNIQ
ARNOP
ARORI
ARREM
ARRIG
ARRON
ARSUL
ARTAJ
ARUBA
ARUBA II
ARUBE
ARUNA
BABET/TEBET
BABRAS
BACAD
BAÇAI
BACAJ
BACAM
BACRO
BACUB
BADEN
BADUC
BAERI
BAFOR
BAGAM
BAGUA
BAIBA
BAJUI
BALEM
BALIS
BALON
BAMAB
BAMAC
BAMAN
BAMAT
BAMON
BANOAS
BAPLAN
BAPON
BARAC
BARIB
BARIX
BASEC
BASPA
BASULII
BATAL
BATAQ
BAURU
BAV1
BAV2
BAV3
BAVAP
BAVEL
BAVIC
BAVIT
BAVOL
BEAPE
BEGON
BEJUA
BERAV
BETER
CCPP
CERAQ
DEAÇU
DECAE
DEJAP
DEMOR
DERIO
DEROD
EPS
GEI - Gerência Industrial
GEOPAR
RAALT
RAARG
RAARU
RAAUS
RABAA
RABAU
RABEL
RABIO
RABOV
RACAB
RACAC
RACAJ
RACAN
RACATI
RACAX
RACGH
RACGR
RACHI
RACMP
RACMT
RACOR
RACRI
RACRU
RACUR
RACWB
RADOU
RAFLO
RAFME
RAFON
RAFOR
RAFOZ
RAFPO
RAGAR
RAGOA
RAGON
RAGUA
RAGUR
RAITU
RAJAS
RAJER
RAJIP
RAJUA
RAJUF
RALAG
RALON
RAMAB
RAMAC
RAMAN
RAMAR
RAMAT
RAMCL
RAMCP
RAMEA
RANAT
RANAV
RAPAB
RAPAL
RAPEL
RAPLU
RAPMG
RAPNZ
RAPRE
RAPRU
RAPSU
RAPUC
RAPVH
RAQNS
RARAL
RAREC
RARIA
RARIB
RARIP2
RASAN
RASCA
RASCR
RASDU
RASEG
RASEN
RASGA
RASIN
RASJO
RASLU
RASPR
RATAB
RATEF
RATER
RATUBA
RAUBE
RAULA
RAURU
RAVAR
RAVARI
RAVIC
RAVIL
RAVIT
SEDE
AICAMP
AICAR
AILAN
AIMAB
AIMAP
AIMIR
AIPAF
AIREM
AIRIB
AIRIN
AISUAP
AITER
ARBRIO
ARCAB
ARCAS
ARCHAP
ARFLO
ARGOV
ARJEQ
ARJOI
ARJOR
ARLAG
ARLEM
ARMOC
ARNOP
ARRIG
ARRIV
ARRON
ARTAJ
ARUBE
ARUNA
BALIS
BAMAT
BEJUA
"""

def normalize_name(name):
    if not name:
        return ""
    n = re.sub(r"\s+", " ", str(name).strip())
    n = n.strip(";-., ")
    if not n or len(n) < 2:
        return ""
    if n.isupper() or n.islower():
        parts = n.title().split(" ")
        lower_words = {"De", "Da", "Do", "Das", "Dos", "E"}
        n = " ".join([p.lower() if i > 0 and p in lower_words else p for i, p in enumerate(parts)])
    return n

def main():
    items_path = os.path.join(SCRATCH_DIR, "blitz_all_items.json")
    with open(items_path, "r", encoding="utf-8-sig") as f:
        sp_items = json.load(f)

    # 1. Deduplicate Bases
    base_set = set()
    for line in USER_BASES_RAW.splitlines():
        b = line.strip()
        if b:
            base_set.add(b)
    for it in sp_items:
        if isinstance(it.get("Base"), dict) and it["Base"].get("Value"):
            base_set.add(it["Base"]["Value"].strip())
    bases = sorted(base_set)

    # 2. Extract Responsáveis sorted by frequency/alphabetical
    resp_map = {}
    transp_counts = {}
    for it in sp_items:
        raw_name = it.get("Nomedorespons_x00e1_velpelaBlitz")
        resp_obj = it.get("Respons_x00e1_velpelaBlitz")
        if not raw_name and isinstance(resp_obj, dict):
            raw_name = resp_obj.get("DisplayName")
        if not raw_name and isinstance(it.get("Author"), dict):
            raw_name = it["Author"].get("DisplayName")
        cname = normalize_name(raw_name)
        base_val = it["Base"].get("Value", "") if isinstance(it.get("Base"), dict) else ""
        if cname:
            k = cname.upper()
            if k not in resp_map:
                resp_map[k] = {"nome": cname, "base": base_val, "count": 1}
            else:
                resp_map[k]["count"] += 1
                if base_val:
                    resp_map[k]["base"] = base_val

        tr = (it.get("Transportadora") or "").strip()
        if tr and len(tr) >= 2:
            tk = tr.upper()
            transp_counts[tk] = transp_counts.get(tk, 0) + 1

    responsaveis = sorted(resp_map.values(), key=lambda x: (-x["count"], x["nome"]))
    top_transp = [k.title() for k, _ in sorted(transp_counts.items(), key=lambda x: -x[1])[:60]]

    bases_json = json.dumps(bases, ensure_ascii=False)
    resp_json = json.dumps(responsaveis, ensure_ascii=False)
    transp_json = json.dumps(top_transp, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>OPER_OPSUL | Blitz de SMS — Vibra Energia</title>
  <style>
    :root {{
      /* Paleta Oficial Vibra Energia (Design System) */
      --vd-primary: #004415;     /* VD verde escuro (~60% dominante: títulos, faixas escuras, ícones, capa) */
      --vg-secondary: #268200;   /* VG verde (Rótulo da seção, coluna Raciocínio, barras laterais, setas) */
      --vy-accent: #FEDC00;      /* VY amarelo (Destaque: um item por grupo, selos, paginação, barra de decisão) */
      --vb-digital: #0000FF;     /* VB azul (Digital: Teams, etapas Receber e Alertar, Próximo passo) */
      --w-white: #FFFFFF;        /* W branco (Cards e texto sobre fundo escuro) */
      --ink: #0B2A14;            /* INK (Texto principal escuro) */
      --mut: #55665A;            /* MUT (Subtítulos, legendas, fontes) */
      --soft: #F2F7EE;           /* SOFT (Fundo de cards secundários) */
      --line: #DCE7D5;           /* LINE (Bordas de cards) */
      --bg: #FAFCF8;             /* BG (Fundo geral) */
      --dark2: #0B3218;          /* DARK2 (Caixa de autoria na capa) */
      --crit: #D92D20;           /* CRIT (Gravidade crítica) */
      --alto: #F07B00;           /* ALTO (Gravidade alta) */
      --med: #E8B400;            /* MED (Gravidade média) */

      --font-main: "Acumin Pro", Arial, sans-serif;
      --shadow-card: 0 2px 6px rgba(0, 0, 0, 0.10);
      --radius-card: 0px;
      --radius-pill: 9999px;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: var(--font-main);
      background-color: var(--bg);
      color: var(--ink);
      min-height: 100vh;
      line-height: 1.45;
      -webkit-font-smoothing: antialiased;
    }}

    /* === TOPO / CAPA DOMINANTE (#004415 - 60% Hierarquia Visual) === */
    .hero-header {{
      background-color: var(--vd-primary);
      color: var(--w-white);
      border-bottom: 4px solid var(--vy-accent);
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18);
    }}

    .hero-top-bar {{
      background-color: var(--dark2);
      padding: 8px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      letter-spacing: 0.6px;
      text-transform: uppercase;
      border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    }}

    .hero-top-bar .badge-pill {{
      background-color: var(--vy-accent);
      color: var(--ink);
      font-weight: 700;
      padding: 2px 10px;
      border-radius: var(--radius-pill);
      font-size: 10px;
    }}

    .hero-main {{
      max-width: 1080px;
      margin: 0 auto;
      padding: 18px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }}

    .hero-title-group {{
      display: flex;
      align-items: center;
      gap: 16px;
    }}

    .hero-icon-box {{
      width: 48px;
      height: 48px;
      background-color: var(--dark2);
      border-left: 4px solid var(--vy-accent);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}

    .hero-title-group h1 {{
      font-size: 24px;
      font-weight: 700;
      color: var(--w-white);
      letter-spacing: -0.3px;
    }}

    .hero-title-group p {{
      font-size: 13px;
      color: #D2E5D6;
      margin-top: 2px;
    }}

    .hero-stats {{
      display: flex;
      gap: 12px;
      align-items: center;
    }}

    .stat-box {{
      background-color: var(--dark2);
      border: 1px solid rgba(255, 255, 255, 0.15);
      padding: 8px 14px;
      text-align: right;
    }}

    .stat-box .stat-num {{
      font-size: 18px;
      font-weight: 700;
      color: var(--vy-accent);
      display: block;
      line-height: 1.1;
    }}

    .stat-box .stat-lbl {{
      font-size: 10px;
      color: #D2E5D6;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    /* === BARRA DE PROGRESSO E STATUS === */
    .progress-strip {{
      background-color: var(--soft);
      border-bottom: 1px solid var(--line);
      padding: 10px 24px;
    }}

    .progress-inner {{
      max-width: 1080px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
    }}

    .step-pills {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}

    .step-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 12px;
      border-radius: var(--radius-pill);
      font-size: 11px;
      font-weight: 700;
      background-color: var(--w-white);
      border: 1px solid var(--line);
      color: var(--mut);
    }}

    .step-pill.active {{
      background-color: var(--vd-primary);
      color: var(--w-white);
      border-color: var(--vd-primary);
    }}

    .step-pill .num {{
      background-color: var(--vy-accent);
      color: var(--ink);
      width: 18px;
      height: 18px;
      border-radius: var(--radius-pill);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      font-weight: 800;
    }}

    /* === CONTAINER PRINCIPAL === */
    .container {{
      max-width: 1080px;
      margin: 24px auto 64px;
      padding: 0 20px;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}

    /* === CARDS DE SEÇÃO (Radius 0, Sombra Externa, Barra Lateral #268200) === */
    .section-card {{
      background-color: var(--w-white);
      border: 1px solid var(--line);
      border-left: 6px solid var(--vg-secondary);
      border-radius: var(--radius-card);
      box-shadow: var(--shadow-card);
    }}

    .section-header {{
      background-color: var(--vd-primary);
      color: var(--w-white);
      padding: 14px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }}

    .section-header-left {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .section-num {{
      background-color: var(--vy-accent);
      color: var(--ink);
      font-weight: 800;
      font-size: 12px;
      padding: 3px 10px;
      border-radius: var(--radius-pill);
      letter-spacing: 0.4px;
    }}

    .section-title {{
      font-size: 16px;
      font-weight: 700;
      letter-spacing: 0.2px;
    }}

    .section-tag {{
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.7px;
      background-color: var(--vg-secondary);
      color: var(--w-white);
      padding: 3px 10px;
      border-radius: var(--radius-pill);
      font-weight: 700;
    }}

    .section-body {{
      padding: 22px 20px;
    }}

    /* === GRID DE CAMPOS === */
    .form-grid {{
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 18px;
    }}

    .col-12 {{ grid-column: span 12; }}
    .col-6 {{ grid-column: span 6; }}
    .col-4 {{ grid-column: span 4; }}
    .col-8 {{ grid-column: span 8; }}

    @media (max-width: 768px) {{
      .col-6, .col-4, .col-8 {{ grid-column: span 12; }}
    }}

    .field-group {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      position: relative;
    }}

    .field-label-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }}

    .field-label {{
      font-size: 12px;
      font-weight: 700;
      color: var(--ink);
      text-transform: uppercase;
      letter-spacing: 0.4px;
    }}

    .badge-req {{
      font-size: 10px;
      font-weight: 700;
      color: var(--crit);
      background-color: #FEECEB;
      border: 1px solid #F8C9C5;
      padding: 1px 8px;
      border-radius: var(--radius-pill);
    }}

    .badge-lock {{
      font-size: 10px;
      font-weight: 700;
      color: #334155;
      background-color: #F1F5F9;
      border: 1px solid #CBD5E1;
      padding: 1px 8px;
      border-radius: var(--radius-pill);
    }}

    .field-hint {{
      font-size: 11px;
      color: var(--mut);
    }}

    input[type="text"],
    input[type="date"],
    input[type="email"],
    textarea,
    select {{
      width: 100%;
      padding: 11px 14px;
      font-family: var(--font-main);
      font-size: 14px;
      color: var(--ink);
      background-color: var(--w-white);
      border: 1.5px solid var(--line);
      border-radius: var(--radius-card);
      transition: border-color 0.15s, box-shadow 0.15s;
    }}

    input:focus,
    textarea:focus,
    select:focus {{
      outline: none;
      border-color: var(--vd-primary);
      box-shadow: 0 0 0 3px rgba(0, 68, 21, 0.14);
    }}

    input[readonly],
    input:read-only {{
      background-color: #F8FAFC !important;
      color: #334155 !important;
      cursor: not-allowed !important;
      border-color: #CBD5E1 !important;
      user-select: none;
    }}

    input.input-error,
    textarea.input-error,
    .combobox-wrapper.input-error input {{
      border-color: var(--crit) !important;
      background-color: #FFFBFB;
    }}

    .error-msg {{
      font-size: 11px;
      font-weight: 700;
      color: var(--crit);
      display: none;
      margin-top: 2px;
    }}

    .error-msg.visible {{
      display: block;
    }}

    /* === COMBOBOX FUZZY SEARCH (BASE E RESPONSÁVEL) === */
    .combobox-wrapper {{
      position: relative;
    }}

    .combobox-input-box {{
      position: relative;
      display: flex;
      align-items: center;
    }}

    .combobox-input-box input {{
      padding-right: 78px;
    }}

    .combobox-actions {{
      position: absolute;
      right: 8px;
      display: flex;
      align-items: center;
      gap: 4px;
    }}

    .combo-btn {{
      background: var(--soft);
      border: 1px solid var(--line);
      color: var(--ink);
      font-size: 11px;
      font-weight: 700;
      padding: 4px 8px;
      cursor: pointer;
    }}

    .combo-btn:hover {{
      background: var(--vd-primary);
      color: var(--w-white);
    }}

    .fuzzy-dropdown {{
      position: absolute;
      top: calc(100% + 2px);
      left: 0;
      right: 0;
      background-color: var(--w-white);
      border: 2px solid var(--vd-primary);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
      max-height: 290px;
      overflow-y: auto;
      z-index: 90;
      display: none;
    }}

    .fuzzy-dropdown.open {{
      display: block;
    }}

    .fuzzy-filter-bar {{
      background-color: var(--soft);
      padding: 8px 10px;
      border-bottom: 1px solid var(--line);
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      position: sticky;
      top: 0;
      z-index: 2;
    }}

    .filter-pill {{
      font-size: 10px;
      font-weight: 700;
      padding: 3px 9px;
      border-radius: var(--radius-pill);
      border: 1px solid var(--line);
      background-color: var(--w-white);
      color: var(--mut);
      cursor: pointer;
    }}

    .filter-pill.active {{
      background-color: var(--vd-primary);
      color: var(--w-white);
      border-color: var(--vd-primary);
    }}

    .fuzzy-item {{
      padding: 10px 14px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      align-items: center;
      cursor: pointer;
      font-size: 13px;
    }}

    .fuzzy-item:hover,
    .fuzzy-item.highlighted {{
      background-color: var(--soft);
      border-left: 4px solid var(--vg-secondary);
    }}

    .fuzzy-item-main {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .fuzzy-badge {{
      font-size: 10px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: var(--radius-pill);
      background-color: var(--vd-primary);
      color: var(--w-white);
    }}

    .fuzzy-score {{
      font-size: 10px;
      color: var(--mut);
    }}

    .fuzzy-add-new {{
      padding: 12px 14px;
      background-color: #EEF6EC;
      border-top: 2px solid var(--vg-secondary);
      color: var(--vd-primary);
      font-weight: 700;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    .fuzzy-add-new:hover {{
      background-color: var(--vd-primary);
      color: var(--w-white);
    }}

    /* === PÍLULAS DE ESCOLHA (CIF / FOB, SIM / NÃO) === */
    .choice-group {{
      display: flex;
      gap: 10px;
    }}

    .choice-btn {{
      flex: 1;
      padding: 11px 16px;
      font-family: var(--font-main);
      font-size: 13px;
      font-weight: 700;
      border: 1.5px solid var(--line);
      background-color: var(--soft);
      color: var(--ink);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.15s;
    }}

    .choice-btn.active-ok {{
      background-color: var(--vg-secondary);
      border-color: var(--vd-primary);
      color: var(--w-white);
    }}

    .choice-btn.active-crit {{
      background-color: var(--crit);
      border-color: #9E1C13;
      color: var(--w-white);
    }}

    .choice-btn.active-neutral {{
      background-color: var(--vd-primary);
      border-color: var(--vd-primary);
      color: var(--w-white);
    }}

    /* === ITENS DE INSPEÇÃO CRÍTICA (ITEM 01 A ITEM 05) === */
    .inspection-list {{
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}

    .inspection-card {{
      background-color: var(--soft);
      border: 1px solid var(--line);
      border-left: 6px solid var(--vg-secondary);
      padding: 18px;
      transition: all 0.2s;
    }}

    .inspection-card.non-compliant {{
      background-color: #FFF5F5;
      border-color: #F5C2C0;
      border-left: 6px solid var(--crit);
    }}

    .inspection-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
    }}

    @media (max-width: 768px) {{
      .inspection-top {{
        flex-direction: column;
      }}
    }}

    .inspection-question {{
      flex: 1;
    }}

    .item-tag-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
    }}

    .item-pill {{
      background-color: var(--vy-accent);
      color: var(--ink);
      font-weight: 800;
      font-size: 11px;
      padding: 2px 10px;
      border-radius: var(--radius-pill);
    }}

    .item-crit-badge {{
      font-size: 10px;
      font-weight: 700;
      color: var(--vd-primary);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    .inspection-question h3 {{
      font-size: 14px;
      font-weight: 700;
      color: var(--ink);
      margin-bottom: 4px;
    }}

    .inspection-question p {{
      font-size: 12px;
      color: var(--mut);
    }}

    .inspection-toggle {{
      display: flex;
      gap: 8px;
      min-width: 240px;
      flex-shrink: 0;
    }}

    .nc-drawer {{
      margin-top: 16px;
      padding-top: 14px;
      border-top: 1px dashed var(--line);
      display: none;
    }}

    .nc-drawer.visible {{
      display: block;
    }}

    .nc-alert-banner {{
      background-color: var(--crit);
      color: var(--w-white);
      padding: 8px 12px;
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .multi-chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
    }}

    .chip-option {{
      padding: 7px 14px;
      border-radius: var(--radius-pill);
      border: 1.5px solid var(--line);
      background-color: var(--w-white);
      color: var(--ink);
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      user-select: none;
      transition: all 0.15s;
    }}

    .chip-option.selected {{
      background-color: var(--crit);
      border-color: var(--crit);
      color: var(--w-white);
    }}

    /* === EVIDÊNCIA FOTOGRÁFICA OPCIONAL (CANVAS + DATAVERSE IMAGE COLUMN) === */
    .badge-opt {{
      font-size: 10px;
      font-weight: 700;
      color: var(--vd-primary);
      background-color: #E7F4E4;
      border: 1px solid #B7DFB0;
      padding: 1px 8px;
      border-radius: var(--radius-pill);
    }}

    .photo-upload-box {{
      margin-top: 12px;
      padding: 12px 14px;
      background-color: var(--w-white);
      border: 1.5px dashed var(--vg-secondary);
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    .photo-upload-actions {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 10px;
    }}

    .btn-photo-capture {{
      background-color: var(--vd-primary);
      color: var(--w-white);
      border: none;
      padding: 8px 14px;
      font-family: var(--font-main);
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      letter-spacing: 0.3px;
    }}

    .btn-photo-capture:hover {{
      background-color: var(--vg-secondary);
    }}

    .photo-preview-card {{
      display: none;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 8px 12px;
      background-color: var(--soft);
      border: 1px solid var(--line);
      border-left: 4px solid var(--vg-secondary);
    }}

    .photo-preview-card.visible {{
      display: flex;
    }}

    .photo-preview-left {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .photo-preview-thumb {{
      width: 64px;
      height: 64px;
      object-fit: cover;
      border: 1px solid var(--line);
      background-color: var(--w-white);
    }}

    .photo-meta-text {{
      display: flex;
      flex-direction: column;
      gap: 2px;
      font-size: 12px;
    }}

    .btn-photo-remove {{
      background-color: #FEECEB;
      color: var(--crit);
      border: 1px solid #F8C9C5;
      padding: 5px 10px;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
    }}

    /* === BOTÃO DE AÇÃO DIGITAL (#0000FF) === */
    .submit-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      background-color: var(--w-white);
      border: 1px solid var(--line);
      border-left: 6px solid var(--vb-digital);
      padding: 18px 22px;
      box-shadow: var(--shadow-card);
      flex-wrap: wrap;
    }}

    .btn-digital {{
      background-color: var(--vb-digital);
      color: var(--w-white);
      font-family: var(--font-main);
      font-size: 15px;
      font-weight: 700;
      padding: 14px 32px;
      border: none;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 10px;
      letter-spacing: 0.4px;
      text-transform: uppercase;
      box-shadow: 0 4px 10px rgba(0, 0, 255, 0.25);
      transition: transform 0.1s, opacity 0.15s;
    }}

    .btn-digital:hover {{
      opacity: 0.92;
    }}

    .btn-digital:active {{
      transform: translateY(1px);
    }}

    .btn-digital:disabled {{
      opacity: 0.55;
      cursor: not-allowed;
    }}

    /* === MODAL / FEEDBACK DE SUCESSO === */
    .toast-banner {{
      display: none;
      padding: 16px 20px;
      background-color: var(--vd-primary);
      color: var(--w-white);
      border-left: 6px solid var(--vy-accent);
      box-shadow: var(--shadow-card);
      margin-bottom: 16px;
    }}

    .toast-banner.visible {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }}

    .saved-user-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background-color: #E7F4E4;
      color: var(--vd-primary);
      border: 1px solid #B7DFB0;
      padding: 3px 10px;
      border-radius: var(--radius-pill);
      font-size: 11px;
      font-weight: 700;
    }}

    /* === OVERLAY DE BLOQUEIO / VERIFICAÇÃO SSO VIBRA === */
    .auth-gate-overlay {{
      position: fixed;
      inset: 0;
      z-index: 9999;
      background: linear-gradient(145deg, var(--vd-primary) 0%, var(--dark2) 100%);
      color: var(--w-white);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px;
      text-align: center;
    }}

    .auth-gate-card {{
      max-width: 480px;
      width: 100%;
      background-color: rgba(11, 50, 24, 0.92);
      border: 1px solid rgba(254, 220, 0, 0.35);
      border-top: 6px solid var(--vy-accent);
      padding: 32px 28px;
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45);
    }}

    .auth-gate-card h2 {{
      font-size: 19px;
      font-weight: 700;
      color: var(--vy-accent);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 10px;
    }}

    .auth-gate-card p {{
      font-size: 13px;
      color: #DCE7D5;
      line-height: 1.5;
      margin-bottom: 20px;
    }}
  </style>
</head>
<body>

  <!-- BLOQUEIO DE SEGURANÇA: EXIGE SESSÃO CORPORATIVA VIBRA (ENTRA ID / DATAVERSE SSO) -->
  <div class="auth-gate-overlay" id="authGateOverlay">
    <div class="auth-gate-card">
      <h2>🔒 Acesso Corporativo Vibra Energia</h2>
      <p id="authGateMessage">Verificando sua sessão autenticada no ambiente corporativo Vibra Energia (Microsoft Entra ID SSO)...</p>
      <button type="button" class="btn-digital" id="btnAuthRedirect" style="display:none; width:100%; justify-content:center;" onclick="window.location.href='https://orgd15f46d4.crm2.dynamics.com/WebResources/opsul_blitz_sms_app.html'">
        Entrar com Conta Corporativa Vibra
      </button>
    </div>
  </div>

  <!-- CABEÇALHO DOMINANTE (#004415 VD Verde Escuro + #0B3218 DARK2 + #FEDC00 VY Amarelo) -->
  <header class="hero-header">
    <div class="hero-top-bar">
      <div>VIBRA ENERGIA • DIRETORIA DE OPERAÇÕES • SOLUÇÃO RELACIONAL <strong>OPER_OPSUL</strong></div>
      <div><span class="badge-pill" id="authBadgePill">🔒 AUTENTICANDO SESSÃO VIBRA...</span></div>
    </div>
    <div class="hero-main">
      <div class="hero-title-group">
        <div class="hero-icon-box">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#FEDC00" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="M9 12l2 2 4-4"/>
          </svg>
        </div>
        <div>
          <h1>BLITZ DE SMS — OPER_OPSUL</h1>
          <p>Inspeção de Segurança, Meio Ambiente e Saúde de Caminhões-Tanque (CT) nas Bases Operacionais</p>
        </div>
      </div>
      <div class="hero-stats">
        <div class="stat-box">
          <span class="stat-num" id="statTotalBases">{len(bases)}</span>
          <span class="stat-lbl">Bases Ativas</span>
        </div>
        <div class="stat-box">
          <span class="stat-num" id="statTotalBlitz">{len(sp_items)}</span>
          <span class="stat-lbl">Blitz no Banco</span>
        </div>
      </div>
    </div>
  </header>

  <!-- FAIXA DE ETAPAS E MEMÓRIA DO RESPONSÁVEL -->
  <div class="progress-strip">
    <div class="progress-inner">
      <div class="step-pills">
        <span class="step-pill active"><span class="num">1</span> Identificação & Base (Fuzzy)</span>
        <span class="step-pill active"><span class="num">2</span> Checklist Crítico (Itens 01 a 05)</span>
        <span class="step-pill active"><span class="num">3</span> Observações Gerais & Registro</span>
      </div>
      <div id="memoryIndicator" style="display:none;">
        <span class="saved-user-pill" id="savedUserBadge"></span>
      </div>
    </div>
  </div>

  <main class="container">

    <!-- BANNER DE CONFIRMAÇÃO -->
    <div class="toast-banner" id="successBanner">
      <div>
        <strong style="color: var(--vy-accent); font-size: 15px;">✓ BLITZ DE SMS REGISTRADA COM SUCESSO NO BANCO RELACIONAL OPER_OPSUL!</strong>
        <p id="successDetails" style="font-size: 12px; margin-top: 4px; color: #E2ECE4;"></p>
      </div>
      <button type="button" class="combo-btn" onclick="resetFormKeepUser()" style="padding: 8px 14px;">+ Nova Blitz</button>
    </div>

    <form id="blitzForm" novalidate>

      <!-- SEÇÃO 01: IDENTIFICAÇÃO DA BLITZ, RESPONSÁVEL E BASE OPERACIONAL -->
      <section class="section-card">
        <div class="section-header">
          <div class="section-header-left">
            <span class="section-num">SEÇÃO 01</span>
            <h2 class="section-title">Identificação da Inspeção, Responsável e Base Operacional</h2>
          </div>
          <span class="section-tag">Campos Críticos Obrigatórios</span>
        </div>

        <div class="section-body">
          <div class="form-grid">

            <!-- DATA DA BLITZ -->
            <div class="field-group col-4">
              <div class="field-label-row">
                <span class="field-label">Data da Blitz</span>
                <span class="badge-lock">🔒 AUTOMÁTICA (HOJE)</span>
              </div>
              <input type="date" id="inpData" readonly tabindex="-1" style="pointer-events: none;" required />
              <span class="field-hint">Preenchida automaticamente com a data de hoje (bloqueada para alteração).</span>
              <span class="error-msg" id="errData">Informe a data da Blitz.</span>
            </div>

            <!-- BASE OPERACIONAL COM BUSCA FUZZY -->
            <div class="field-group col-8">
              <div class="field-label-row">
                <label class="field-label" for="inpBaseSearch">Base Operacional (Busca Inteligente Fuzzy)</label>
                <span class="badge-req">OBRIGATÓRIO</span>
              </div>
              <div class="combobox-wrapper" id="baseComboWrapper">
                <div class="combobox-input-box">
                  <input
                    type="text"
                    id="inpBaseSearch"
                    placeholder="Digite a sigla ou parte do nome (ex.: BACUB, BAVAP, AICAI, RACWB, GEI)..."
                    autocomplete="off"
                  />
                  <div class="combobox-actions">
                    <button type="button" class="combo-btn" id="btnClearBase" title="Limpar Base" style="display:none;">✕</button>
                    <button type="button" class="combo-btn" id="btnToggleBaseDropdown">▼ Lista ({len(bases)})</button>
                  </div>
                </div>
                <input type="hidden" id="inpBaseValue" required />

                <div class="fuzzy-dropdown" id="baseDropdown">
                  <div class="fuzzy-filter-bar" id="baseCategoryFilters">
                    <button type="button" class="filter-pill active" data-cat="ALL">Todas ({len(bases)})</button>
                    <button type="button" class="filter-pill" data-cat="BA">BA • Bases</button>
                    <button type="button" class="filter-pill" data-cat="RA">RA • Revendas/Aviação</button>
                    <button type="button" class="filter-pill" data-cat="AR">AR • Armazéns</button>
                    <button type="button" class="filter-pill" data-cat="AI">AI • Aeroportos</button>
                    <button type="button" class="filter-pill" data-cat="OUT">DE / BE / SEDE / GEI</button>
                  </div>
                  <div id="baseResultsList"></div>
                </div>
              </div>
              <span class="field-hint">Busca tolerante a erros de digitação e acentos (ex.: <strong>bacai</strong> encontra <strong>BAÇAI</strong>; <strong>cuba</strong> encontra <strong>BACUB</strong>).</span>
              <span class="error-msg" id="errBase">Selecione uma Base Operacional válida da lista.</span>
            </div>

            <!-- RESPONSÁVEL PELA BLITZ (VINCULADO AO LOGIN CORPORATIVO VIBRA SSO) -->
            <div class="field-group col-8" id="respComboWrapper">
              <div class="field-label-row">
                <span class="field-label">Nome do Responsável pela Blitz</span>
                <span class="badge-lock">🔒 AUTOMÁTICO (LOGIN CORPORATIVO)</span>
              </div>
              <input
                type="text"
                id="inpRespSearch"
                readonly
                tabindex="-1"
                style="pointer-events: none; font-weight: 700;"
                placeholder="Identificando usuário do login corporativo Vibra..."
              />
              <input type="hidden" id="inpRespValue" required />
              <span class="field-hint">Vinculado automaticamente ao seu login corporativo Vibra Energia (sem opção de escolher outro nome).</span>
              <span class="error-msg" id="errResp">Autentique-se com seu login corporativo Vibra para preencher o Responsável pela Blitz.</span>
            </div>

            <!-- MODALIDADE CIF OU FOB -->
            <div class="field-group col-4">
              <div class="field-label-row">
                <label class="field-label">Modalidade (CIF ou FOB)</label>
                <span class="badge-req">OBRIGATÓRIO</span>
              </div>
              <div class="choice-group" id="cifFobGroup">
                <button type="button" class="choice-btn" data-val="CIF" onclick="selectCifFob('CIF')">CIF</button>
                <button type="button" class="choice-btn" data-val="FOB" onclick="selectCifFob('FOB')">FOB</button>
              </div>
              <input type="hidden" id="inpCifFob" required />
              <span class="field-hint">Tipo de frete da operação inspecionada.</span>
              <span class="error-msg" id="errCifFob">Selecione CIF ou FOB.</span>
            </div>

            <!-- TRANSPORTADORA -->
            <div class="field-group col-6">
              <div class="field-label-row">
                <label class="field-label" for="inpTransportadora">Transportadora</label>
                <span class="badge-req">OBRIGATÓRIO</span>
              </div>
              <input
                type="text"
                id="inpTransportadora"
                list="transportadorasDatalist"
                placeholder="Digite ou selecione a Transportadora..."
                required
              />
              <datalist id="transportadorasDatalist"></datalist>
              <span class="error-msg" id="errTransportadora">Informe o nome da Transportadora.</span>
            </div>

            <!-- PLACA DO CT -->
            <div class="field-group col-6">
              <div class="field-label-row">
                <label class="field-label" for="inpPlaca">Placa do CT (Caminhão-Tanque)</label>
                <span class="badge-req">OBRIGATÓRIO</span>
              </div>
              <input
                type="text"
                id="inpPlaca"
                placeholder="Ex.: ABC1D23 ou ABC-1234"
                maxlength="10"
                style="text-transform: uppercase; font-weight: 700;"
                required
              />
              <span class="error-msg" id="errPlaca">Informe a Placa do CT inspecionado.</span>
            </div>

          </div>
        </div>
      </section>

      <!-- SEÇÃO 02: CHECKLIST DE ITENS CRÍTICOS DE SMS (ITENS 01 A 05) -->
      <section class="section-card">
        <div class="section-header">
          <div class="section-header-left">
            <span class="section-num">SEÇÃO 02</span>
            <h2 class="section-title">Verificação dos 5 Itens Críticos Operacionais de SMS</h2>
          </div>
          <span class="section-tag">100% Obrigatórios</span>
        </div>

        <div class="section-body">
          <div class="inspection-list">

            <!-- ITEM 01 -->
            <div class="inspection-card" id="cardItem1">
              <div class="inspection-top">
                <div class="inspection-question">
                  <div class="item-tag-row">
                    <span class="item-pill">ITEM 01</span>
                    <span class="item-crit-badge">EPIs & Proteção Individual • Obrigatório</span>
                  </div>
                  <h3>Os EPI's são apropriados para a atividade que será realizada? Apresentam boas condições de uso e aparentam higienizados (limpos)?</h3>
                  <p>Uniforme 100% em algodão natural em duas peças, Calçado de segurança, Luvas de PVC ou Nitrílica, Capacete com Jugular, Óculos de segurança modelo ampla visão antirrespingo e Cinto de segurança tipo paraquedista com extensor (máximo 60 cm).</p>
                </div>
                <div class="inspection-toggle">
                  <button type="button" class="choice-btn active-ok" id="btnItem1Sim" onclick="setItemStatus(1, true)">✓ SIM (Conforme)</button>
                  <button type="button" class="choice-btn" id="btnItem1Nao" onclick="setItemStatus(1, false)">✕ NÃO</button>
                </div>
              </div>

              <div class="nc-drawer" id="drawerItem1">
                <div class="nc-alert-banner">
                  ⚠ NÃO CONFORMIDADE CRÍTICA NO ITEM 01: Selecione abaixo qual(is) EPI(s) não está(ão) apropriado(s) e descreva a observação.
                </div>
                <div class="field-group" style="margin-bottom: 12px;">
                  <div class="field-label-row">
                    <span class="field-label">Qual EPI não está apropriado? (Selecione um ou mais)</span>
                    <span class="badge-req">OBRIGATÓRIO EM CASO DE NÃO</span>
                  </div>
                  <div class="multi-chips" id="chipsEpi">
                    <span class="chip-option" data-val="Uniforme 100% Algodão" onclick="toggleChip(this)">Uniforme 100% Algodão</span>
                    <span class="chip-option" data-val="Calçado de Segurança" onclick="toggleChip(this)">Calçado de Segurança</span>
                    <span class="chip-option" data-val="Luvas de PVC ou Nitrilica" onclick="toggleChip(this)">Luvas de PVC ou Nitrílica</span>
                    <span class="chip-option" data-val="Capacete com Jugular" onclick="toggleChip(this)">Capacete com Jugular</span>
                    <span class="chip-option" data-val="Óculos Ampla Visão" onclick="toggleChip(this)">Óculos Ampla Visão</span>
                    <span class="chip-option" data-val="Cinto de Segurança tipo paraquedista" onclick="toggleChip(this)">Cinto de Segurança tipo paraquedista</span>
                  </div>
                  <span class="error-msg" id="errEpiChips">Selecione pelo menos um EPI não conforme.</span>
                </div>
                <div class="field-group">
                  <div class="field-label-row">
                    <label class="field-label" for="inpObs1">Observação do Item 01 (EPIs)</label>
                    <span class="badge-req" id="reqBadgeObs1" style="display:none;">OBRIGATÓRIO</span>
                  </div>
                  <input type="text" id="inpObs1" placeholder="Descreva o desvio identificado nos EPIs..." />
                  <span class="error-msg" id="errObs1">Descreva a observação referente à não conformidade do Item 01.</span>
                </div>
                <div class="photo-upload-box">
                  <div class="photo-upload-actions">
                    <div>
                      <span class="field-label">Evidência Fotográfica — Item 01 (EPIs)</span>
                      <span class="badge-opt" style="margin-left:6px;">OPCIONAL</span>
                      <div class="field-hint">Armazenamento nativo em coluna de imagem do Dataverse (<code>opsul_foto_item1</code>).</div>
                    </div>
                    <div>
                      <input type="file" id="inpFoto1" accept="image/*" capture="environment" style="display:none;" onchange="handlePhotoInput(1, this)" />
                      <button type="button" class="btn-photo-capture" onclick="document.getElementById('inpFoto1').click()">📷 Tirar / Anexar Foto</button>
                    </div>
                  </div>
                  <div class="photo-preview-card" id="photoPreviewCard1">
                    <div class="photo-preview-left">
                      <img id="photoThumb1" class="photo-preview-thumb" alt="Preview Item 01" />
                      <div class="photo-meta-text">
                        <strong id="photoName1" style="color:var(--vd-primary);"></strong>
                        <span id="photoSize1" style="color:var(--mut); font-size:11px;"></span>
                      </div>
                    </div>
                    <button type="button" class="btn-photo-remove" onclick="clearPhotoItem(1)">✕ Remover Foto</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- ITEM 02 -->
            <div class="inspection-card" id="cardItem2">
              <div class="inspection-top">
                <div class="inspection-question">
                  <div class="item-tag-row">
                    <span class="item-pill">ITEM 02</span>
                    <span class="item-crit-badge">Integridade Estrutural do Veículo • Obrigatório</span>
                  </div>
                  <h3>Veículo está íntegro em sua estrutura e sem peças quebradas?</h3>
                  <p>Condições avaliadas: fiação elétrica, pneus, vidros, lanternas e faróis.</p>
                </div>
                <div class="inspection-toggle">
                  <button type="button" class="choice-btn active-ok" id="btnItem2Sim" onclick="setItemStatus(2, true)">✓ SIM (Conforme)</button>
                  <button type="button" class="choice-btn" id="btnItem2Nao" onclick="setItemStatus(2, false)">✕ NÃO</button>
                </div>
              </div>

              <div class="nc-drawer" id="drawerItem2">
                <div class="nc-alert-banner">
                  ⚠ NÃO CONFORMIDADE CRÍTICA NO ITEM 02: Selecione qual(is) peça(s) não está(ão) conforme(s) e registre a observação.
                </div>
                <div class="field-group" style="margin-bottom: 12px;">
                  <div class="field-label-row">
                    <span class="field-label">Qual peça não está conforme? (Selecione uma ou mais)</span>
                    <span class="badge-req">OBRIGATÓRIO EM CASO DE NÃO</span>
                  </div>
                  <div class="multi-chips" id="chipsPeca">
                    <span class="chip-option" data-val="Fiação Elétrica" onclick="toggleChip(this)">Fiação Elétrica</span>
                    <span class="chip-option" data-val="Pneus" onclick="toggleChip(this)">Pneus</span>
                    <span class="chip-option" data-val="Vidros" onclick="toggleChip(this)">Vidros</span>
                    <span class="chip-option" data-val="Lanternas e Faróis" onclick="toggleChip(this)">Lanternas e Faróis</span>
                    <span class="chip-option" data-val="Outros" onclick="toggleChip(this)">Outros</span>
                  </div>
                  <span class="error-msg" id="errPecaChips">Selecione pelo menos uma peça não conforme.</span>
                </div>
                <div class="field-group">
                  <div class="field-label-row">
                    <label class="field-label" for="inpObs2">Observação do Item 02 (Estrutura / Peças)</label>
                    <span class="badge-req" id="reqBadgeObs2" style="display:none;">OBRIGATÓRIO</span>
                  </div>
                  <input type="text" id="inpObs2" placeholder="Descreva a avaria ou peça quebrada no veículo..." />
                  <span class="error-msg" id="errObs2">Descreva a observação referente à não conformidade do Item 02.</span>
                </div>
                <div class="photo-upload-box">
                  <div class="photo-upload-actions">
                    <div>
                      <span class="field-label">Evidência Fotográfica — Item 02 (Estrutura / Peças)</span>
                      <span class="badge-opt" style="margin-left:6px;">OPCIONAL</span>
                      <div class="field-hint">Armazenamento nativo em coluna de imagem do Dataverse (<code>opsul_foto_item2</code>).</div>
                    </div>
                    <div>
                      <input type="file" id="inpFoto2" accept="image/*" capture="environment" style="display:none;" onchange="handlePhotoInput(2, this)" />
                      <button type="button" class="btn-photo-capture" onclick="document.getElementById('inpFoto2').click()">📷 Tirar / Anexar Foto</button>
                    </div>
                  </div>
                  <div class="photo-preview-card" id="photoPreviewCard2">
                    <div class="photo-preview-left">
                      <img id="photoThumb2" class="photo-preview-thumb" alt="Preview Item 02" />
                      <div class="photo-meta-text">
                        <strong id="photoName2" style="color:var(--vd-primary);"></strong>
                        <span id="photoSize2" style="color:var(--mut); font-size:11px;"></span>
                      </div>
                    </div>
                    <button type="button" class="btn-photo-remove" onclick="clearPhotoItem(2)">✕ Remover Foto</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- ITEM 03 -->
            <div class="inspection-card" id="cardItem3">
              <div class="inspection-top">
                <div class="inspection-question">
                  <div class="item-tag-row">
                    <span class="item-pill">ITEM 03</span>
                    <span class="item-crit-badge">Condições do Tanque • Obrigatório</span>
                  </div>
                  <h3>O Tanque do veículo está em boas condições operacionais?</h3>
                  <p>Verificação visual de estanqueidade, ausência de vazamentos, tampas, válvulas e integridade do costado.</p>
                </div>
                <div class="inspection-toggle">
                  <button type="button" class="choice-btn active-ok" id="btnItem3Sim" onclick="setItemStatus(3, true)">✓ SIM (Conforme)</button>
                  <button type="button" class="choice-btn" id="btnItem3Nao" onclick="setItemStatus(3, false)">✕ NÃO</button>
                </div>
              </div>

              <div class="nc-drawer" id="drawerItem3">
                <div class="nc-alert-banner">
                  ⚠ NÃO CONFORMIDADE CRÍTICA NO ITEM 03: Descreva obrigatoriamente a anomalia identificada no tanque.
                </div>
                <div class="field-group">
                  <div class="field-label-row">
                    <label class="field-label" for="inpObs3">Observação do Item 03 (Tanque)</label>
                    <span class="badge-req">OBRIGATÓRIO EM CASO DE NÃO</span>
                  </div>
                  <input type="text" id="inpObs3" placeholder="Detalhe a condição insegura identificada no tanque..." />
                  <span class="error-msg" id="errObs3">Descreva a observação referente à não conformidade do Item 03.</span>
                </div>
                <div class="photo-upload-box">
                  <div class="photo-upload-actions">
                    <div>
                      <span class="field-label">Evidência Fotográfica — Item 03 (Tanque)</span>
                      <span class="badge-opt" style="margin-left:6px;">OPCIONAL</span>
                      <div class="field-hint">Armazenamento nativo em coluna de imagem do Dataverse (<code>opsul_foto_item3</code>).</div>
                    </div>
                    <div>
                      <input type="file" id="inpFoto3" accept="image/*" capture="environment" style="display:none;" onchange="handlePhotoInput(3, this)" />
                      <button type="button" class="btn-photo-capture" onclick="document.getElementById('inpFoto3').click()">📷 Tirar / Anexar Foto</button>
                    </div>
                  </div>
                  <div class="photo-preview-card" id="photoPreviewCard3">
                    <div class="photo-preview-left">
                      <img id="photoThumb3" class="photo-preview-thumb" alt="Preview Item 03" />
                      <div class="photo-meta-text">
                        <strong id="photoName3" style="color:var(--vd-primary);"></strong>
                        <span id="photoSize3" style="color:var(--mut); font-size:11px;"></span>
                      </div>
                    </div>
                    <button type="button" class="btn-photo-remove" onclick="clearPhotoItem(3)">✕ Remover Foto</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- ITEM 04 -->
            <div class="inspection-card" id="cardItem4">
              <div class="inspection-top">
                <div class="inspection-question">
                  <div class="item-tag-row">
                    <span class="item-pill">ITEM 04</span>
                    <span class="item-crit-badge">Aterramento, Overfill e Acesso ao CT • Obrigatório</span>
                  </div>
                  <h3>Condições dos sistemas de aterramento / sensor overfill estão em condições operacionais?</h3>
                  <p>Verificar todo tanque (ênfase nas soldas), possui apoio para subida e descida e se os degraus de acesso ao CT são antiderrapantes.</p>
                </div>
                <div class="inspection-toggle">
                  <button type="button" class="choice-btn active-ok" id="btnItem4Sim" onclick="setItemStatus(4, true)">✓ SIM (Conforme)</button>
                  <button type="button" class="choice-btn" id="btnItem4Nao" onclick="setItemStatus(4, false)">✕ NÃO</button>
                </div>
              </div>

              <div class="nc-drawer" id="drawerItem4">
                <div class="nc-alert-banner">
                  ⚠ NÃO CONFORMIDADE CRÍTICA NO ITEM 04: Descreva obrigatoriamente a falha no aterramento, sensor overfill ou acesso.
                </div>
                <div class="field-group">
                  <div class="field-label-row">
                    <label class="field-label" for="inpObs4">Observação do Item 04 (Aterramento / Overfill / Escada)</label>
                    <span class="badge-req">OBRIGATÓRIO EM CASO DE NÃO</span>
                  </div>
                  <input type="text" id="inpObs4" placeholder="Detalhe a falha de aterramento, sensor overfill ou degraus..." />
                  <span class="error-msg" id="errObs4">Descreva a observação referente à não conformidade do Item 04.</span>
                </div>
                <div class="photo-upload-box">
                  <div class="photo-upload-actions">
                    <div>
                      <span class="field-label">Evidência Fotográfica — Item 04 (Aterramento / Overfill)</span>
                      <span class="badge-opt" style="margin-left:6px;">OPCIONAL</span>
                      <div class="field-hint">Armazenamento nativo em coluna de imagem do Dataverse (<code>opsul_foto_item4</code>).</div>
                    </div>
                    <div>
                      <input type="file" id="inpFoto4" accept="image/*" capture="environment" style="display:none;" onchange="handlePhotoInput(4, this)" />
                      <button type="button" class="btn-photo-capture" onclick="document.getElementById('inpFoto4').click()">📷 Tirar / Anexar Foto</button>
                    </div>
                  </div>
                  <div class="photo-preview-card" id="photoPreviewCard4">
                    <div class="photo-preview-left">
                      <img id="photoThumb4" class="photo-preview-thumb" alt="Preview Item 04" />
                      <div class="photo-meta-text">
                        <strong id="photoName4" style="color:var(--vd-primary);"></strong>
                        <span id="photoSize4" style="color:var(--mut); font-size:11px;"></span>
                      </div>
                    </div>
                    <button type="button" class="btn-photo-remove" onclick="clearPhotoItem(4)">✕ Remover Foto</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- ITEM 05 -->
            <div class="inspection-card" id="cardItem5">
              <div class="inspection-top">
                <div class="inspection-question">
                  <div class="item-tag-row">
                    <span class="item-pill">ITEM 05</span>
                    <span class="item-crit-badge">Chave Geral do CT • Obrigatório</span>
                  </div>
                  <h3>Chave geral do CT está desempenhando sua função, e possui identificação da posição liga e desliga?</h3>
                  <p>Solicitar que o motorista desligue a chave geral para teste prático de funcionamento.</p>
                </div>
                <div class="inspection-toggle">
                  <button type="button" class="choice-btn active-ok" id="btnItem5Sim" onclick="setItemStatus(5, true)">✓ SIM (Conforme)</button>
                  <button type="button" class="choice-btn" id="btnItem5Nao" onclick="setItemStatus(5, false)">✕ NÃO</button>
                </div>
              </div>

              <div class="nc-drawer" id="drawerItem5">
                <div class="nc-alert-banner">
                  ⚠ NÃO CONFORMIDADE CRÍTICA NO ITEM 05: Descreva obrigatoriamente o problema na chave geral do CT.
                </div>
                <div class="field-group">
                  <div class="field-label-row">
                    <label class="field-label" for="inpObs5">Observação do Item 05 (Chave Geral)</label>
                    <span class="badge-req">OBRIGATÓRIO EM CASO DE NÃO</span>
                  </div>
                  <input type="text" id="inpObs5" placeholder="Detalhe o problema constatado no teste da chave geral..." />
                  <span class="error-msg" id="errObs5">Descreva a observação referente à não conformidade do Item 05.</span>
                </div>
                <div class="photo-upload-box">
                  <div class="photo-upload-actions">
                    <div>
                      <span class="field-label">Evidência Fotográfica — Item 05 (Chave Geral)</span>
                      <span class="badge-opt" style="margin-left:6px;">OPCIONAL</span>
                      <div class="field-hint">Armazenamento nativo em coluna de imagem do Dataverse (<code>opsul_foto_item5</code>).</div>
                    </div>
                    <div>
                      <input type="file" id="inpFoto5" accept="image/*" capture="environment" style="display:none;" onchange="handlePhotoInput(5, this)" />
                      <button type="button" class="btn-photo-capture" onclick="document.getElementById('inpFoto5').click()">📷 Tirar / Anexar Foto</button>
                    </div>
                  </div>
                  <div class="photo-preview-card" id="photoPreviewCard5">
                    <div class="photo-preview-left">
                      <img id="photoThumb5" class="photo-preview-thumb" alt="Preview Item 05" />
                      <div class="photo-meta-text">
                        <strong id="photoName5" style="color:var(--vd-primary);"></strong>
                        <span id="photoSize5" style="color:var(--mut); font-size:11px;"></span>
                      </div>
                    </div>
                    <button type="button" class="btn-photo-remove" onclick="clearPhotoItem(5)">✕ Remover Foto</button>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      <!-- SEÇÃO 03: OBSERVAÇÕES GERAIS E FECHAMENTO DA BLITZ -->
      <section class="section-card">
        <div class="section-header">
          <div class="section-header-left">
            <span class="section-num">SEÇÃO 03</span>
            <h2 class="section-title">Observações Gerais e Fechamento da Blitz</h2>
          </div>
          <span class="section-tag">Fechamento da Blitz</span>
        </div>

        <div class="section-body" style="display: flex; flex-direction: column; gap: 20px;">

          <div class="field-group">
            <div class="field-label-row">
              <label class="field-label" for="inpObsGeral">Observação Geral da Blitz (Opcional)</label>
            </div>
            <textarea id="inpObsGeral" rows="3" placeholder="Observações complementares sobre a inspeção, ações corretivas imediatas ou orientações ao motorista..."></textarea>
          </div>

        </div>
      </section>

      <!-- RODAPÉ DE SUBMISSÃO DIGITAL (#0000FF) -->
      <div class="submit-footer">
        <div>
          <strong style="font-size: 14px; color: var(--ink);">Destino: Solução Relacional <code>OPER_OPSUL</code> (Tabela <code>opsul_blitzsms</code>)</strong>
          <p style="font-size: 12px; color: var(--mut);">Gravação direta sem necessidade de login • Sincronização automática do catálogo de Responsáveis.</p>
        </div>
        <button type="submit" class="btn-digital" id="btnSubmit">
          <span>Registrar Blitz de SMS</span>
          <span>→</span>
        </button>
      </div>

    </form>
  </main>

  <script>
    // === DADOS INICIAIS EMBUTIDOS (196 BASES + RESPONSÁVEIS HISTÓRICOS + TRANSPORTADORAS) ===
    const INITIAL_BASES = {bases_json};
    const INITIAL_RESPONSAVEIS = {resp_json};
    const INITIAL_TRANSPORTADORAS = {transp_json};

    // URL da API Power Automate (injetada no deploy)
    const FLOW_API_URL = "__FLOW_API_URL__";

    // Estado do Formulário
    let basesList = [...INITIAL_BASES];
    let responsaveisList = [...INITIAL_RESPONSAVEIS];
    let activeBaseCat = "ALL";
    let itemState = {{ 1: true, 2: true, 3: true, 4: true, 5: true }};
    let itemPhotos = {{ 1: null, 2: null, 3: null, 4: null, 5: null }};

    // === COMPRESSÃO CLIENT-SIDE VIA CANVAS & PREPARAÇÃO BASE64 PARA DATAVERSE ===
    window.handlePhotoInput = function(itemNum, inputEl) {{
      const file = inputEl && inputEl.files && inputEl.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function(evt) {{
        const img = new Image();
        img.onload = function() {{
          const maxDim = 1280;
          let w = img.width;
          let h = img.height;
          if (w > maxDim || h > maxDim) {{
            if (w >= h) {{
              h = Math.round((h * maxDim) / w);
              w = maxDim;
            }} else {{
              w = Math.round((w * maxDim) / h);
              h = maxDim;
            }}
          }}
          const canvas = document.createElement("canvas");
          canvas.width = w;
          canvas.height = h;
          const ctx = canvas.getContext("2d");
          ctx.drawImage(img, 0, 0, w, h);

          // Exporta JPEG otimizado (78%) e extrai Base64 puro (sem prefixo data:image/jpeg;base64,)
          const dataUrl = canvas.toDataURL("image/jpeg", 0.78);
          const base64Pure = dataUrl.split(",")[1] || "";
          const sizeKb = Math.max(1, Math.round((base64Pure.length * 3) / 4 / 1024));
          const safeName = `blitz_item0${{itemNum}}_${{Date.now()}}.jpg`;

          itemPhotos[itemNum] = {{
            base64: base64Pure,
            nome: safeName,
            sizeKb: sizeKb,
            width: w,
            height: h
          }};

          document.getElementById(`photoThumb${{itemNum}}`).src = dataUrl;
          document.getElementById(`photoName${{itemNum}}`).textContent = `✓ Evidência pronta (${{safeName}})`;
          document.getElementById(`photoSize${{itemNum}}`).textContent = `${{w}}x${{h}}px • ${{sizeKb}} KB (JPEG comprimido para Dataverse Image)`;
          document.getElementById(`photoPreviewCard${{itemNum}}`).classList.add("visible");
        }};
        img.src = evt.target.result;
      }};
      reader.readAsDataURL(file);
    }};

    window.clearPhotoItem = function(itemNum) {{
      itemPhotos[itemNum] = null;
      const inp = document.getElementById(`inpFoto${{itemNum}}`);
      if (inp) inp.value = "";
      const card = document.getElementById(`photoPreviewCard${{itemNum}}`);
      if (card) card.classList.remove("visible");
      const thumb = document.getElementById(`photoThumb${{itemNum}}`);
      if (thumb) thumb.removeAttribute("src");
    }};

    // === UTILITÁRIO DE NORMALIZAÇÃO E BUSCA FUZZY ===
    function stripAccents(str) {{
      return (str || "").normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").toUpperCase().trim();
    }}

    function classifyBaseCat(sigla) {{
      const s = (sigla || "").toUpperCase().trim();
      if (s.startsWith("BA")) return "BA";
      if (s.startsWith("RA")) return "RA";
      if (s.startsWith("AR")) return "AR";
      if (s.startsWith("AI")) return "AI";
      return "OUT";
    }}

    function classifyBaseLabel(sigla) {{
      const c = classifyBaseCat(sigla);
      if (c === "BA") return "BA • Base";
      if (c === "RA") return "RA • Revenda/Abast.";
      if (c === "AR") return "AR • Armazém";
      if (c === "AI") return "AI • Aeroporto";
      return "Unidade Especial";
    }}

    // Distância de Levenshtein para tolerância a erros de digitação (Fuzzy Search real)
    function levenshtein(a, b) {{
      const m = a.length, n = b.length;
      if (m === 0) return n;
      if (n === 0) return m;
      const dp = Array.from({{ length: m + 1 }}, () => new Array(n + 1).fill(0));
      for (let i = 0; i <= m; i++) dp[i][0] = i;
      for (let j = 0; j <= n; j++) dp[0][j] = j;
      for (let i = 1; i <= m; i++) {{
        for (let j = 1; j <= n; j++) {{
          const cost = a[i - 1] === b[j - 1] ? 0 : 1;
          dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost);
        }}
      }}
      return dp[m][n];
    }}

    function fuzzyScore(query, target) {{
      const q = stripAccents(query);
      const t = stripAccents(target);
      if (!q) return 100;
      if (t === q) return 1000;
      if (t.startsWith(q)) return 850 - (t.length - q.length);
      if (t.includes(q)) return 700 - t.indexOf(q) * 5;

      // Subsequência (ex.: "bvp" -> "BAVAP", "rcw" -> "RACWB")
      let qi = 0;
      for (let ti = 0; ti < t.length && qi < q.length; ti++) {{
        if (t[ti] === q[qi]) qi++;
      }}
      if (qi === q.length) return 520 - (t.length - q.length) * 3;

      // Tolerância a erro de digitação (Levenshtein nos primeiros caracteres ou palavra inteira)
      const sliceT = t.slice(0, Math.max(q.length, Math.min(t.length, q.length + 2)));
      const dist = Math.min(levenshtein(q, t), levenshtein(q, sliceT));
      if (q.length >= 3 && dist <= 2) {{
        return 400 - dist * 120;
      }}
      return 0;
    }}

    // === RENDERIZAÇÃO DO COMBOBOX DE BASE (FUZZY) ===
    const inpBaseSearch = document.getElementById("inpBaseSearch");
    const inpBaseValue = document.getElementById("inpBaseValue");
    const baseDropdown = document.getElementById("baseDropdown");
    const baseResultsList = document.getElementById("baseResultsList");
    const btnClearBase = document.getElementById("btnClearBase");

    function renderBaseDropdown() {{
      const query = inpBaseSearch.value;
      const scored = [];
      for (const b of basesList) {{
        if (activeBaseCat !== "ALL" && classifyBaseCat(b) !== activeBaseCat) continue;
        const sc = fuzzyScore(query, b);
        if (sc > 0) scored.push({{ sigla: b, score: sc }});
      }}
      scored.sort((a, b) => b.score - a.score || a.sigla.localeCompare(b.sigla));

      if (scored.length === 0) {{
        baseResultsList.innerHTML = `<div style="padding:14px; color:var(--mut); font-size:13px;">Nenhuma base encontrada para "<strong>${{query}}</strong>". Tente outra sigla.</div>`;
        return;
      }}

      baseResultsList.innerHTML = scored.slice(0, 60).map(item => {{
        const matchType = item.score >= 700 ? "Exato/Prefixo" : (item.score >= 500 ? "Subsequência" : "Aproximação Fuzzy");
        return `
          <div class="fuzzy-item" onclick="selectBase('${{item.sigla.replace(/'/g, "\\\\'")}}')">
            <div class="fuzzy-item-main">
              <strong style="font-size:14px; color:var(--ink);">${{item.sigla}}</strong>
              <span class="fuzzy-badge">${{classifyBaseLabel(item.sigla)}}</span>
            </div>
            <span class="fuzzy-score">${{query ? matchType : "Disponível"}}</span>
          </div>
        `;
      }}).join("");
    }}

    window.selectBase = function(sigla) {{
      inpBaseSearch.value = sigla;
      inpBaseValue.value = sigla;
      baseDropdown.classList.remove("open");
      btnClearBase.style.display = "inline-block";
      document.getElementById("baseComboWrapper").classList.remove("input-error");
      document.getElementById("errBase").classList.remove("visible");
      localStorage.setItem("opsul_saved_base", sigla);
    }};

    inpBaseSearch.addEventListener("focus", () => {{
      renderBaseDropdown();
      baseDropdown.classList.add("open");
    }});

    inpBaseSearch.addEventListener("input", () => {{
      inpBaseValue.value = "";
      btnClearBase.style.display = inpBaseSearch.value ? "inline-block" : "none";
      renderBaseDropdown();
      baseDropdown.classList.add("open");
    }});

    btnClearBase.addEventListener("click", () => {{
      inpBaseSearch.value = "";
      inpBaseValue.value = "";
      btnClearBase.style.display = "none";
      inpBaseSearch.focus();
    }});

    document.getElementById("btnToggleBaseDropdown").addEventListener("click", () => {{
      if (baseDropdown.classList.contains("open")) {{
        baseDropdown.classList.remove("open");
      }} else {{
        renderBaseDropdown();
        baseDropdown.classList.add("open");
      }}
    }});

    document.querySelectorAll("#baseCategoryFilters .filter-pill").forEach(btn => {{
      btn.addEventListener("click", (e) => {{
        e.stopPropagation();
        document.querySelectorAll("#baseCategoryFilters .filter-pill").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        activeBaseCat = btn.getAttribute("data-cat");
        renderBaseDropdown();
      }});
    }});

    // === RESPONSÁVEL PELA BLITZ (BLOQUEADO E VINCULADO AO LOGIN CORPORATIVO VIBRA) ===
    const inpRespSearch = document.getElementById("inpRespSearch");
    const inpRespValue = document.getElementById("inpRespValue");

    function lockResponsavelFromCorporateLogin(rawDispName, email) {{
      const fallbackName = rawDispName || (email ? email.split("@")[0].replace(/[._-]+/g, " ").toUpperCase() : "");
      const matched = responsaveisList.find(r => stripAccents(r.nome) === stripAccents(fallbackName));
      const canonicalName = matched ? matched.nome : fallbackName;
      const suggestedBase = matched ? matched.base : "";

      inpRespValue.value = canonicalName;
      inpRespSearch.value = email ? `${{canonicalName}} (${{email}})` : canonicalName;
      document.getElementById("respComboWrapper").classList.remove("input-error");
      document.getElementById("errResp").classList.remove("visible");

      // Limpar qualquer seleção antiga de terceiros salva no navegador
      try {{
        localStorage.removeItem("opsul_saved_responsavel");
        localStorage.removeItem("opsul_custom_responsaveis");
      }} catch (_) {{}}

      const memInd = document.getElementById("memoryIndicator");
      const memBadge = document.getElementById("savedUserBadge");
      if (canonicalName) {{
        memInd.style.display = "block";
        memBadge.textContent = `🔒 Login Corporativo: ${{canonicalName}}`;
      }}

      if (suggestedBase && !inpBaseValue.value && basesList.includes(suggestedBase)) {{
        selectBase(suggestedBase);
      }}
    }}

    // Fechar dropdown de Base ao clicar fora
    document.addEventListener("click", (e) => {{
      if (!document.getElementById("baseComboWrapper").contains(e.target)) {{
        baseDropdown.classList.remove("open");
        if (!inpBaseValue.value && inpBaseSearch.value.trim()) {{
          const exact = basesList.find(b => stripAccents(b) === stripAccents(inpBaseSearch.value));
          if (exact) selectBase(exact);
        }}
      }}
    }});

    // === CONTROLES DE CIF/FOB, ITENS 01-05 E DECISÃO DE BLOQUEIO ===
    window.selectCifFob = function(val) {{
      document.getElementById("inpCifFob").value = val;
      document.querySelectorAll("#cifFobGroup .choice-btn").forEach(btn => {{
        btn.classList.toggle("active-neutral", btn.getAttribute("data-val") === val);
      }});
      document.getElementById("errCifFob").classList.remove("visible");
    }};

    window.setItemStatus = function(num, isOk) {{
      itemState[num] = isOk;
      const card = document.getElementById(`cardItem${{num}}`);
      const btnSim = document.getElementById(`btnItem${{num}}Sim`);
      const btnNao = document.getElementById(`btnItem${{num}}Nao`);
      const drawer = document.getElementById(`drawerItem${{num}}`);

      card.classList.toggle("non-compliant", !isOk);
      btnSim.classList.toggle("active-ok", isOk);
      btnNao.classList.toggle("active-crit", !isOk);
      drawer.classList.toggle("visible", !isOk);

      if (isOk) {{
        clearPhotoItem(num);
      }}
    }};

    window.toggleChip = function(el) {{
      el.classList.toggle("selected");
    }};

    function getSelectedChips(containerId) {{
      return Array.from(document.querySelectorAll(`#${{containerId}} .chip-option.selected`)).map(el => el.getAttribute("data-val"));
    }}

    function getLocalDateString() {{
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, "0");
      const day = String(now.getDate()).padStart(2, "0");
      return `${{year}}-${{month}}-${{day}}`;
    }}

    // === VALIDAÇÃO RIGOROSA DOS CAMPOS CRÍTICOS OBRIGATÓRIOS ===
    function validateForm() {{
      let valid = true;

      let dataVal = document.getElementById("inpData").value;
      if (!dataVal) {{
        document.getElementById("inpData").value = getLocalDateString();
        dataVal = document.getElementById("inpData").value;
      }}
      document.getElementById("errData").classList.toggle("visible", !dataVal);
      if (!dataVal) valid = false;

      const baseVal = document.getElementById("inpBaseValue").value;
      document.getElementById("baseComboWrapper").classList.toggle("input-error", !baseVal);
      document.getElementById("errBase").classList.toggle("visible", !baseVal);
      if (!baseVal) valid = false;

      const finalResp = document.getElementById("inpRespValue").value;
      document.getElementById("respComboWrapper").classList.toggle("input-error", !finalResp);
      document.getElementById("errResp").classList.toggle("visible", !finalResp);
      if (!finalResp) valid = false;

      const cifFob = document.getElementById("inpCifFob").value;
      document.getElementById("errCifFob").classList.toggle("visible", !cifFob);
      if (!cifFob) valid = false;

      const transp = document.getElementById("inpTransportadora").value.trim();
      document.getElementById("inpTransportadora").classList.toggle("input-error", !transp);
      document.getElementById("errTransportadora").classList.toggle("visible", !transp);
      if (!transp) valid = false;

      const placa = document.getElementById("inpPlaca").value.trim();
      document.getElementById("inpPlaca").classList.toggle("input-error", !placa);
      document.getElementById("errPlaca").classList.toggle("visible", !placa);
      if (!placa) valid = false;

      // Validação condicional dos 5 itens críticos
      if (!itemState[1]) {{
        const epis = getSelectedChips("chipsEpi");
        const obs1 = document.getElementById("inpObs1").value.trim();
        document.getElementById("errEpiChips").classList.toggle("visible", epis.length === 0);
        document.getElementById("errObs1").classList.toggle("visible", !obs1);
        if (epis.length === 0 || !obs1) valid = false;
      }} else {{
        document.getElementById("errEpiChips").classList.remove("visible");
        document.getElementById("errObs1").classList.remove("visible");
      }}

      if (!itemState[2]) {{
        const pecas = getSelectedChips("chipsPeca");
        const obs2 = document.getElementById("inpObs2").value.trim();
        document.getElementById("errPecaChips").classList.toggle("visible", pecas.length === 0);
        document.getElementById("errObs2").classList.toggle("visible", !obs2);
        if (pecas.length === 0 || !obs2) valid = false;
      }} else {{
        document.getElementById("errPecaChips").classList.remove("visible");
        document.getElementById("errObs2").classList.remove("visible");
      }}

      for (const n of [3, 4, 5]) {{
        const obs = document.getElementById(`inpObs${{n}}`).value.trim();
        const showErr = !itemState[n] && !obs;
        document.getElementById(`errObs${{n}}`).classList.toggle("visible", showErr);
        if (showErr) valid = false;
      }}

      return valid;
    }}

    // === SUBMISSÃO SEM LOGIN PARA O BANCO RELACIONAL OPER_OPSUL ===
    document.getElementById("blitzForm").addEventListener("submit", async (e) => {{
      e.preventDefault();
      if (!validateForm()) {{
        const firstErr = document.querySelector(".error-msg.visible");
        if (firstErr) firstErr.scrollIntoView({{ behavior: "smooth", block: "center" }});
        return;
      }}

      const btn = document.getElementById("btnSubmit");
      btn.disabled = true;
      btn.innerHTML = `<span>Gravando no Banco OPER_OPSUL...</span>`;

      const payload = {{
        mode: "submit",
        data: document.getElementById("inpData").value,
        base: document.getElementById("inpBaseValue").value,
        responsavel_nome: document.getElementById("inpRespValue").value,
        responsavel_email: currentAuthUser.email || "",
        auth_systemuserid: currentAuthUser.userId || "",
        transportadora: document.getElementById("inpTransportadora").value.trim(),
        placa_ct: document.getElementById("inpPlaca").value.trim().toUpperCase(),
        cif_fob: document.getElementById("inpCifFob").value,
        item01_epis_ok: itemState[1],
        qual_epi_inapropriado: getSelectedChips("chipsEpi").join(", "),
        obs_item1: document.getElementById("inpObs1").value.trim(),
        foto_item1_base64: (!itemState[1] && itemPhotos[1]) ? itemPhotos[1].base64 : "",
        foto_item1_nome: (!itemState[1] && itemPhotos[1]) ? itemPhotos[1].nome : "",
        item02_veiculo_ok: itemState[2],
        qual_peca_nao_conforme: getSelectedChips("chipsPeca").join(", "),
        obs_item2: document.getElementById("inpObs2").value.trim(),
        foto_item2_base64: (!itemState[2] && itemPhotos[2]) ? itemPhotos[2].base64 : "",
        foto_item2_nome: (!itemState[2] && itemPhotos[2]) ? itemPhotos[2].nome : "",
        item03_tanque_ok: itemState[3],
        obs_item3: document.getElementById("inpObs3").value.trim(),
        foto_item3_base64: (!itemState[3] && itemPhotos[3]) ? itemPhotos[3].base64 : "",
        foto_item3_nome: (!itemState[3] && itemPhotos[3]) ? itemPhotos[3].nome : "",
        item04_aterramento_ok: itemState[4],
        obs_item4: document.getElementById("inpObs4").value.trim(),
        foto_item4_base64: (!itemState[4] && itemPhotos[4]) ? itemPhotos[4].base64 : "",
        foto_item4_nome: (!itemState[4] && itemPhotos[4]) ? itemPhotos[4].nome : "",
        item05_chave_geral_ok: itemState[5],
        obs_item5: document.getElementById("inpObs5").value.trim(),
        foto_item5_base64: (!itemState[5] && itemPhotos[5]) ? itemPhotos[5].base64 : "",
        foto_item5_nome: (!itemState[5] && itemPhotos[5]) ? itemPhotos[5].nome : "",
        observacao_geral: document.getElementById("inpObsGeral").value.trim()
      }};

      const totalPhotos = [1, 2, 3, 4, 5].filter(i => !itemState[i] && itemPhotos[i] && itemPhotos[i].base64).length;

      try {{
        let apiRes = {{}};
        if (FLOW_API_URL && !FLOW_API_URL.startsWith("__")) {{
          const resp = await fetch(FLOW_API_URL, {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify(payload)
          }});
          if (!resp.ok) throw new Error(`HTTP ${{resp.status}}`);
          try {{ apiRes = await resp.json(); }} catch (_) {{}}
        }}

        const totalEl = document.getElementById("statTotalBlitz");
        totalEl.textContent = (parseInt(totalEl.textContent || "0", 10) + 1).toString();

        const banner = document.getElementById("successBanner");
        const protoTxt = apiRes.protocolo ? `Protocolo: ${{apiRes.protocolo}} | ` : "";
        const teamsTxt = apiRes.notificado_teams ? ` | Alerta enviado ao grupo Teams (Blitz SSMA BAERI)` : "";
        document.getElementById("successDetails").textContent =
          `${{protoTxt}}Base: ${{payload.base}} | Placa CT: ${{payload.placa_ct}} | Transportadora: ${{payload.transportadora}} | Responsável: ${{payload.responsavel_nome}} (${{currentAuthUser.email || 'SSO Vibra'}}) | Fotos salvas no Dataverse: ${{totalPhotos}}${{teamsTxt}}`;
        banner.classList.add("visible");
        window.scrollTo({{ top: 0, behavior: "smooth" }});
      }} catch (err) {{
        alert("Erro ao enviar registro para a API: " + err.message);
      }} finally {{
        btn.disabled = false;
        btn.innerHTML = `<span>Registrar Blitz de SMS</span><span>→</span>`;
      }}
    }});

    window.resetFormKeepUser = function() {{
      document.getElementById("inpData").value = getLocalDateString();
      document.getElementById("inpTransportadora").value = "";
      document.getElementById("inpPlaca").value = "";
      document.getElementById("inpObsGeral").value = "";
      for (let i = 1; i <= 5; i++) {{
        setItemStatus(i, true);
        clearPhotoItem(i);
        document.getElementById(`inpObs${{i}}`).value = "";
      }}
      document.querySelectorAll(".chip-option.selected").forEach(c => c.classList.remove("selected"));
      document.getElementById("successBanner").classList.remove("visible");
    }};

    // === AUTENTICAÇÃO CORPORATIVA OBRIGATÓRIA (VIBRA ENTRA ID / DATAVERSE SSO) ===
    const OFFICIAL_SSO_URL = "https://orgd15f46d4.crm2.dynamics.com/WebResources/opsul_blitz_sms_app.html";
    let currentAuthUser = {{ userId: "", name: "", email: "", aadObjectId: "" }};

    function formatDisplayName(rawName) {{
      if (!rawName) return "";
      const clean = rawName.replace(/^#\\s*/, "").trim();
      if (clean.includes(",")) {{
        const parts = clean.split(",").map(s => s.trim()).filter(Boolean);
        if (parts.length === 2) return `${{parts[1]}} ${{parts[0]}}`;
      }}
      return clean;
    }}

    async function verifyCorporateSession() {{
      const overlay = document.getElementById("authGateOverlay");
      const msgEl = document.getElementById("authGateMessage");
      const btnRedirect = document.getElementById("btnAuthRedirect");

      // Se não estiver no domínio autenticado do Dataverse da Vibra, redireciona para forçar o login SSO Microsoft Entra ID
      if (window.location.hostname.toLowerCase() !== "orgd15f46d4.crm2.dynamics.com") {{
        msgEl.textContent = "Redirecionando para o login corporativo Vibra Energia (Microsoft Entra ID SSO)...";
        btnRedirect.style.display = "inline-flex";
        window.location.replace(OFFICIAL_SSO_URL);
        return false;
      }}

      try {{
        const whoResp = await fetch("/api/data/v9.2/WhoAmI", {{
          method: "GET",
          credentials: "include",
          headers: {{ "Accept": "application/json" }}
        }});
        if (!whoResp.ok) throw new Error(`Sessão não autenticada (HTTP ${{whoResp.status}})`);
        const whoData = await whoResp.json();
        const userId = whoData.UserId;
        if (!userId) throw new Error("UserId ausente na sessão");

        const userResp = await fetch(`/api/data/v9.2/systemusers(${{userId}})?$select=fullname,internalemailaddress,azureactivedirectoryobjectid`, {{
          method: "GET",
          credentials: "include",
          headers: {{ "Accept": "application/json" }}
        }});
        if (!userResp.ok) throw new Error(`Falha ao validar usuário corporativo (HTTP ${{userResp.status}})`);
        const userData = await userResp.json();
        const email = (userData.internalemailaddress || "").trim().toLowerCase();
        const dispName = formatDisplayName(userData.fullname || "");

        currentAuthUser = {{
          userId: userId,
          name: dispName,
          email: email,
          aadObjectId: userData.azureactivedirectoryobjectid || ""
        }};

        document.getElementById("authBadgePill").textContent = `🔒 VIBRA SSO • ${{email || dispName}}`;
        overlay.style.display = "none";

        lockResponsavelFromCorporateLogin(dispName, email);
        return true;
      }} catch (err) {{
        msgEl.textContent = "Para acessar o aplicativo Blitz de SMS, você precisa estar logado na sua conta corporativa Vibra Energia (@vibraenergia.com.br).";
        btnRedirect.style.display = "inline-flex";
        return false;
      }}
    }}

    // === INICIALIZAÇÃO ===
    (async function init() {{
      document.getElementById("inpData").value = getLocalDateString();

      // Popular datalist de transportadoras
      const dl = document.getElementById("transportadorasDatalist");
      dl.innerHTML = INITIAL_TRANSPORTADORAS.map(t => `<option value="${{t}}"></option>`).join("");

      // Restaurar última base operacional selecionada no dispositivo
      const savedBase = localStorage.getItem("opsul_saved_base");
      if (savedBase && basesList.includes(savedBase)) {{
        selectBase(savedBase);
      }}

      await verifyCorporateSession();
    }})();
  </script>
</body>
</html>
"""
    out_path = os.path.join(SCRATCH_DIR, "opsul_blitz_sms_app.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    repo_wr_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webresources", "opsul_blitz_sms_app.html")
    with open(repo_wr_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated {out_path} and {repo_wr_path} ({len(html)} bytes, {len(bases)} bases, {len(responsaveis)} responsaveis)")

if __name__ == "__main__":
    main()
