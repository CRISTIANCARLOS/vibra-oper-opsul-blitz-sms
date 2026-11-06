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

TEAMS_ORG_URL = "https://org165415fc.crm.dynamics.com"
TEAMS_API_URL = f"{TEAMS_ORG_URL}/api/data/v9.2"
TEAMS_ENV_ID = "898c553e-12ff-e6c6-8b11-bc7586165a03"
BAERI_GROUP_CHAT_ID = "19:063ca6b11e714dc8b17d26e11c0ebd40@thread.v2"

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
TEAMS_DV_TOKEN = get_token(TEAMS_ORG_URL + "/")
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

def teams_dv_req(method, path, body=None, extra_headers=None):
    url = f"{TEAMS_API_URL}/{path}" if not path.startswith("http") else path
    headers = {
        "Authorization": f"Bearer {TEAMS_DV_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0"
    }
    if extra_headers:
        headers.update(extra_headers)
    r = requests.request(method, url, json=body, headers=headers, verify=False, timeout=120)
    if not r.ok:
        print(f"TEAMS DV HTTP {r.status_code} on {method} {path}: {r.text[:800]}")
        r.raise_for_status()
    return r.json() if r.text else {}

def ensure_teams_alert_flow():
    flow_name = "OPER_OPSUL - Alerta de Desvio Blitz de SMS no Teams (BAERI)"
    card_dict = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "🚨 ALERTA DE DESVIO EM BLITZ DE SMS — BASE @{coalesce(triggerBody()?['base'], 'BAERI')}",
                "weight": "Bolder",
                "size": "Medium",
                "color": "Attention",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": "Foi registrada uma Blitz de SMS na unidade **@{coalesce(triggerBody()?['base'], 'BAERI')}** com item(ns) não conforme(s) no checklist crítico.",
                "wrap": True
            },
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Protocolo:", "value": "@{coalesce(triggerBody()?['protocolo'], '-')}"},
                    {"title": "Data da Blitz:", "value": "@{coalesce(triggerBody()?['data'], '-')}"},
                    {"title": "Base Operacional:", "value": "@{coalesce(triggerBody()?['base'], 'BAERI')}"},
                    {"title": "Placa CT / Frete:", "value": "@{coalesce(triggerBody()?['placa_ct'], '-')} (@{coalesce(triggerBody()?['cif_fob'], '-')})"},
                    {"title": "Transportadora:", "value": "@{outputs('Sanitizar_Campos_Livres')?['Transportadora']}"},
                    {"title": "Responsável Blitz:", "value": "@{outputs('Sanitizar_Campos_Livres')?['Responsavel']}"},
                    {"title": "Sessão SSO (Tablet):", "value": "@{coalesce(triggerBody()?['responsavel_email'], '-')}"},
                    {"title": "Itens com Desvio:", "value": "@{string(coalesce(triggerBody()?['qtd_desvios'], 1))} de 5"},
                    {"title": "Fotos Anexadas:", "value": "@{string(coalesce(triggerBody()?['qtd_fotos'], 0))} foto(s) no Dataverse"}
                ]
            },
            {
                "type": "Container",
                "style": "attention",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "⚠️ **Detalhamento dos Desvios Apontados no Checklist:**",
                        "weight": "Bolder",
                        "wrap": True
                    },
                    {
                        "type": "TextBlock",
                        "text": "@{outputs('Sanitizar_Campos_Livres')?['DetalhesDesvios']}",
                        "wrap": True
                    }
                ]
            }
        ]
    }
    card_json_str = json.dumps(card_dict, ensure_ascii=False)

    clientdata = {
        "properties": {
            "connectionReferences": {
                "shared_teams": {
                    "runtimeSource": "embedded",
                    "connection": {
                        "name": "shared-teams-cf39a891-ddf6-442d-b7b2-00885b7377c5",
                        "connectionReferenceLogicalName": "new_sharedteams_c3243"
                    },
                    "api": {
                        "name": "shared_teams"
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
                                    "group_chat_id": {"type": "string"},
                                    "protocolo": {"type": "string"},
                                    "data": {"type": "string"},
                                    "base": {"type": "string"},
                                    "placa_ct": {"type": "string"},
                                    "cif_fob": {"type": "string"},
                                    "transportadora": {"type": "string"},
                                    "responsavel_nome": {"type": "string"},
                                    "responsavel_email": {"type": "string"},
                                    "qtd_desvios": {"type": "integer"},
                                    "qtd_fotos": {"type": "integer"},
                                    "detalhes_desvios": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "actions": {
                    "Sanitizar_Campos_Livres": {
                        "type": "Compose",
                        "inputs": {
                            "Transportadora": "@replace(replace(replace(replace(coalesce(triggerBody()?['transportadora'], '-'), '\"', ''), '\\', '/'), '\r', ' '), '\n', ' ')",
                            "Responsavel": "@replace(replace(replace(replace(coalesce(triggerBody()?['responsavel_nome'], '-'), '\"', ''), '\\', '/'), '\r', ' '), '\n', ' ')",
                            "DetalhesDesvios": "@replace(replace(replace(replace(coalesce(triggerBody()?['detalhes_desvios'], 'Desvio apontado no checklist.'), '\"', ''), '\\', '/'), '\r', ' '), '\n', ' | ')"
                        },
                        "runAfter": {}
                    },
                    "Enviar_Aviso_Grupo_Blitz_SSMA_BAERI": {
                        "type": "OpenApiConnection",
                        "inputs": {
                            "host": {
                                "apiId": "/providers/Microsoft.PowerApps/apis/shared_teams",
                                "connectionName": "shared_teams",
                                "operationId": "PostCardToConversation"
                            },
                            "parameters": {
                                "poster": "Flow bot",
                                "location": "Group chat",
                                "body/recipient": f"@coalesce(triggerBody()?['group_chat_id'], '{BAERI_GROUP_CHAT_ID}')",
                                "body/messageBody": card_json_str
                            }
                        },
                        "runAfter": {
                            "Sanitizar_Campos_Livres": ["Succeeded"]
                        }
                    },
                    "Response_Teams_OK": {
                        "type": "Response",
                        "kind": "Http",
                        "inputs": {
                            "statusCode": 200,
                            "headers": {"Content-Type": "application/json; charset=utf-8"},
                            "body": {
                                "ok": True,
                                "group_chat": "Blitz SSMA BAERI",
                                "group_chat_id": f"@{{coalesce(triggerBody()?['group_chat_id'], '{BAERI_GROUP_CHAT_ID}')}}"
                            }
                        },
                        "runAfter": {
                            "Enviar_Aviso_Grupo_Blitz_SSMA_BAERI": ["Succeeded"]
                        }
                    }
                },
                "outputs": {}
            }
        },
        "schemaVersion": "1.0.0.0"
    }

    existing = teams_dv_req("GET", f"workflows?$filter=name eq '{flow_name}' and category eq 5&$select=workflowid,name")
    if existing.get("value"):
        wf_id = existing["value"][0]["workflowid"]
        print(f"Updating existing Teams Alert Flow {flow_name} ({wf_id})...")
        teams_dv_req("PATCH", f"workflows({wf_id})", {"clientdata": json.dumps(clientdata)})
    else:
        print(f"Creating Teams Alert Flow {flow_name}...")
        res = teams_dv_req("POST", "workflows", {
            "name": flow_name,
            "category": 5,
            "type": 1,
            "modernflowtype": 0,
            "primaryentity": "none",
            "clientdata": json.dumps(clientdata)
        }, {"Prefer": "return=representation"})
        wf_id = res["workflowid"]

    teams_dv_req("POST", "PublishXml", {
        "ParameterXml": f"<importexportxml><workflows><workflow>{wf_id}</workflow></workflows></importexportxml>"
    })
    teams_dv_req("PATCH", f"workflows({wf_id})", {"statecode": 1, "statuscode": 2})

    f_headers = {"Authorization": f"Bearer {FLOW_TOKEN}", "Accept": "application/json"}
    flows_res = requests.get(
        f"https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/{TEAMS_ENV_ID}/flows?api-version=2016-11-01",
        headers=f_headers, verify=False, timeout=60
    ).json()
    flow_ps_name = wf_id
    for fl in flows_res.get("value", []):
        if fl.get("properties", {}).get("workflowEntityId", "").lower() == wf_id.lower() or fl.get("properties", {}).get("displayName") == flow_name:
            flow_ps_name = fl["name"]
            break

    cb_resp = requests.post(
        f"https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/{TEAMS_ENV_ID}/flows/{flow_ps_name}/triggers/manual/listCallbackUrl?api-version=2016-11-01",
        headers=f_headers,
        verify=False, timeout=60
    )
    cb_resp.raise_for_status()
    cb_json = cb_resp.json()
    cb_url = (cb_json.get("response") or {}).get("value") or cb_json.get("value")
    print(f"Teams Alert Flow {wf_id} (ps={flow_ps_name}) active! Callback URL resolved.")
    return wf_id, cb_url

def build_api_flow_clientdata(conn_ref_logical, teams_alert_url):
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
    actions["Compor_Resumo_Desvios_Blitz"] = {
        "type": "Compose",
        "inputs": {
            "TemDesvio": "@or(equals(coalesce(triggerBody()?['item01_epis_ok'], true), false), equals(coalesce(triggerBody()?['item02_veiculo_ok'], true), false), equals(coalesce(triggerBody()?['item03_tanque_ok'], true), false), equals(coalesce(triggerBody()?['item04_aterramento_ok'], true), false), equals(coalesce(triggerBody()?['item05_chave_geral_ok'], true), false))",
            "QtdDesvios": "@add(add(add(add(if(equals(coalesce(triggerBody()?['item01_epis_ok'], true), false), 1, 0), if(equals(coalesce(triggerBody()?['item02_veiculo_ok'], true), false), 1, 0)), if(equals(coalesce(triggerBody()?['item03_tanque_ok'], true), false), 1, 0)), if(equals(coalesce(triggerBody()?['item04_aterramento_ok'], true), false), 1, 0)), if(equals(coalesce(triggerBody()?['item05_chave_geral_ok'], true), false), 1, 0))",
            "QtdFotos": "@add(add(add(add(if(not(empty(triggerBody()?['foto_item1_base64'])), 1, 0), if(not(empty(triggerBody()?['foto_item2_base64'])), 1, 0)), if(not(empty(triggerBody()?['foto_item3_base64'])), 1, 0)), if(not(empty(triggerBody()?['foto_item4_base64'])), 1, 0)), if(not(empty(triggerBody()?['foto_item5_base64'])), 1, 0))",
            "DetalhesDesvios": "@concat(if(equals(coalesce(triggerBody()?['item01_epis_ok'], true), false), concat('• ITEM 01 (EPIs): ', coalesce(triggerBody()?['qual_epi_inapropriado'], '-'), ' — Obs: ', coalesce(triggerBody()?['obs_item1'], '-'), ' '), ''), if(equals(coalesce(triggerBody()?['item02_veiculo_ok'], true), false), concat('• ITEM 02 (Veículo/Peças): ', coalesce(triggerBody()?['qual_peca_nao_conforme'], '-'), ' — Obs: ', coalesce(triggerBody()?['obs_item2'], '-'), ' '), ''), if(equals(coalesce(triggerBody()?['item03_tanque_ok'], true), false), concat('• ITEM 03 (Tanque): ', coalesce(triggerBody()?['obs_item3'], '-'), ' '), ''), if(equals(coalesce(triggerBody()?['item04_aterramento_ok'], true), false), concat('• ITEM 04 (Aterramento/Overfill): ', coalesce(triggerBody()?['obs_item4'], '-'), ' '), ''), if(equals(coalesce(triggerBody()?['item05_chave_geral_ok'], true), false), concat('• ITEM 05 (Chave Geral): ', coalesce(triggerBody()?['obs_item5'], '-'), ' '), ''), if(not(empty(triggerBody()?['observacao_geral'])), concat('• Obs Geral: ', triggerBody()?['observacao_geral']), ''))"
        },
        "runAfter": {
            "Cond_Foto_Item5": ["Succeeded", "Skipped", "Failed"]
        }
    }
    actions["Obter_Config_Base_Teams"] = {
        "type": "OpenApiConnection",
        "inputs": {
            "host": {
                "apiId": "/providers/Microsoft.PowerApps/apis/shared_commondataserviceforapps",
                "connectionName": "shared_commondataserviceforapps",
                "operationId": "ListRecords"
            },
            "parameters": {
                "entityName": "opsul_bases",
                "$filter": "opsul_sigla eq '@{coalesce(triggerBody()?['base'], '')}' and opsul_alerta_teams_ativo eq true",
                "$top": 1
            }
        },
        "runAfter": {
            "Compor_Resumo_Desvios_Blitz": ["Succeeded"]
        }
    }
    actions["Cond_Notificar_Desvio_BAERI_Teams"] = {
        "type": "If",
        "expression": {
            "and": [
                {
                    "greater": [
                        "@length(coalesce(outputs('Obter_Config_Base_Teams')?['body/value'], json('[]')))",
                        0
                    ]
                },
                {
                    "equals": [
                        "@outputs('Compor_Resumo_Desvios_Blitz')?['TemDesvio']",
                        True
                    ]
                }
            ]
        },
        "actions": {
            "Disparar_Aviso_Teams_BAERI": {
                "type": "Http",
                "inputs": {
                    "method": "POST",
                    "uri": teams_alert_url,
                    "headers": {"Content-Type": "application/json; charset=utf-8"},
                    "body": {
                        "group_chat_id": f"@coalesce(first(outputs('Obter_Config_Base_Teams')?['body/value'])?['opsul_destinatarios_teams'], '{BAERI_GROUP_CHAT_ID}')",
                        "protocolo": "@outputs('Compose_Protocolo')",
                        "data": "@coalesce(triggerBody()?['data'], formatDateTime(utcNow(), 'yyyy-MM-dd'))",
                        "base": "@coalesce(triggerBody()?['base'], 'BAERI')",
                        "placa_ct": "@coalesce(triggerBody()?['placa_ct'], '-')",
                        "cif_fob": "@coalesce(triggerBody()?['cif_fob'], '-')",
                        "transportadora": "@coalesce(triggerBody()?['transportadora'], '-')",
                        "responsavel_nome": "@coalesce(triggerBody()?['responsavel_nome'], 'Não Informado')",
                        "responsavel_email": "@coalesce(triggerBody()?['responsavel_email'], '-')",
                        "qtd_desvios": "@outputs('Compor_Resumo_Desvios_Blitz')?['QtdDesvios']",
                        "qtd_fotos": "@outputs('Compor_Resumo_Desvios_Blitz')?['QtdFotos']",
                        "detalhes_desvios": "@outputs('Compor_Resumo_Desvios_Blitz')?['DetalhesDesvios']"
                    }
                },
                "runAfter": {}
            }
        },
        "else": {
            "actions": {}
        },
        "runAfter": {
            "Obter_Config_Base_Teams": ["Succeeded", "Failed"]
        }
    }
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
                "notificado_teams": "@and(greater(length(coalesce(outputs('Obter_Config_Base_Teams')?['body/value'], json('[]'))), 0), equals(outputs('Compor_Resumo_Desvios_Blitz')?['TemDesvio'], true))",
                "solution": "OPER_OPSUL"
            }
        },
        "runAfter": {
            "Cond_Notificar_Desvio_BAERI_Teams": ["Succeeded", "Skipped", "Failed"]
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
    teams_wf_id, teams_alert_url = ensure_teams_alert_flow()

    # 1. Update API Flow in Dataverse
    print(f"Updating API Flow {API_FLOW_ID}...")
    api_clientdata = build_api_flow_clientdata(conn_ref_logical, teams_alert_url)
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
    for wf_id, slug, req_fn in [
        (PORTAL_FLOW_ID, "oper_opsul_portal_web_blitz_de_sms", dv_req),
        (API_FLOW_ID, "oper_opsul_api_blitz_de_sms", dv_req),
        (teams_wf_id, "oper_opsul_alerta_desvio_blitz_teams_baeri", teams_dv_req)
    ]:
        wf_data = req_fn("GET", f"workflows({wf_id})?$select=workflowid,name,statecode,statuscode,clientdata,modifiedon,createdon")
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
