import os
import sys
import json

INPUT_DIR_NAME = 'prevent_actions'

if len(sys.argv) < 2:
    print(
        'USAGE: python3 combine-actions.py ACTION_LIST_ID')
    sys.exit(1)

INPUT_FN = os.path.join(INPUT_DIR_NAME, '%s.json' % sys.argv[1])
with open(INPUT_FN, 'r') as h:
    actions = json.load(h)

for group in actions:
    for act in group:
        print(act)
