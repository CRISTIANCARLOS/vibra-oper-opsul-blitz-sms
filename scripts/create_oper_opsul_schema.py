import json
import subprocess
import urllib.request
import urllib.error
import ssl
import sys

ORG_URL = "https://orgd15f46d4.crm2.dynamics.com"
API_URL = f"{ORG_URL}/api/data/v9.2"
LANG_CODE = 1046

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

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

TOKEN = get_token(ORG_URL + "/")

def dv_request(method, path, body=None, extra_headers=None):
    url = (f"{API_URL}/{path}" if not path.startswith("http") else path).replace(" ", "%20")
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0"
    }
    if extra_headers:
        headers.update(extra_headers)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=180) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {"status": resp.status, "headers": dict(resp.headers)}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code} on {method} {path}: {err_body}")
        raise

def label(text):
    return {
        "@odata.type": "Microsoft.Dynamics.CRM.Label",
        "LocalizedLabels": [
            {
                "@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                "Label": text,
                "LanguageCode": LANG_CODE
            }
        ]
    }

def str_attr(schema_name, display_name, max_len=150, req_level="None", desc=""):
    return {
        "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata",
        "SchemaName": schema_name,
        "RequiredLevel": {"Value": req_level, "CanBeChanged": True},
        "MaxLength": max_len,
        "FormatName": {"Value": "Text"},
        "DisplayName": label(display_name),
        "Description": label(desc or display_name)
    }

def memo_attr(schema_name, display_name, max_len=2000, req_level="None", desc=""):
    return {
        "@odata.type": "Microsoft.Dynamics.CRM.MemoAttributeMetadata",
        "SchemaName": schema_name,
        "RequiredLevel": {"Value": req_level, "CanBeChanged": True},
        "MaxLength": max_len,
        "Format": "TextArea",
        "DisplayName": label(display_name),
        "Description": label(desc or display_name)
    }

def int_attr(schema_name, display_name, req_level="None", desc=""):
    return {
        "@odata.type": "Microsoft.Dynamics.CRM.IntegerAttributeMetadata",
        "SchemaName": schema_name,
        "RequiredLevel": {"Value": req_level, "CanBeChanged": True},
        "Format": "None",
        "MinValue": -2147483648,
        "MaxValue": 2147483647,
        "DisplayName": label(display_name),
        "Description": label(desc or display_name)
    }

def bool_attr(schema_name, display_name, default_val=True, req_level="None", desc=""):
    return {
        "@odata.type": "Microsoft.Dynamics.CRM.BooleanAttributeMetadata",
        "SchemaName": schema_name,
        "RequiredLevel": {"Value": req_level, "CanBeChanged": True},
        "DefaultValue": default_val,
        "DisplayName": label(display_name),
        "Description": label(desc or display_name),
        "OptionSet": {
            "@odata.type": "Microsoft.Dynamics.CRM.BooleanOptionSetMetadata",
            "TrueOption": {"Value": 1, "Label": label("Sim")},
            "FalseOption": {"Value": 0, "Label": label("Não")}
        }
    }

def date_attr(schema_name, display_name, date_only=True, req_level="None", desc=""):
    return {
        "@odata.type": "Microsoft.Dynamics.CRM.DateTimeAttributeMetadata",
        "SchemaName": schema_name,
        "RequiredLevel": {"Value": req_level, "CanBeChanged": True},
        "Format": "DateOnly" if date_only else "DateAndTime",
        "DateTimeBehavior": {"Value": "DateOnly" if date_only else "UserLocal"},
        "DisplayName": label(display_name),
        "Description": label(desc or display_name)
    }

def img_attr(schema_name, display_name, is_primary=False, max_kb=10240, desc=""):
    return {
        "@odata.type": "Microsoft.Dynamics.CRM.ImageAttributeMetadata",
        "AttributeTypeName": {"Value": "ImageType"},
        "SchemaName": schema_name,
        "IsPrimaryImage": is_primary,
        "CanStoreFullImage": True,
        "MaxSizeInKB": max_kb,
        "DisplayName": label(display_name),
        "Description": label(desc or display_name)
    }

