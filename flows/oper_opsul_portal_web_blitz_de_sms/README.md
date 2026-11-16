# ⚙️ Fluxo: `OPER_OPSUL - Portal Web Blitz de SMS (Com Login)`

- **Workflow ID (Dataverse):** `8bfaac34-48d9-f111-84e8-e4fade0322c2`
- **Flow ID (Power Automate):** `38abac2b-332e-58e2-31ea-7e092597d2d7`
- **Solução:** `OPER_OPSUL` (`e11a7dcc-45d9-f111-84e8-e4fade0322c2`)
- **Ambiente:** `Cristian Ferreira Carlos` (`4a9ba077-4920-ea16-ae45-293f56eb85e3`)
- **Estado:** `Ativo (Started)` (`statecode: 1, statuscode: 2`)
- **Destino SSO:** `https://org3359db9c.crm.dynamics.com/WebResources/opsul_blitz_sms_app.html`

## Descrição
Fluxo HTTP GET que intercepta acessos ao link do Portal e redireciona automaticamente (`window.location.replace` + `meta http-equiv="refresh"`) para o Web Resource autenticado no ambiente `Petrobras Distribuidora S/A (default)` (`https://org3359db9c.crm.dynamics.com/WebResources/opsul_blitz_sms_app.html`), exigindo login corporativo Vibra Energia (`@vibraenergia.com.br` via Microsoft Entra ID SSO).

## Fluxograma WDL
```mermaid
flowchart TD
    TRIG(["⚡ Trigger HTTP Request: manual (Anonymous / All)"])
    ACT["⚙️ Processamento & Response HTTP 200"]
    TRIG --> ACT
```

## Arquivos neste Diretório
- [`definition.wdl.json`](./definition.wdl.json) — Definição lógica WDL (`triggers` + `actions`)
- [`connection_references.json`](./connection_references.json) — Referências de conexão
- [`flow_full.json`](./flow_full.json) — Snapshot completo da entidade `workflow` no Dataverse
