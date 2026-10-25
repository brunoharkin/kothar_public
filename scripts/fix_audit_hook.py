with open('/home/bruno-harkin/kothar/hooks/kothar-structure-audit.sh', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'echo "⚠️  AUDITORIA ESTRUTURAL DETECTOU $VIOLATIONS VIOLAÇÕES"' in line:
        lines[i] = '    echo "⚠️  AUDITORIA ESTRUTURAL DETECTOU $VIOLATIONS VIOLAÇÕES" >&2\n'
    elif 'echo "   Veja: $AUDIT_REPORT"' in line:
        lines[i] = '    echo "   Veja: $AUDIT_REPORT" >&2\n'
    elif 'echo "   AÇÃO: Organize a estrutura ANTES de criar novos arquivos"' in line:
        lines[i] = '    echo "   AÇÃO: Organize a estrutura ANTES de criar novos arquivos" >&2\n'
    elif 'echo ""\n' == line and 'if [[ "$VIOLATIONS" -gt 0 ]]; then' in lines[i-1]:
        lines[i] = '    echo "" >&2\n'

with open('/home/bruno-harkin/kothar/hooks/kothar-structure-audit.sh', 'w') as f:
    f.writelines(lines)
