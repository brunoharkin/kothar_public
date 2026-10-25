import yaml

with open('/home/bruno-harkin/kothar/docker-compose.yml', 'r') as f:
    d = yaml.safe_load(f)

if 'kothar_chromadb' in d['services']:
    # Remove o healthcheck do chromadb para não travar a stack
    if 'healthcheck' in d['services']['kothar_chromadb']:
        del d['services']['kothar_chromadb']['healthcheck']
    
# E precisamos remover a dependência de healthcheck do chromadb no kothar_api
if 'kothar_api' in d['services']:
    if 'kothar_chromadb' in d['services']['kothar_api']['depends_on']:
        d['services']['kothar_api']['depends_on']['kothar_chromadb']['condition'] = 'service_started'

with open('/home/bruno-harkin/kothar/docker-compose.yml', 'w') as f:
    yaml.dump(d, f, default_flow_style=False, sort_keys=False)
