import itertools
import re

def generate_report(rooms, description):
    room = description['room']
    new_owner = description['new_owner']
    prev_owner = description['prev_owner']
    if prev_owner is not None:
        if any(r['owner'] == prev_owner for r in rooms.values()):
            return '[%d] ha conquistato %s, precedentemente di [%d]' % (new_owner, rooms[room]['name'], prev_owner)
        else:
            return '[%d] ha conquistato %s, cancellando [%d] dalla faccia del Faedo' % (new_owner, rooms[room]['name'], prev_owner)
    else:
        return '[%d] ha conquistato %s' % (new_owner, rooms[room]['name'])

def pretty_report(rooms, description):
    report = generate_report(rooms, description)
    ans = ''
    for i, t in zip(itertools.count(), re.split('\[|\]', report)):
        if i % 2:
            ans += rooms[int(t)]['person']
        else:
            ans += t
    return ans