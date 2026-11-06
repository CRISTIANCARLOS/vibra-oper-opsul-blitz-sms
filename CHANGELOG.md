# Changelog — `vibra-oper-opsul-blitz-sms`

## [v1.3.0] — 2026-11-06
### Alterado
- **Exigência de Login Corporativo no Ambiente Vibra (Microsoft Entra ID / Dataverse SSO):**
  - O aplicativo [`webresources/opsul_blitz_sms_app.html`](./webresources/opsul_blitz_sms_app.html) agora exige sessão corporativa ativa no ambiente Vibra (`https://orgd15f46d4.crm2.dynamics.com/WebResources/opsul_blitz_sms_app.html`), validando a identidade via `/api/data/v9.2/WhoAmI` e `/api/data/v9.2/systemusers` antes de desbloquear o formulário (`#authGateOverlay`).
  - O fluxo [`OPER_OPSUL - Portal Web Blitz de SMS`](./flows/oper_opsul_portal_web_blitz_de_sms/definition.wdl.json) (`8bfaac34-48d9-f111-84e8-e4fade0322c2`) deixou de servir o HTML sem login e agora responde com `HTTP 302 Found` redirecionando para `https://orgd15f46d4.crm2.dynamics.com/WebResources/opsul_blitz_sms_app.html` (forçando o login Microsoft Entra ID `@vibraenergia.com.br` quando o usuário não estiver autenticado).
  - Preenchimento e envio automático do e-mail do usuário autenticado (`responsavel_email` -> `opsul_responsavel_email`) na gravação da Blitz de SMS.

## [v1.2.0] — 2026-11-06
### Removido
- **Remoção da Decisão de Bloqueio (`opsul_motorista_bloqueado`):**
  - Remoção do bloco visual `"Decisão Crítica: Motorista / CT Bloqueado?"` (`#decisionBar`, `#inpBloqueado`, `selectBloqueado()`, `updateDecisionRecommendation()`) da Seção 03 do Portal Web [`webresources/opsul_blitz_sms_app.html`](./webresources/opsul_blitz_sms_app.html), que agora foca em **Observações Gerais e Fechamento da Blitz**.
  - Remoção da propriedade `motorista_bloqueado` / `item/opsul_motorista_bloqueado` no trigger, na ação `Criar_Registro_Blitz_Dataverse` e no `Response_OK` do fluxo [`OPER_OPSUL - API Blitz de SMS (Sem Login)`](./flows/oper_opsul_api_blitz_de_sms/definition.wdl.json) (`592191f7-47d9-f111-84e8-e4fade0322c2`).
  - Exclusão permanente da coluna `opsul_motorista_bloqueado` na tabela `opsul_blitzsms` no Microsoft Dataverse (`DELETE EntityDefinitions(LogicalName='opsul_blitzsms')/Attributes(LogicalName='opsul_motorista_bloqueado')`).

## [v1.1.0] — 2026-11-06
### Adicionado
- **Evidência Fotográfica Opcional nas Não Conformidades (Itens 01 a 05):**
  - Provisionamento de **5 colunas nativas de imagem (`Microsoft.Dynamics.CRM.ImageAttributeMetadata`)** na tabela `opsul_blitzsms` (`opsul_foto_item1` a `opsul_foto_item5`) com `CanStoreFullImage: true` e `MaxSizeInKB: 10240` (armazenamento binário no Azure Blob Storage gerenciado pelo Dataverse sem consumir limites de texto da tabela).
  - Componente de captura/upload opcional (`<input type="file" accept="image/*" capture="environment">`) dentro das gavetas de não conformidade dos 5 itens no formulário [`webresources/opsul_blitz_sms_app.html`](./webresources/opsul_blitz_sms_app.html), com redimensionamento e compressão em navegador via `<canvas>` (JPEG máx. `1280px`, ~120–250 KB) e miniatura instantânea.
  - Evolução do fluxo [`OPER_OPSUL - API Blitz de SMS (Sem Login)`](./flows/oper_opsul_api_blitz_de_sms/definition.wdl.json) (`592191f7-47d9-f111-84e8-e4fade0322c2`) com criação do registro via `CreateRecord` e upload binário das fotos em duas etapas via `UpdateEntityFileImageFieldContent` (`@base64ToBinary`).

## [v1.0.0] — 2026-11-05
### Adicionado
- Criação da solução relacional **`OPER_OPSUL`** (`e11a7dcc-45d9-f111-84e8-e4fade0322c2`) e do Publisher **`OPER_OPSUL Vibra Energia`** (`opsul_`) no ambiente **Cristian Ferreira Carlos** (`https://orgd15f46d4.crm2.dynamics.com`).
- Criação e publicação das **4 tabelas relacionais** no Dataverse:
  1. `opsul_base` (`opsul_bases`) — Catálogo com **204 Bases Operacionais** únicas classificadas por prefixo (`BA`, `RA`, `AR`, `AI`, `DE`, `BE`, `SEDE`, `GEI`, `CCPP`, `EPS`).
  2. `opsul_responsavel` (`opsul_responsavels`) — Catálogo com **372 Responsáveis pela Blitz** normalizados a partir da base histórica.
  3. `opsul_usuarioregional` (`opsul_usuarioregionals`) — Tabela dedicada aos gestores do Regional preparados para login SSO futuro (`wedson@vibraenergia.com.br` e `anasales@vibraenergia.com.br`).
  4. `opsul_blitzsms` (`opsul_blitzsmses`) — Tabela fato principal de inspeções **Blitz de SMS** com 26 colunas e relacionamentos `1:N` (`opsul_baseid` e `opsul_responsavelid`), populada com **3.761 registros históricos** migrados da lista SharePoint original.
- Desenvolvimento e publicação do **Portal e Formulário Web Sem Login** (`webresources/opsul_blitz_sms_app.html`) seguindo estritamente o Design System Oficial da Vibra Energia (`#004415`, `#268200`, `#FEDC00`, `#0000FF`), com:
  - Busca **Fuzzy** tolerante a erros de digitação, acentuação e subsequência nas 204 bases;
  - Memória inteligente de Responsável (*escreve o nome uma única vez e depois escolhe na lista*);
  - Validação obrigatória dos 5 itens críticos de SMS e decisão de bloqueio do motorista/CT.
- Provisionamento e ativação dos **2 Solution Flows anônimos (`triggerAuthenticationType: "All"`)**:
  - `OPER_OPSUL - Portal Web Blitz de SMS (Sem Login)` (`8bfaac34-48d9-f111-84e8-e4fade0322c2`)
  - `OPER_OPSUL - API Blitz de SMS (Sem Login)` (`592191f7-47d9-f111-84e8-e4fade0322c2`)
