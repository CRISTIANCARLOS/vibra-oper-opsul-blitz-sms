"""Script utilitário para exportar as definições atualizadas dos fluxos e WebResource da solução OPER_OPSUL."""
import json
import ssl
import subprocess
import urllib.request

AZ_WRAPPER = r"C:\Users\CE9X\.agents\skills\azure-cli-netskope\scripts\invoke-az-netskope.ps1"
ORG_URL = "https://orgd15f46d4.crm2.dynamics.com"
WORKFLOW_IDS = [
    "8bfaac34-48d9-f111-84e8-e4fade0322c2",
    "592191f7-47d9-f111-84e8-e4fade0322c2"
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get_token(resource: str) -> str:
    cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", AZ_WRAPPER,
           "account", "get-access-token", "--resource", resource, "--query", "accessToken", "-o", "tsv"]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()

if __name__ == "__main__":
    token = get_token(ORG_URL + "/")
    for wf_id in WORKFLOW_IDS:
        url = f"{ORG_URL}/api/data/v9.2/workflows({wf_id})?$select=workflowid,name,statecode,modifiedon"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"  [OK] Workflow: {data.get('name')} ({wf_id}) - modificado em {data.get('modifiedon')}")
