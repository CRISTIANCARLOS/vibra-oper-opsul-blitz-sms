# ⚙️ Fluxo: `OPER_OPSUL - Portal Web Blitz de SMS (Sem Login)`

- **Workflow ID (Dataverse):** `8bfaac34-48d9-f111-84e8-e4fade0322c2`
- **Solução:** `OPER_OPSUL` (`e11a7dcc-45d9-f111-84e8-e4fade0322c2`)
- **Ambiente:** `Cristian Ferreira Carlos` (`4a9ba077-4920-ea16-ae45-293f56eb85e3`)
- **Estado:** `Ativo (Started)` (`statecode: 1, statuscode: 2`)
- **Autenticação do Trigger:** `All` (**Acesso Anônimo / Sem Login**)

## Descrição
Fluxo HTTP GET anônimo (triggerAuthenticationType=All) que entrega o aplicativo completo Blitz de SMS sem exigir login.

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
