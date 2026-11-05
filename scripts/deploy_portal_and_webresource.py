import base64
import json
import os
import subprocess
import ssl
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
_orig_wrap = ssl.SSLContext.wrap_socket
ssl.SSLContext.wrap_socket = lambda self, *a, **kw: (setattr(self, "verify_flags", self.verify_flags & ~ssl.VERIFY_X509_STRICT), _orig_wrap(self, *a, **kw))[1]

ORG_URL = "https://orgd15f46d4.crm2.dynamics.com"
API_URL = f"{ORG_URL}/api/data/v9.2"
ENV_ID = "4a9ba077-4920-ea16-ae45-293f56eb85e3"
SCRATCH_DIR = r"C:\Users\CE9X\.gemini\antigravity-cli\brain\8cae6e32-993e-4789-bd1b-881b43fbd9e1\scratch"

API_CALLBACK_URL = "https://4a9ba0774920ea16ae45293f56eb85.e3.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/27/workflows/fb72dd18f9f2408da343a04df8987a4c/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=j18hLaW9dieZy0QgfWQ1k-QA1SokwZohMvoLgX8JKH0"

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

DV_TOKEN = get_token(ORG_URL + "/")
FLOW_TOKEN = get_token("https://service.flow.microsoft.com/")

def dv_req(method, path, body=None, extra_headers=None):
    url = f"{API_URL}/{path}" if not path.startswith("http") else path
    headers = {
        "Authorization": f"Bearer {DV_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "MSCRM.SolutionUniqueName": "OPER_OPSUL"
    }
    if extra_headers:
        headers.update(extra_headers)
    r = requests.request(method, url, json=body, headers=headers, verify=False, timeout=120)
    if not r.ok:
        print(f"DV HTTP {r.status_code}: {r.text[:600]}")
        r.raise_for_status()
    return r.json() if r.text else {}

