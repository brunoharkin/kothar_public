import yaml

with open('/home/bruno-harkin/kothar/docker-compose.yml', 'r') as f:
    d = yaml.safe_load(f)

if 'kothar_api' in d['services']:
    vols = d['services']['kothar_api'].get('volumes', [])
    new_vols = ['../orby:/app/apps/orby:ro', '../crm-Sophia:/app/apps/crm-Sophia:ro', '../chronodesk:/app/apps/chronodesk:ro']
    for v in new_vols:
        if v not in vols:
            vols.append(v)
    d['services']['kothar_api']['volumes'] = vols

with open('/home/bruno-harkin/kothar/docker-compose.yml', 'w') as f:
    yaml.dump(d, f, default_flow_style=False, sort_keys=False)
