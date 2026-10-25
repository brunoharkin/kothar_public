import yaml

with open('/home/bruno-harkin/kothar/docker-compose.yml', 'r') as f:
    d = yaml.safe_load(f)

if 'kothar_ollama' not in d.get('services', {}):
    d['services']['kothar_ollama'] = {
        'image': 'ollama/ollama:latest',
        'container_name': 'kothar_ollama',
        'restart': 'unless-stopped',
        'volumes': ['kothar_ollama_data:/root/.ollama'],
        'ports': ['11434:11434'],
        'networks': ['kothar_net'],
        'deploy': {
            'resources': {
                'limits': {
                    'cpus': '1.0',
                    'memory': '1.5g'
                }
            }
        }
    }
    
    if 'volumes' not in d:
        d['volumes'] = {}
    if 'kothar_ollama_data' not in d['volumes']:
        d['volumes']['kothar_ollama_data'] = None

with open('/home/bruno-harkin/kothar/docker-compose.yml', 'w') as f:
    yaml.dump(d, f, default_flow_style=False, sort_keys=False)