def ensure_publisher():
    res = dv_request("GET", "publishers?$filter=uniquename eq 'oper_opsul_publisher'&$select=publisherid,uniquename")
    if res.get("value"):
        pub_id = res["value"][0]["publisherid"]
        print(f"Publisher already exists: {pub_id}")
        return pub_id
    body = {
        "uniquename": "oper_opsul_publisher",
        "friendlyname": "OPER_OPSUL Vibra Energia",
        "description": "Publisher oficial da solução relacional OPER_OPSUL (Blitz de SMS e Governança Regional)",
        "customizationprefix": "opsul",
        "customizationoptionvalueprefix": 75200
    }
    dv_request("POST", "publishers", body)
    res = dv_request("GET", "publishers?$filter=uniquename eq 'oper_opsul_publisher'&$select=publisherid")
    pub_id = res["value"][0]["publisherid"]
    print(f"Created Publisher: {pub_id}")
    return pub_id

def ensure_solution(pub_id):
    res = dv_request("GET", "solutions?$filter=uniquename eq 'OPER_OPSUL'&$select=solutionid,uniquename")
    if res.get("value"):
        sol_id = res["value"][0]["solutionid"]
        print(f"Solution OPER_OPSUL already exists: {sol_id}")
        return sol_id
    body = {
        "uniquename": "OPER_OPSUL",
        "friendlyname": "OPER_OPSUL",
        "description": "Solução de Banco Relacional OPER_OPSUL - Blitz de SMS e Governança Regional (SSO)",
        "version": "1.0.0.0",
        "publisherid@odata.bind": f"/publishers({pub_id})"
    }
    dv_request("POST", "solutions", body)
    res = dv_request("GET", "solutions?$filter=uniquename eq 'OPER_OPSUL'&$select=solutionid")
    sol_id = res["value"][0]["solutionid"]
    print(f"Created Solution OPER_OPSUL: {sol_id}")
    return sol_id

def ensure_entity(schema_name, display_name, plural_name, desc, primary_attr_schema, primary_attr_display, primary_max_len, extra_attrs):
    logical_name = schema_name.lower()
    res = dv_request("GET", f"EntityDefinitions?$select=LogicalName,MetadataId&$filter=LogicalName eq '{logical_name}'")
    sol_headers = {"MSCRM.SolutionUniqueName": "OPER_OPSUL"}
    if not res.get("value"):
        primary_attr = str_attr(primary_attr_schema, primary_attr_display, primary_max_len, "ApplicationRequired")
        primary_attr["IsPrimaryName"] = True
        entity_def = {
            "@odata.type": "Microsoft.Dynamics.CRM.EntityMetadata",
            "SchemaName": schema_name,
            "DisplayName": label(display_name),
            "DisplayCollectionName": label(plural_name),
            "Description": label(desc),
            "OwnershipType": "UserOwned",
            "IsActivity": False,
            "HasNotes": False,
            "HasActivities": False,
            "PrimaryNameAttribute": primary_attr_schema.lower(),
            "Attributes": [primary_attr] + extra_attrs
        }
        print(f"Creating entity {schema_name} with {len(extra_attrs)+1} attributes...")
        dv_request("POST", "EntityDefinitions", entity_def, sol_headers)
        print(f"Created entity {schema_name}!")
    else:
        print(f"Entity {schema_name} already exists, checking missing attributes...")
        existing = dv_request("GET", f"EntityDefinitions(LogicalName='{logical_name}')/Attributes?$select=LogicalName")
        existing_names = {a["LogicalName"] for a in existing.get("value", [])}
        for attr in extra_attrs:
            if attr["SchemaName"].lower() not in existing_names:
                print(f"  Adding attribute {attr['SchemaName']} to {schema_name}...")
                dv_request("POST", f"EntityDefinitions(LogicalName='{logical_name}')/Attributes", attr, sol_headers)

