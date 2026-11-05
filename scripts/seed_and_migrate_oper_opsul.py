import json
import subprocess
import os
import re
import ssl
import requests
import urllib3
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
_orig_wrap = ssl.SSLContext.wrap_socket
ssl.SSLContext.wrap_socket = lambda self, *a, **kw: (setattr(self, "verify_flags", self.verify_flags & ~ssl.VERIFY_X509_STRICT), _orig_wrap(self, *a, **kw))[1]

ORG_URL = "https://orgd15f46d4.crm2.dynamics.com"
API_URL = f"{ORG_URL}/api/data/v9.2"
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

def get_token(resource):
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", r"C:\Users\CE9X\.agents\skills\azure-cli-netskope\scripts\invoke-az-netskope.ps1",
        "account", "get-access-token",
        "--resource", resource
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(res.stdout)["accessToken"]

TOKEN = get_token(ORG_URL + "/")

SESSION = requests.Session()
SESSION.verify = False
adapter = HTTPAdapter(pool_connections=32, pool_maxsize=32, max_retries=3)
SESSION.mount("https://", adapter)
SESSION.headers.update({
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "OData-MaxVersion": "4.0",
    "OData-Version": "4.0"
})

def dv_request(method, path, body=None, prefer_return=False):
    url = (f"{API_URL}/{path}" if not path.startswith("http") else path)
    extra = {"Prefer": "return=representation"} if prefer_return else None
    resp = SESSION.request(method, url, json=body, headers=extra, timeout=120, verify=False)
    if not resp.ok:
        print(f"HTTP {resp.status_code} on {method} {path}: {resp.text[:400]}")
        resp.raise_for_status()
    return resp.json() if resp.text else {"status": resp.status_code}

def get_entity_set_names():
    ents = {}
    for lname in ["opsul_base", "opsul_responsavel", "opsul_usuarioregional", "opsul_blitzsms"]:
        res = dv_request("GET", f"EntityDefinitions(LogicalName='{lname}')?$select=EntitySetName,LogicalName")
        ents[lname] = res["EntitySetName"]
    print("EntitySetNames:", ents)
    return ents

def classify_base(sigla):
    s = sigla.upper().strip()
    if s.startswith("BA"):
        return "BA - Base Operacional"
    if s.startswith("RA"):
        return "RA - Revenda / Abastecimento"
    if s.startswith("AR"):
        return "AR - Armazém / Regional"
    if s.startswith("AI"):
        return "AI - Aeroporto / Aviação"
    if s.startswith("DE"):
        return "DE - Depósito"
    if s.startswith("BE"):
        return "BE - Base Especial"
    return "Corporativo / Outros"

def normalize_name(name):
    if not name:
        return ""
    n = re.sub(r"\s+", " ", str(name).strip())
    n = n.strip(";-., ")
    if not n or len(n) < 2:
        return ""
    # Title case if all upper or all lower
    if n.isupper() or n.islower():
        parts = n.title().split(" ")
        lower_words = {"De", "Da", "Do", "Das", "Dos", "E"}
        n = " ".join([p.lower() if i > 0 and p in lower_words else p for i, p in enumerate(parts)])
    return n

