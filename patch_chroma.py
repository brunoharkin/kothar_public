import yaml
with open('docker-compose.yml', 'r') as f:
    d = yaml.safe_load(f)
if 'kothar_chromadb' in d['services']:
    env = d['services']['kothar_chromadb'].get('environment', {})
    env['CHROMA_SERVER_HOST'] = '0.0.0.0'
    env['CHROMA_SERVER_CORS_ALLOW_ANY_ORIGIN'] = 'True'
    d['services']['kothar_chromadb']['environment'] = env

with open('docker-compose.yml', 'w') as f:
    yaml.dump(d, f, default_flow_style=False, sort_keys=False)
