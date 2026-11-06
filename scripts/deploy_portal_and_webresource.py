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
REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH_DIR = r"C:\Users\CE9X\.gemini\antigravity-cli\brain\8cae6e32-993e-4789-bd1b-881b43fbd9e1\scratch"

API_FLOW_ID = "592191f7-47d9-f111-84e8-e4fade0322c2"
PORTAL_FLOW_ID = "8bfaac34-48d9-f111-84e8-e4fade0322c2"
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
        print(f"DV HTTP {r.status_code} on {method} {path}: {r.text[:800]}")
        r.raise_for_status()
    return r.json() if r.text else {}

def ensure_dv_conn_ref():
    logical_name = "opsul_sharedcommondataserviceforapps"
    res = dv_req("GET", f"connectionreferences?$filter=connectionreferencelogicalname eq '{logical_name}'&$select=connectionreferenceid,connectionid")
    if res.get("value"):
        cr_id = res["value"][0]["connectionreferenceid"]
        print(f"Updating existing Connection Reference {logical_name} ({cr_id})...")
        dv_req("PATCH", f"connectionreferences({cr_id})", {
            "connectionid": "shared-commondataser-b382b50b",
            "connectorid": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
            "statecode": 0,
            "statuscode": 1
        })
        return logical_name
    print(f"Creating Connection Reference {logical_name}...")
    dv_req("POST", "connectionreferences", {
        "connectionreferencelogicalname": logical_name,
        "connectionreferencedisplayname": "OPER_OPSUL - Microsoft Dataverse",
        "connectorid": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
        "connectionid": "shared-commondataser-b382b50b",
        "description": "Referência de conexão oficial Microsoft Dataverse da solução OPER_OPSUL"
    })
    return logical_name

