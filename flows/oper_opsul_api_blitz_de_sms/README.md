# ⚙️ Fluxo: `OPER_OPSUL - API Blitz de SMS`

- **Workflow ID (Dataverse):** `592191f7-47d9-f111-84e8-e4fade0322c2`
- **Solução:** `OPER_OPSUL` (`e11a7dcc-45d9-f111-84e8-e4fade0322c2`)
- **Ambiente:** `Cristian Ferreira Carlos` (`4a9ba077-4920-ea16-ae45-293f56eb85e3`)
- **Estado:** `Ativo (Started)` (`statecode: 1, statuscode: 2`)
- **Autenticação do Trigger:** `All` (invocado pelo Web Resource autenticado via SSO Vibra)

## Descrição
Fluxo HTTP POST que recebe as submissões do formulário Blitz de SMS, cria o registro na tabela `opsul_blitzsms` (`CreateRecord`), grava as fotos opcionais de não conformidade (`opsul_foto_item1` a `opsul_foto_item5`) como binário nativo no Dataverse (`UpdateEntityFileImageFieldContent`), consulta a parametrização da base em `opsul_bases` (`opsul_alerta_teams_ativo eq true`) e, quando houver **1 ou mais desvios no checklist**, aciona o fluxo de aviso no Microsoft Teams (`OPER_OPSUL - Alerta de Desvio Blitz de SMS no Teams (BAERI)` -> grupo **`Blitz SSMA BAERI`**), retornando o protocolo único, `blitz_id` e flag `notificado_teams` via JSON com suporte a CORS.

## Fluxograma WDL
```mermaid
flowchart TD
    TRIG(["⚡ Trigger HTTP Request: manual"])
    PROTO["⚙️ Compose_Protocolo"]
    CREATE["🗄️ Criar_Registro_Blitz_Dataverse (CreateRecord -> opsul_blitzsmses)"]
    FOTO["📷 Cond_Foto_Item1..5 -> Upload_Foto_Item1..5 (UpdateEntityFileImageFieldContent)"]
    RESUMO["📋 Compor_Resumo_Desvios_Blitz (TemDesvio, QtdDesvios, QtdFotos, DetalhesDesvios)"]
    CFG_BASE["🔎 Obter_Config_Base_Teams (ListRecords -> opsul_bases)"]
    COND_TEAMS{"🚨 Base com Alerta Ativo (BAERI) E TemDesvio == true?"}
    POST_TEAMS["📢 Disparar_Aviso_Teams_BAERI (HTTP POST -> Grupo Blitz SSMA BAERI)"]
    ACT["✅ Response_OK (HTTP 200 JSON + CORS)"]
    TRIG --> PROTO --> CREATE --> FOTO --> RESUMO --> CFG_BASE --> COND_TEAMS
    COND_TEAMS -->|"Sim"| POST_TEAMS --> ACT
    COND_TEAMS -->|"Não"| ACT
```

## Arquivos neste Diretório
- [`definition.wdl.json`](./definition.wdl.json) — Definição lógica WDL (`triggers` + `actions`)
- [`connection_references.json`](./connection_references.json) — Referências de conexão
- [`flow_full.json`](./flow_full.json) — Snapshot completo da entidade `workflow` no Dataverse
