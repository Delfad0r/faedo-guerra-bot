import itertools
import re

def generate_report(state, description):
    rooms = state['rooms']
    if description['type'] == 'attack':
        room = description['room']
        new_owner = description['new_owner']
        prev_owner = description['prev_owner']
        if prev_owner is not None:
            if any(r['owner'] == prev_owner for r in rooms.values()):
                s = '[{0}] ha sottratto {1} a [{2}]'
                if prev_owner in state['infected']:
                    s += ', incurante della carica virale'
            else:
                s = '[{0}] ha conquistato {1}, cancellando [{2}] dalla faccia del Faedo\nAnd [{0}] is a test'
                if prev_owner in state['infected']:
                    s = '[{0}] ha sacrificato la sua salute per conquistare {1} e cancellare [{2}] dalla faccia del Faedo'
        else:
            s =  '[%d] ha conquistato %s' % (new_owner, rooms[room]['name'])
        return s.format(new_owner, rooms[room]['name'], prev_owner)
    elif description['type'] == 'heal':
        person = description['person']
        return '[%d] è guarit* ed è più agguerrit* che mai' % person
    elif description['type'] == 'infect':
        person = description['person']
        return '[%d] accusa sintomi influenzali' % person

def pretty_report(state, description):
    report = generate_report(state, description)
    ans = ''
    for i, t in zip(itertools.count(), re.split('\[|\]', report)):
        if i % 2:
            ans += state['rooms'][int(t)]['person']
        else:
            ans += t
    return ans