def build_api_flow_clientdata(conn_ref_logical):
    photo_conditions = {}
    for i in range(1, 6):
        prev_dep = "Criar_Registro_Blitz_Dataverse" if i == 1 else f"Cond_Foto_Item{i-1}"
        run_after = {prev_dep: ["Succeeded"] if i == 1 else ["Succeeded", "Skipped", "Failed"]}
        photo_conditions[f"Cond_Foto_Item{i}"] = {
            "type": "If",
            "expression": {
                "and": [
                    {
                        "not": {
                            "equals": [
                                f"@empty(triggerBody()?['foto_item{i}_base64'])",
                                True
                            ]
                        }
                    }
                ]
            },
            "actions": {
                f"Upload_Foto_Item{i}": {
                    "type": "OpenApiConnection",
                    "inputs": {
                        "host": {
                            "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
                            "connectionName": "shared_commondataserviceforapps",
                            "operationId": "UpdateEntityFileImageFieldContent"
                        },
                        "parameters": {
                            "entityName": "opsul_blitzsmses",
                            "recordId": "@outputs('Criar_Registro_Blitz_Dataverse')?['body/opsul_blitzsmsid']",
                            "fileImageFieldName": f"opsul_foto_item{i}",
                            "item": f"@base64ToBinary(triggerBody()?['foto_item{i}_base64'])",
                            "x-ms-file-name": f"@coalesce(triggerBody()?['foto_item{i}_nome'], 'blitz_item0{i}.jpg')"
                        }
                    },
                    "runAfter": {}
                }
            },
            "else": {
                "actions": {}
            },
            "runAfter": run_after
        }

    actions = {
        "Compose_Protocolo": {
            "type": "Compose",
            "inputs": "@concat('BLITZ-', coalesce(triggerBody()?['base'], 'OPSUL'), '-', toUpper(substring(guid(), 0, 8)))",
            "runAfter": {}
        },
        "Criar_Registro_Blitz_Dataverse": {
            "type": "OpenApiConnection",
            "inputs": {
                "host": {
                    "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
                    "connectionName": "shared_commondataserviceforapps",
                    "operationId": "CreateRecord"
                },
                "parameters": {
                    "entityName": "opsul_blitzsmses",
                    "item/opsul_titulo": "@concat(coalesce(triggerBody()?['base'], 'OPSUL'), ' - ', coalesce(triggerBody()?['data'], ''), ' - ', coalesce(triggerBody()?['placa_ct'], ''), ' (', outputs('Compose_Protocolo'), ')')",
                    "item/opsul_data": "@coalesce(triggerBody()?['data'], formatDateTime(utcNow(), 'yyyy-MM-dd'))",
                    "item/opsul_base": "@coalesce(triggerBody()?['base'], 'N/A')",
                    "item/opsul_responsavel_nome": "@coalesce(triggerBody()?['responsavel_nome'], 'Não Informado')",
                    "item/opsul_responsavel_email": "@coalesce(triggerBody()?['responsavel_email'], '')",
                    "item/opsul_transportadora": "@coalesce(triggerBody()?['transportadora'], '')",
                    "item/opsul_placa_ct": "@coalesce(triggerBody()?['placa_ct'], '')",
                    "item/opsul_cif_fob": "@coalesce(triggerBody()?['cif_fob'], '')",
                    "item/opsul_item01_epis_ok": "@coalesce(triggerBody()?['item01_epis_ok'], true)",
                    "item/opsul_qual_epi_inapropriado": "@coalesce(triggerBody()?['qual_epi_inapropriado'], '')",
                    "item/opsul_obs_item1": "@coalesce(triggerBody()?['obs_item1'], '')",
                    "item/opsul_item02_veiculo_ok": "@coalesce(triggerBody()?['item02_veiculo_ok'], true)",
                    "item/opsul_qual_peca_nao_conforme": "@coalesce(triggerBody()?['qual_peca_nao_conforme'], '')",
                    "item/opsul_obs_item2": "@coalesce(triggerBody()?['obs_item2'], '')",
                    "item/opsul_item03_tanque_ok": "@coalesce(triggerBody()?['item03_tanque_ok'], true)",
                    "item/opsul_obs_item3": "@coalesce(triggerBody()?['obs_item3'], '')",
                    "item/opsul_item04_aterramento_ok": "@coalesce(triggerBody()?['item04_aterramento_ok'], true)",
                    "item/opsul_obs_item4": "@coalesce(triggerBody()?['obs_item4'], '')",
                    "item/opsul_item05_chave_geral_ok": "@coalesce(triggerBody()?['item05_chave_geral_ok'], true)",
                    "item/opsul_obs_item5": "@coalesce(triggerBody()?['obs_item5'], '')",
                    "item/opsul_observacao_geral": "@coalesce(triggerBody()?['observacao_geral'], '')"
                }
            },
            "runAfter": {
                "Compose_Protocolo": ["Succeeded"]
            }
        }
    }
    actions.update(photo_conditions)
    actions["Response_OK"] = {
        "type": "Response",
        "kind": "Http",
        "inputs": {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Content-Type": "application/json; charset=utf-8"
            },
            "body": {
                "ok": True,
                "protocolo": "@{outputs('Compose_Protocolo')}",
                "blitz_id": "@{outputs('Criar_Registro_Blitz_Dataverse')?['body/opsul_blitzsmsid']}",
                "base": "@{triggerBody()?['base']}",
                "responsavel_nome": "@{triggerBody()?['responsavel_nome']}",
                "responsavel_email": "@{triggerBody()?['responsavel_email']}",
                "placa_ct": "@{triggerBody()?['placa_ct']}",
                "solution": "OPER_OPSUL"
            }
        },
        "runAfter": {
            "Cond_Foto_Item5": ["Succeeded", "Skipped", "Failed"]
        }
    }

    return {
        "properties": {
            "connectionReferences": {
                "shared_commondataserviceforapps": {
                    "runtimeSource": "embedded",
                    "connection": {
                        "name": "shared-commondataser-b382b50b",
                        "connectionReferenceLogicalName": conn_ref_logical
                    },
                    "api": {
                        "name": "shared_commondataserviceforapps"
                    }
                }
            },
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
                            "triggerAuthenticationType": "All",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "mode": {"type": "string"},
                                    "data": {"type": "string"},
                                    "base": {"type": "string"},
                                    "responsavel_nome": {"type": "string"},
                                    "responsavel_email": {"type": "string"},
                                    "auth_systemuserid": {"type": "string"},
                                    "transportadora": {"type": "string"},
                                    "placa_ct": {"type": "string"},
                                    "cif_fob": {"type": "string"},
                                    "item01_epis_ok": {"type": "boolean"},
                                    "qual_epi_inapropriado": {"type": "string"},
                                    "obs_item1": {"type": "string"},
                                    "foto_item1_base64": {"type": "string"},
                                    "foto_item1_nome": {"type": "string"},
                                    "item02_veiculo_ok": {"type": "boolean"},
                                    "qual_peca_nao_conforme": {"type": "string"},
                                    "obs_item2": {"type": "string"},
                                    "foto_item2_base64": {"type": "string"},
                                    "foto_item2_nome": {"type": "string"},
                                    "item03_tanque_ok": {"type": "boolean"},
                                    "obs_item3": {"type": "string"},
                                    "foto_item3_base64": {"type": "string"},
                                    "foto_item3_nome": {"type": "string"},
                                    "item04_aterramento_ok": {"type": "boolean"},
                                    "obs_item4": {"type": "string"},
                                    "foto_item4_base64": {"type": "string"},
                                    "foto_item4_nome": {"type": "string"},
                                    "item05_chave_geral_ok": {"type": "boolean"},
                                    "obs_item5": {"type": "string"},
                                    "foto_item5_base64": {"type": "string"},
                                    "foto_item5_nome": {"type": "string"},
                                    "observacao_geral": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "actions": actions,
                "outputs": {}
            }
        },
        "schemaVersion": "1.0.0.0"
    }

