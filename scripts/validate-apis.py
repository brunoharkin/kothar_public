import re
import urllib.request
import urllib.error
import concurrent.futures
from pathlib import Path

# Configurações
REPO_URL = "https://raw.githubusercontent.com/public-apis/public-apis/master/README.md"
OUTPUT_DIR = Path("/home/bruno/kothar/scratch/public-apis")
OUTPUT_FILE = OUTPUT_DIR / "VALIDATED_APIS.md"
TIMEOUT = 5

def fetch_readme():
    print(f"📥 Baixando repositório original de {REPO_URL}...")
    req = urllib.request.Request(REPO_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8')

def extract_apis(markdown_content):
    apis = []
    # Busca todas as linhas da tabela Markdown. Exemplo: | [Cat Facts](https://alexwohlbruck.github.io/cat-facts/) | Daily cat facts | No | Yes | No |
    pattern = re.compile(r'\|\s*\[(.*?)\]\((.*?)\)\s*\|\s*(.*?)\s*\|')
    
    for line in markdown_content.splitlines():
        if line.strip().startswith('|') and 'http' in line:
            match = pattern.search(line)
            if match:
                name, url, desc = match.groups()
                # Remove Markdown da descrição, se houver
                desc = re.sub(r'\[.*?\]\(.*?\)', '', desc).strip()
                apis.append({'name': name.strip(), 'url': url.strip(), 'desc': desc})
    return apis

def validate_api(api):
    try:
        req = urllib.request.Request(api['url'], headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            if response.getcode() == 200:
                return api
    except Exception:
        pass
    return None

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    md_content = fetch_readme()
    apis = extract_apis(md_content)
    print(f"🔍 Encontradas {len(apis)} APIs na lista. Iniciando validação massiva (Pode levar um minuto)...")
    
    valid_apis = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(validate_api, apis)
        for res in results:
            if res:
                valid_apis.append(res)
                
    print(f"✅ Validação concluída. APIs Online: {len(valid_apis)} de {len(apis)}.")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# 🌐 Cofre de APIs Públicas Validadas\n\n")
        f.write("Estas APIs foram testadas pelo Agente de Segurança e estão prontas para uso no código.\n\n")
        f.write("| Nome da API | Descrição | URL (Endpoint) |\n")
        f.write("| --- | --- | --- |\n")
        for api in valid_apis:
            f.write(f"| {api['name']} | {api['desc']} | {api['url']} |\n")
            
    print(f"📄 Arquivo salvo em {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