def main():
    html_path = os.path.join(SCRATCH_DIR, "opsul_blitz_sms_app.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Inject live API_CALLBACK_URL
    html_content = html_content.replace("__FLOW_API_URL__", API_CALLBACK_URL)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Updated {html_path} with live API_CALLBACK_URL.")

    # 1. Create/Update Dataverse Web Resource in OPER_OPSUL solution
    wr_name = "opsul_blitz_sms_app.html"
    existing_wr = dv_req("GET", f"webresourceset?$filter=name eq '{wr_name}'&$select=webresourceid,name")
    b64_html = base64.b64encode(html_content.encode("utf-8")).decode("ascii")

    if existing_wr.get("value"):
        wr_id = existing_wr["value"][0]["webresourceid"]
        print(f"Updating existing Web Resource {wr_name} ({wr_id})...")
        dv_req("PATCH", f"webresourceset({wr_id})", {
            "content": b64_html,
            "displayname": "OPER_OPSUL - Formulário Blitz de SMS (Design Vibra)",
            "description": "Formulário Web / Power Pages Blitz de SMS com Busca Fuzzy de Bases e Catálogo de Responsáveis"
        })
    else:
        print(f"Creating Web Resource {wr_name} in solution OPER_OPSUL...")
        res = dv_req("POST", "webresourceset", {
            "name": wr_name,
            "displayname": "OPER_OPSUL - Formulário Blitz de SMS (Design Vibra)",
            "description": "Formulário Web / Power Pages Blitz de SMS com Busca Fuzzy de Bases e Catálogo de Responsáveis",
            "webresourcetype": 1,  # Webpage (HTML)
            "content": b64_html
        }, {"Prefer": "return=representation"})
        wr_id = res["webresourceid"]
        print(f"Created Web Resource: {wr_id}")

    # Publish Web Resource
    dv_req("POST", "PublishXml", {
        "ParameterXml": f"<importexportxml><webresources><webresource>{wr_id}</webresource></webresources></importexportxml>"
    })
    print(f"Published Web Resource {wr_name} ({ORG_URL}/WebResources/{wr_name})!")

    # 2. Create/Update Zero-Login Portal Flow (HTTP GET -> serves HTML directly without login)
    portal_flow_name = "OPER_OPSUL - Portal Web Blitz de SMS (Sem Login)"
    existing_pf = dv_req("GET", f"workflows?$filter=name eq '{portal_flow_name}' and category eq 5&$select=workflowid,name")

    # Escape "@" in HTML for Logic Apps expression parser (replace "@" with "@@")
    escaped_html = html_content.replace("@", "@@")

    portal_clientdata = {
        "properties": {
            "connectionReferences": {},
            "definition": {
                "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                "contentVersion": "1.0.0.0",
                "parameters": {
                    "$connections": {"defaultValue": {}, "type": "Object"},
                    "$authentication": {"defaultValue": {}, "type": "SecureObject"}
                },
                "triggers": {
                    "manual": {
                        "type": "Request",
                        "kind": "Http",
                        "inputs": {
                            "method": "GET",
                            "triggerAuthenticationType": "All"
                        }
                    }
                },
                "actions": {
                    "Response_Portal_HTML": {
                        "type": "Response",
                        "kind": "Http",
                        "inputs": {
                            "statusCode": 200,
                            "headers": {
                                "Content-Type": "text/html; charset=utf-8",
                                "Access-Control-Allow-Origin": "*",
                                "Cache-Control": "no-cache"
                            },
                            "body": escaped_html
                        },
                        "runAfter": {}
                    }
                },
                "outputs": {}
            }
        },
        "schemaVersion": "1.0.0.0"
    }

    if existing_pf.get("value"):
        pf_id = existing_pf["value"][0]["workflowid"]
        print(f"Updating existing Portal Flow: {pf_id}")
        dv_req("PATCH", f"workflows({pf_id})", {"clientdata": json.dumps(portal_clientdata)})
    else:
        res_pf = dv_req("POST", "workflows", {
            "name": portal_flow_name,
            "category": 5,
            "type": 1,
            "primaryentity": "none",
            "clientdata": json.dumps(portal_clientdata)
        }, {"Prefer": "return=representation"})
        pf_id = res_pf["workflowid"]
        print(f"Created Portal Flow: {pf_id}")

    dv_req("PATCH", f"workflows({pf_id})", {"statecode": 1, "statuscode": 2})
    print(f"Activated Portal Flow {pf_id}!")

    # Get Portal Flow Callback URL
    f_headers = {"Authorization": f"Bearer {FLOW_TOKEN}", "Accept": "application/json"}
    flows_res = requests.get(
        f"https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/{ENV_ID}/flows?api-version=2016-11-01",
        headers=f_headers, verify=False
    ).json()
    portal_url = None
    for fl in flows_res.get("value", []):
        if fl.get("properties", {}).get("workflowEntityId", "").lower() == pf_id.lower() or fl.get("properties", {}).get("displayName") == portal_flow_name:
            f_name = fl["name"]
            cb = requests.post(
                f"https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/{ENV_ID}/flows/{f_name}/triggers/manual/listCallbackUrl?api-version=2016-11-01",
                headers=f_headers, verify=False
            ).json()
            portal_url = cb.get("response", {}).get("value")
            print("PORTAL_PUBLIC_URL:", portal_url)

    # 3. Verify Anonymous GET on Portal URL and Anonymous POST on API URL
    if portal_url:
        r_get = requests.get(portal_url, verify=False, timeout=30)
        print(f"Anonymous GET Portal Test -> HTTP {r_get.status_code}, Content-Type: {r_get.headers.get('Content-Type')}, Length: {len(r_get.text)} bytes")

    r_post = requests.post(API_CALLBACK_URL, json={
        "mode": "submit",
        "data": "2026-11-05",
        "base": "BACUB",
        "responsavel_nome": "Ana Carolina da Silva Lima",
        "transportadora": "Transtassi",
        "placa_ct": "ABC1D23",
        "cif_fob": "CIF",
        "item01_epis_ok": True,
        "item02_veiculo_ok": True,
        "item03_tanque_ok": True,
        "item04_aterramento_ok": True,
        "item05_chave_geral_ok": True,
        "motorista_bloqueado": "NÃO",
        "observacao_geral": "Teste de integração automatizada OPER_OPSUL"
    }, verify=False, timeout=30)
    print(f"Anonymous POST API Test -> HTTP {r_post.status_code}, Response: {r_post.text}")

if __name__ == "__main__":
    main()