def main():
    conn_ref_logical = ensure_dv_conn_ref()

    # 1. Update API Flow in Dataverse
    print(f"Updating API Flow {API_FLOW_ID}...")
    api_clientdata = build_api_flow_clientdata(conn_ref_logical)
    dv_req("PATCH", f"workflows({API_FLOW_ID})", {"clientdata": json.dumps(api_clientdata)})
    dv_req("POST", "PublishXml", {
        "ParameterXml": f"<importexportxml><workflows><workflow>{API_FLOW_ID}</workflow></workflows></importexportxml>"
    })
    dv_req("PATCH", f"workflows({API_FLOW_ID})", {"statecode": 1, "statuscode": 2})
    print(f"Published and Activated API Flow {API_FLOW_ID}!")

    # 2. Inject live API_CALLBACK_URL into HTML and update WebResource + Portal Flow
    repo_html_path = os.path.join(REPO_DIR, "webresources", "opsul_blitz_sms_app.html")
    with open(repo_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    html_content = html_content.replace("__FLOW_API_URL__", API_CALLBACK_URL)
    with open(repo_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    if os.path.exists(SCRATCH_DIR):
        with open(os.path.join(SCRATCH_DIR, "opsul_blitz_sms_app.html"), "w", encoding="utf-8") as f:
            f.write(html_content)
    print(f"Updated {repo_html_path} with live API_CALLBACK_URL.")

    wr_name = "opsul_blitz_sms_app.html"
    existing_wr = dv_req("GET", f"webresourceset?$filter=name eq '{wr_name}'&$select=webresourceid,name")
    b64_html = base64.b64encode(html_content.encode("utf-8")).decode("ascii")

    if existing_wr.get("value"):
        wr_id = existing_wr["value"][0]["webresourceid"]
        print(f"Updating existing Web Resource {wr_name} ({wr_id})...")
        dv_req("PATCH", f"webresourceset({wr_id})", {
            "content": b64_html,
            "displayname": "OPER_OPSUL - Formulário Blitz de SMS (Design Vibra)",
            "description": "Formulário Web / Power Pages Blitz de SMS com Busca Fuzzy, Catálogo de Responsáveis e Upload de Fotos para Dataverse"
        })
    else:
        res = dv_req("POST", "webresourceset", {
            "name": wr_name,
            "displayname": "OPER_OPSUL - Formulário Blitz de SMS (Design Vibra)",
            "description": "Formulário Web / Power Pages Blitz de SMS com Busca Fuzzy, Catálogo de Responsáveis e Upload de Fotos para Dataverse",
            "webresourcetype": 1,
            "content": b64_html
        }, {"Prefer": "return=representation"})
        wr_id = res["webresourceid"]

    dv_req("POST", "PublishXml", {
        "ParameterXml": f"<importexportxml><webresources><webresource>{wr_id}</webresource></webresources></importexportxml>"
    })
    print(f"Published Web Resource {wr_name}!")

    sso_url = "https://orgd15f46d4.crm2.dynamics.com/WebResources/opsul_blitz_sms_app.html"
    redirect_html = (
        "<!DOCTYPE html><html lang='pt-BR'><head><meta charset='UTF-8' />"
        f"<meta http-equiv='refresh' content='0;url={sso_url}' />"
        "<title>Redirecionando para Login Corporativo Vibra...</title>"
        f"<script>window.location.replace('{sso_url}');</script></head>"
        "<body style='font-family:sans-serif;background:#004415;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;'>"
        f"<p>Redirecionando para autenticação corporativa Vibra Energia (<a href='{sso_url}' style='color:#FEDC00;'>clique aqui</a>)...</p>"
        "</body></html>"
    )
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
                                "Cache-Control": "no-store, no-cache, must-revalidate"
                            },
                            "body": redirect_html
                        },
                        "runAfter": {}
                    }
                },
                "outputs": {}
            }
        },
        "schemaVersion": "1.0.0.0"
    }

    dv_req("PATCH", f"workflows({PORTAL_FLOW_ID})", {"clientdata": json.dumps(portal_clientdata)})
    dv_req("POST", "PublishXml", {
        "ParameterXml": f"<importexportxml><workflows><workflow>{PORTAL_FLOW_ID}</workflow></workflows></importexportxml>"
    })
    dv_req("PATCH", f"workflows({PORTAL_FLOW_ID})", {"statecode": 1, "statuscode": 2})
    print(f"Published and Activated Portal Flow {PORTAL_FLOW_ID}!")

    # 3. Export updated snapshots into repo/flows/
    for wf_id, slug in [(PORTAL_FLOW_ID, "oper_opsul_portal_web_blitz_de_sms"), (API_FLOW_ID, "oper_opsul_api_blitz_de_sms")]:
        wf_data = dv_req("GET", f"workflows({wf_id})?$select=workflowid,name,statecode,statuscode,clientdata,modifiedon,createdon")
        cd = json.loads(wf_data.get("clientdata", "{}"))
        flow_dir = os.path.join(REPO_DIR, "flows", slug)
        os.makedirs(flow_dir, exist_ok=True)
        with open(os.path.join(flow_dir, "flow_full.json"), "w", encoding="utf-8") as f:
            json.dump(wf_data, f, indent=2, ensure_ascii=False)
        with open(os.path.join(flow_dir, "definition.wdl.json"), "w", encoding="utf-8") as f:
            json.dump(cd.get("properties", {}).get("definition", {}), f, indent=2, ensure_ascii=False)
        with open(os.path.join(flow_dir, "connection_references.json"), "w", encoding="utf-8") as f:
            json.dump(cd.get("properties", {}).get("connectionReferences", {}), f, indent=2, ensure_ascii=False)
        print(f"Exported flow snapshots for {slug}.")

if __name__ == "__main__":
    main()