def main():
    sets = get_entity_set_names()
    items_path = os.path.join(SCRATCH_DIR, "blitz_all_items.json")
    with open(items_path, "r", encoding="utf-8-sig") as f:
        sp_items = json.load(f)
    print(f"Loaded {len(sp_items)} historical SharePoint items.")

    # 1. Seed opsul_usuarioregional
    print("=== 1. Seeding opsul_usuarioregional ===")
    existing_reg = dv_request("GET", f"{sets['opsul_usuarioregional']}?$select=opsul_email,opsul_usuarioregionalid")
    reg_by_email = {r.get("opsul_email", "").lower(): r["opsul_usuarioregionalid"] for r in existing_reg.get("value", [])}

    regional_users = [
        {
            "opsul_nome": "Wedson Pereira da Silva",
            "opsul_email": "wedson@vibraenergia.com.br",
            "opsul_entra_oid": "19f80cc5-873f-4aa3-afea-46e92de2bfa2",
            "opsul_departamento": "Operação Regional Sul e Sudeste",
            "opsul_cargo": "Empregado",
            "opsul_perfil": "Gestor Regional OPSUL",
            "opsul_regional": "OPSUL - Sul e Sudeste",
            "opsul_sso_habilitado": True,
            "opsul_ativo": True
        },
        {
            "opsul_nome": "Ana Claudia Camargos Sales",
            "opsul_email": "anasales@vibraenergia.com.br",
            "opsul_entra_oid": "a57b45d7-0126-4f0a-8c45-f3a65e7161d7",
            "opsul_departamento": "Operação Regional Sul e Sudeste",
            "opsul_cargo": "Empregada",
            "opsul_perfil": "Gestora Regional OPSUL",
            "opsul_regional": "OPSUL - Sul e Sudeste",
            "opsul_sso_habilitado": True,
            "opsul_ativo": True
        }
    ]
    for u in regional_users:
        em = u["opsul_email"].lower()
        if em not in reg_by_email:
            dv_request("POST", sets["opsul_usuarioregional"], u)
            print(f"  Created regional user: {u['opsul_nome']} ({u['opsul_email']})")
        else:
            print(f"  Regional user already exists: {u['opsul_email']}")

    # 2. Seed opsul_base
    print("=== 2. Seeding opsul_base ===")
    base_set = set()
    for line in USER_BASES_RAW.splitlines():
        b = line.strip()
        if b:
            base_set.add(b)
    for item in sp_items:
        b_obj = item.get("Base")
        if isinstance(b_obj, dict) and b_obj.get("Value"):
            base_set.add(b_obj["Value"].strip())

    all_bases = sorted(base_set)
    print(f"Total unique bases to seed: {len(all_bases)}")

    existing_bases_res = dv_request("GET", f"{sets['opsul_base']}?$select=opsul_sigla,opsul_baseid&$top=5000")
    base_map = {r["opsul_sigla"].upper(): r["opsul_baseid"] for r in existing_bases_res.get("value", []) if r.get("opsul_sigla")}

    missing_bases = [b for b in all_bases if b.upper() not in base_map]
    print(f"Inserting {len(missing_bases)} missing bases...")

    def insert_base(sigla):
        body = {
            "opsul_sigla": sigla,
            "opsul_categoria": classify_base(sigla),
            "opsul_descricao": f"Unidade Operacional {sigla} ({classify_base(sigla)})",
            "opsul_ativo": True
        }
        res = dv_request("POST", sets["opsul_base"], body, prefer_return=True)
        return sigla.upper(), res["opsul_baseid"]

    if missing_bases:
        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = [ex.submit(insert_base, b) for b in missing_bases]
            for fut in as_completed(futures):
                k, vid = fut.result()
                base_map[k] = vid
    print(f"opsul_base ready with {len(base_map)} records.")

    # 3. Extract & Seed opsul_responsavel
    print("=== 3. Seeding opsul_responsavel ===")
    resp_stats = {}  # key: upper_name -> {nome, email, base_padrao, count}
    for item in sp_items:
        raw_name = item.get("Nomedorespons_x00e1_velpelaBlitz")
        email = ""
        resp_obj = item.get("Respons_x00e1_velpelaBlitz")
        if isinstance(resp_obj, dict):
            if not raw_name and resp_obj.get("DisplayName"):
                raw_name = resp_obj.get("DisplayName")
            email = resp_obj.get("Email") or ""
        if not raw_name:
            auth_obj = item.get("Author")
            if isinstance(auth_obj, dict) and auth_obj.get("DisplayName"):
                raw_name = auth_obj.get("DisplayName")
                if not email:
                    email = auth_obj.get("Email") or ""

        clean_name = normalize_name(raw_name)
        if not clean_name:
            continue
        key = clean_name.upper()
        base_val = ""
        if isinstance(item.get("Base"), dict):
            base_val = item["Base"].get("Value") or ""

        if key not in resp_stats:
            resp_stats[key] = {
                "nome": clean_name,
                "email": email,
                "base_padrao": base_val,
                "count": 1
            }
        else:
            resp_stats[key]["count"] += 1
            if email and not resp_stats[key]["email"]:
                resp_stats[key]["email"] = email
            if base_val:
                resp_stats[key]["base_padrao"] = base_val

    print(f"Total unique normalized Responsáveis extracted: {len(resp_stats)}")
    existing_resp_res = dv_request("GET", f"{sets['opsul_responsavel']}?$select=opsul_nome,opsul_responsavelid&$top=5000")
    resp_map = {r["opsul_nome"].upper(): r["opsul_responsavelid"] for r in existing_resp_res.get("value", []) if r.get("opsul_nome")}

    missing_resps = [v for k, v in resp_stats.items() if k not in resp_map]
    print(f"Inserting {len(missing_resps)} missing Responsáveis...")

    def insert_resp(info):
        body = {
            "opsul_nome": info["nome"][:150],
            "opsul_email": (info["email"] or "")[:150],
            "opsul_base_padrao": (info["base_padrao"] or "")[:50],
            "opsul_total_blitz": info["count"],
            "opsul_ativo": True
        }
        res = dv_request("POST", sets["opsul_responsavel"], body, prefer_return=True)
        return info["nome"].upper(), res["opsul_responsavelid"]

    if missing_resps:
        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = [ex.submit(insert_resp, r) for r in missing_resps]
            for fut in as_completed(futures):
                k, vid = fut.result()
                resp_map[k] = vid
    print(f"opsul_responsavel ready with {len(resp_map)} records.")

    # 4. Migrate all 3,761 SharePoint items into opsul_blitzsms
    print("=== 4. Migrating 3,761 Blitz de SMS records into opsul_blitzsms ===")
    existing_blitz = set()
    next_link = f"{sets['opsul_blitzsms']}?$select=opsul_sp_id&$top=5000"
    while next_link:
        page = dv_request("GET", next_link)
        for r in page.get("value", []):
            if r.get("opsul_sp_id") is not None:
                existing_blitz.add(int(r["opsul_sp_id"]))
        next_link = page.get("@odata.nextLink")

    to_insert = [it for it in sp_items if int(it["ID"]) not in existing_blitz]
    print(f"Already migrated: {len(existing_blitz)} | Remaining to insert: {len(to_insert)}")

    def build_blitz_payload(item):
        sp_id = int(item["ID"])
        base_val = ""
        if isinstance(item.get("Base"), dict):
            base_val = (item["Base"].get("Value") or "").strip()

        raw_name = item.get("Nomedorespons_x00e1_velpelaBlitz")
        email = ""
        resp_obj = item.get("Respons_x00e1_velpelaBlitz")
        if isinstance(resp_obj, dict):
            if not raw_name and resp_obj.get("DisplayName"):
                raw_name = resp_obj.get("DisplayName")
            email = resp_obj.get("Email") or ""
        if not raw_name and isinstance(item.get("Author"), dict):
            raw_name = item["Author"].get("DisplayName") or ""
            if not email:
                email = item["Author"].get("Email") or ""
        clean_name = normalize_name(raw_name) or "Não Informado"

        data_str = item.get("Data")
        if not data_str and item.get("Created"):
            data_str = item["Created"][:10]
        if not data_str:
            data_str = "2026-01-01"

        placa = (item.get("PlacadoCT") or "").strip()
        titulo = (item.get("Title") or f"{base_val or 'OPSUL'} - {data_str} - {placa or f'ID-{sp_id}'}")[:255]

        epis_arr = item.get("QualEPIn_x00e3_oestaapropriado_x") or []
        epis_str = ", ".join([x.get("Value", "") for x in epis_arr if isinstance(x, dict) and x.get("Value")])

        pecas_arr = item.get("Qualpe_x00e7_an_x00e3_oestaconfo") or []
        pecas_str = ", ".join([x.get("Value", "") for x in pecas_arr if isinstance(x, dict) and x.get("Value")])

        cif_fob = ""
        if isinstance(item.get("CIFouFOB"), dict):
            cif_fob = item["CIFouFOB"].get("Value") or ""

        bloqueado = ""
        if isinstance(item.get("MotoristaBloqueado_x003f_"), dict):
            val_b = str(item["MotoristaBloqueado_x003f_"].get("Value") or "").strip().upper()
            if val_b in ("1", "SIM", "TRUE"):
                bloqueado = "SIM"
            elif val_b in ("0", "NÃO", "NAO", "FALSE"):
                bloqueado = "NÃO"
            else:
                bloqueado = val_b

        author_name = ""
        if isinstance(item.get("Author"), dict):
            author_name = item["Author"].get("DisplayName") or ""

        payload = {
            "opsul_titulo": titulo,
            "opsul_sp_id": sp_id,
            "opsul_data": data_str[:10],
            "opsul_base": (base_val or "N/A")[:50],
            "opsul_responsavel_nome": clean_name[:150],
            "opsul_responsavel_email": (email or "")[:150],
            "opsul_transportadora": (item.get("Transportadora") or "")[:255],
            "opsul_placa_ct": placa[:50],
            "opsul_cif_fob": cif_fob[:20],
            "opsul_item01_epis_ok": bool(item.get("OsEpiss_x00e3_oapropriadosparaaa", True)),
            "opsul_qual_epi_inapropriado": epis_str[:500],
            "opsul_obs_item1": (item.get("ObsItem1") or "")[:2000],
            "opsul_item02_veiculo_ok": bool(item.get("Ve_x00ed_culoest_x00e1__x00ed_nt", True)),
            "opsul_qual_peca_nao_conforme": pecas_str[:500],
            "opsul_obs_item2": (item.get("ObsItem3") or "")[:2000],
            "opsul_item03_tanque_ok": bool(item.get("OTanquedove_x00ed_culoest_x00e1_", True)),
            "opsul_obs_item3": (item.get("ObsItem4") or "")[:2000],
            "opsul_item04_aterramento_ok": bool(item.get("Condi_x00e7__x00f5_esdossistemas", True)),
            "opsul_obs_item4": (item.get("ObsItem5") or "")[:2000],
            "opsul_item05_chave_geral_ok": bool(item.get("ChavegeraldoCTest_x00e1_desempen", True)),
            "opsul_obs_item5": (item.get("ObsItem6") or "")[:2000],
            "opsul_motorista_bloqueado": bloqueado[:30],
            "opsul_observacao_geral": (item.get("Observa_x00e7__x00e3_o") or "")[:4000],
            "opsul_sp_author": author_name[:150]
        }
        if item.get("Created"):
            payload["opsul_sp_created"] = item["Created"]
        if item.get("Modified"):
            payload["opsul_sp_modified"] = item["Modified"]

        if base_val and base_val.upper() in base_map:
            payload["opsul_baseid@odata.bind"] = f"/{sets['opsul_base']}({base_map[base_val.upper()]})"
        if clean_name.upper() in resp_map:
            payload["opsul_responsavelid@odata.bind"] = f"/{sets['opsul_responsavel']}({resp_map[clean_name.upper()]})"

        return payload

    def insert_blitz_item(item):
        body = build_blitz_payload(item)
        dv_request("POST", sets["opsul_blitzsms"], body)
        return item["ID"]

    if to_insert:
        done = 0
        with ThreadPoolExecutor(max_workers=16) as ex:
            futures = [ex.submit(insert_blitz_item, it) for it in to_insert]
            for fut in as_completed(futures):
                _ = fut.result()
                done += 1
                if done % 250 == 0 or done == len(to_insert):
                    print(f"  Progress: {done}/{len(to_insert)} records migrated...")

    print("MIGRATION COMPLETE!")

if __name__ == "__main__":
    main()
