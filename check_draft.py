import sys
# Read the draft endpoint from line 480 to end
with open('backend/routers/draft.py', 'r') as f:
    lines = f.readlines()
    for line in lines[480:]:
        print(line, end='')