def drop_attribute_if_exists(entity_logical_name, attr_logical_name):
    existing = dv_request("GET", f"EntityDefinitions(LogicalName='{entity_logical_name}')/Attributes?$select=LogicalName")
    existing_names = {a["LogicalName"] for a in existing.get("value", [])}
    if attr_logical_name.lower() in existing_names:
        print(f"  Dropping attribute {attr_logical_name} from {entity_logical_name}...")
        dv_request("DELETE", f"EntityDefinitions(LogicalName='{entity_logical_name}')/Attributes(LogicalName='{attr_logical_name.lower()}')")
        print(f"  Dropped attribute {attr_logical_name} from {entity_logical_name}!")
    else:
        print(f"  Attribute {attr_logical_name} already absent on {entity_logical_name}.")

def ensure_lookup(schema_name_rel, referenced_entity, referencing_entity, lookup_schema_name, lookup_display_name):
    res = dv_request("GET", f"EntityDefinitions(LogicalName='{referencing_entity}')/Attributes?$select=LogicalName")
    existing_names = {a["LogicalName"] for a in res.get("value", [])}
    if lookup_schema_name.lower() in existing_names:
        print(f"Lookup {lookup_schema_name} already exists on {referencing_entity}.")
        return
    sol_headers = {"MSCRM.SolutionUniqueName": "OPER_OPSUL"}
    rel_def = {
        "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata",
        "SchemaName": schema_name_rel,
        "ReferencedEntity": referenced_entity,
        "ReferencingEntity": referencing_entity,
        "CascadeConfiguration": {
            "Assign": "NoCascade",
            "Delete": "RemoveLink",
            "Merge": "NoCascade",
            "Reparent": "NoCascade",
            "Share": "NoCascade",
            "Unshare": "NoCascade"
        },
        "Lookup": {
            "@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata",
            "SchemaName": lookup_schema_name,
            "DisplayName": label(lookup_display_name),
            "RequiredLevel": {"Value": "None", "CanBeChanged": True},
            "Description": label(f"Relacionamento com {lookup_display_name}")
        }
    }
    print(f"Creating 1:N Relationship {schema_name_rel} ({referenced_entity} -> {referencing_entity})...")
    dv_request("POST", "RelationshipDefinitions", rel_def, sol_headers)
    print(f"Created Relationship {schema_name_rel}!")

