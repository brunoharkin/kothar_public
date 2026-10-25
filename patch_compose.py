import yaml

with open('docker-compose.yml', 'r') as f:
    d = yaml.safe_load(f)

if 'kothar_chromadb' in d['services']:
    env = d['services']['kothar_chromadb'].get('environment', {})
    if 'CHROMA_SERVER_AUTH_CREDENTIALS_PROVIDER' in env:
        del env['CHROMA_SERVER_AUTH_CREDENTIALS_PROVIDER']
    if 'CHROMA_SERVER_AUTH_CREDENTIALS' in env:
        del env['CHROMA_SERVER_AUTH_CREDENTIALS']
    if 'CHROMA_SERVER_AUTH_PROVIDER' in env:
        del env['CHROMA_SERVER_AUTH_PROVIDER']

with open('docker-compose.yml', 'w') as f:
    yaml.dump(d, f, default_flow_style=False, sort_keys=False)
