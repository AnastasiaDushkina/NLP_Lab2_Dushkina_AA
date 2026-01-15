import json
from pathlib import Path

nb = json.loads(Path('NLP_Lab2_Dushkina_AA.ipynb').read_text(encoding='utf-8'))
# print RoutingDecision block (cell 13)
src = nb['cells'][13]['source']
start=None
for i,line in enumerate(src):
    if line.startswith('class RoutingDecision'):
        start=i
        break
for j in range(start, start+10):
    print(src[j].rstrip())