def main():
    pub_id = ensure_publisher()
    sol_id = ensure_solution(pub_id)

    # 1. Tabela opsul_base (Catálogo de Bases Operacionais)
    ensure_entity(
        schema_name="opsul_base",
        display_name="Base Operacional OPSUL",
        plural_name="Bases Operacionais OPSUL",
        desc="Catálogo relacional de Bases Operacionais (AI, AR, BA, BE, DE, RA, SEDE, GEI, CCPP, EPS)",
        primary_attr_schema="opsul_sigla",
        primary_attr_display="Sigla da Base",
        primary_max_len=50,
        extra_attrs=[
            str_attr("opsul_categoria", "Categoria da Base", 50, "None", "Tipo/Prefixo da Base (BA, RA, AR, AI, DE, BE, etc.)"),
            str_attr("opsul_descricao", "Descrição", 150, "None", "Descrição da Base Operacional"),
            bool_attr("opsul_ativo", "Ativo", True, "None", "Base ativa para seleção no formulário")
        ]
    )

    # 2. Tabela opsul_responsavel (Catálogo de Responsáveis pela Blitz)
    ensure_entity(
        schema_name="opsul_responsavel",
        display_name="Responsável pela Blitz",
        plural_name="Responsáveis pela Blitz",
        desc="Tabela relacional de pessoas responsáveis pela Blitz de SMS (escreve 1x e depois escolhe na lista)",
        primary_attr_schema="opsul_nome",
        primary_attr_display="Nome do Responsável",
        primary_max_len=150,
        extra_attrs=[
            str_attr("opsul_email", "E-mail", 150, "None", "E-mail do responsável quando identificado"),
            str_attr("opsul_base_padrao", "Base Padrão", 50, "None", "Última base utilizada pelo responsável"),
            int_attr("opsul_total_blitz", "Total de Blitz Realizadas", "None", "Quantidade total de inspeções registradas"),
            bool_attr("opsul_ativo", "Ativo", True, "None", "Responsável ativo na lista de seleção")
        ]
    )

    # 3. Tabela opsul_usuarioregional (Pessoas do Regional - Login SSO em outra solução)
    ensure_entity(
        schema_name="opsul_usuarioregional",
        display_name="Usuário Regional OPSUL",
        plural_name="Usuários Regionais OPSUL",
        desc="Tabela relacional de usuários da Regional OPSUL habilitados para login via SSO corporativo em solução dedicada",
        primary_attr_schema="opsul_nome",
        primary_attr_display="Nome Completo",
        primary_max_len=150,
        extra_attrs=[
            str_attr("opsul_email", "E-mail Corporativo (UPN)", 150, "ApplicationRequired", "E-mail para autenticação SSO"),
            str_attr("opsul_entra_oid", "Entra Object ID", 100, "None", "Object ID do usuário no Microsoft Entra ID"),
            str_attr("opsul_departamento", "Departamento", 150, "None", "Departamento no Entra ID"),
            str_attr("opsul_cargo", "Cargo", 100, "None", "Cargo no Entra ID"),
            str_attr("opsul_perfil", "Perfil de Acesso", 100, "None", "Perfil na solução Regional"),
            str_attr("opsul_regional", "Regional", 100, "None", "Regional de atuação"),
            bool_attr("opsul_sso_habilitado", "SSO Habilitado", True, "None", "Habilitado para login SSO na solução Regional"),
            bool_attr("opsul_ativo", "Ativo", True, "None", "Status ativo do usuário regional")
        ]
    )

    # 4. Tabela Fato Principal: opsul_blitzsms (Blitz de SMS)
    ensure_entity(
        schema_name="opsul_blitzsms",
        display_name="Blitz de SMS",
        plural_name="Blitz de SMS",
        desc="Tabela relacional principal de inspeções Blitz de SMS (migrada e sincronizada com a lista Blitz de SMS)",
        primary_attr_schema="opsul_titulo",
        primary_attr_display="Título / Identificador",
        primary_max_len=255,
        extra_attrs=[
            int_attr("opsul_sp_id", "ID SharePoint", "None", "ID original do registro na lista SharePoint Blitz de SMS"),
            date_attr("opsul_data", "Data da Blitz", True, "ApplicationRequired", "Data de realização da Blitz"),
            str_attr("opsul_base", "Base", 50, "ApplicationRequired", "Sigla da Base Operacional"),
            str_attr("opsul_responsavel_nome", "Nome do Responsável pela Blitz", 150, "ApplicationRequired", "Nome do responsável pela inspeção"),
            str_attr("opsul_responsavel_email", "E-mail do Responsável", 150, "None", "E-mail do responsável pela Blitz"),
            str_attr("opsul_transportadora", "Transportadora", 255, "None", "Nome da transportadora inspecionada"),
            str_attr("opsul_placa_ct", "Placa do CT", 50, "None", "Placa do caminhão-tanque (CT)"),
            str_attr("opsul_cif_fob", "CIF ou FOB", 20, "None", "Modalidade do frete (CIF ou FOB)"),
            bool_attr("opsul_item01_epis_ok", "ITEM 01 - EPIs Apropriados e Higienizados?", True, "ApplicationRequired", "Os EPIs são apropriados para a atividade, apresentam boas condições e aparentam higienizados?"),
            str_attr("opsul_qual_epi_inapropriado", "Qual EPI não está apropriado?", 500, "None", "Lista de EPIs não conformes identificados no Item 01"),
            memo_attr("opsul_obs_item1", "ObsItem1", 2000, "None", "Observações detalhadas do Item 01 (EPIs)"),
            bool_attr("opsul_item02_veiculo_ok", "ITEM 02 - Veículo Íntegro e sem Peças Quebradas?", True, "ApplicationRequired", "Veículo está íntegro em sua estrutura e sem peças quebradas (fiação elétrica, pneus, vidros, lanternas e faróis)?"),
            str_attr("opsul_qual_peca_nao_conforme", "Qual peça não está conforme?", 500, "None", "Lista de peças não conformes identificadas no Item 02"),
            memo_attr("opsul_obs_item2", "ObsItem2", 2000, "None", "Observações detalhadas do Item 02 (Estrutura/Peças)"),
            bool_attr("opsul_item03_tanque_ok", "ITEM 03 - Tanque em Boas Condições Operacionais?", True, "ApplicationRequired", "O Tanque do veículo está em boas condições operacionais?"),
            memo_attr("opsul_obs_item3", "ObsItem3", 2000, "None", "Observações detalhadas do Item 03 (Tanque)"),
            bool_attr("opsul_item04_aterramento_ok", "ITEM 04 - Aterramento e Sensor Overfill Operacionais?", True, "ApplicationRequired", "Condições dos sistemas de aterramento/sensor overfill, soldas, apoio e degraus antiderrapantes estão operacionais?"),
            memo_attr("opsul_obs_item4", "ObsItem4", 2000, "None", "Observações detalhadas do Item 04 (Aterramento/Overfill)"),
            bool_attr("opsul_item05_chave_geral_ok", "ITEM 05 - Chave Geral do CT Operacional e Identificada?", True, "ApplicationRequired", "Chave geral do CT está desempenhando sua função e possui identificação liga/desliga?"),
            memo_attr("opsul_obs_item5", "ObsItem5", 2000, "None", "Observações detalhadas do Item 05 (Chave Geral)"),
            memo_attr("opsul_observacao_geral", "Observação Geral", 4000, "None", "Observações gerais da Blitz de SMS"),
            date_attr("opsul_sp_created", "Criado em (SharePoint)", False, "None", "Data/hora original de criação no SharePoint"),
            date_attr("opsul_sp_modified", "Modificado em (SharePoint)", False, "None", "Data/hora original de modificação no SharePoint"),
            str_attr("opsul_sp_author", "Criado por (SharePoint)", 150, "None", "Autor original do registro no SharePoint"),
            img_attr("opsul_foto_item1", "Foto Evidência Item 01 (EPIs)", True, 10240, "Evidência fotográfica de não conformidade no Item 01 (EPIs)"),
            img_attr("opsul_foto_item2", "Foto Evidência Item 02 (Veículo/Peças)", False, 10240, "Evidência fotográfica de não conformidade no Item 02 (Estrutura e Peças)"),
            img_attr("opsul_foto_item3", "Foto Evidência Item 03 (Tanque)", False, 10240, "Evidência fotográfica de não conformidade no Item 03 (Tanque)"),
            img_attr("opsul_foto_item4", "Foto Evidência Item 04 (Aterramento/Overfill)", False, 10240, "Evidência fotográfica de não conformidade no Item 04 (Aterramento, Overfill e Acesso)"),
            img_attr("opsul_foto_item5", "Foto Evidência Item 05 (Chave Geral)", False, 10240, "Evidência fotográfica de não conformidade no Item 05 (Chave Geral do CT)")
        ]
    )

    # Remover coluna descontinuada opsul_motorista_bloqueado se ainda existir no Dataverse
    drop_attribute_if_exists("opsul_blitzsms", "opsul_motorista_bloqueado")

    # 5. Relacionamentos 1:N (Lookups relacionais)
    ensure_lookup(
        schema_name_rel="opsul_base_opsul_blitzsms",
        referenced_entity="opsul_base",
        referencing_entity="opsul_blitzsms",
        lookup_schema_name="opsul_baseid",
        lookup_display_name="Base Relacional"
    )
    ensure_lookup(
        schema_name_rel="opsul_responsavel_opsul_blitzsms",
        referenced_entity="opsul_responsavel",
        referencing_entity="opsul_blitzsms",
        lookup_schema_name="opsul_responsavelid",
        lookup_display_name="Responsável Relacional"
    )

    print("Publishing customizations via PublishAllXml...")
    dv_request("POST", "PublishAllXml", {})
    print("ALL DONE! OPER_OPSUL schema created and published successfully!")

if __name__ == "__main__":
    main()
