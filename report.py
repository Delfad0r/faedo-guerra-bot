import itertools
import random
import re

with open('sentences/heal.txt', 'r') as fin:
    sentences_heal = [l.strip() for l in fin if l]

with open('sentences/infect.txt', 'r') as fin:
    sentences_infect = [l.strip() for l in fin if l]

with open('sentences/conquer.txt', 'r') as fin:
    sentences_conquer = [l.strip() for l in fin if l]

with open('sentences/conquer_infect.txt', 'r') as fin:
    sentences_conquer_infect = [l.strip() for l in fin if l]

with open('sentences/conquer_eradicate.txt', 'r') as fin:
    sentences_conquer_eradicate = [l.strip() for l in fin if l]
    
with open('sentences/conquer_immune.txt', 'r') as fin:
    sentences_conquer_immune = [l.strip() for l in fin if l]
    
with open('sentences/conquer_no_defender.txt', 'r') as fin:
    sentences_conquer_no_defender = [l.strip() for l in fin if l]

def generate_report(state, description):
    random.seed(state['iterations'])
    rooms = state['rooms']
    if description['type'] == 'attack':
        room = description['room']
        new_owner = description['new_owner']
        prev_owner = description['prev_owner']
        if prev_owner is not None:
            if prev_owner in state['infected']:
                if new_owner in state['infected']:
                    s = random.choice(sentences_conquer_infect)
                else:
                    s = random.choice(sentences_conquer_immune)
            else:
                s = random.choice(sentences_conquer)
            if all(r['owner'] != prev_owner for r in rooms.values()):
                s += '\n' + random.choice(sentences_conquer_eradicate)
            return s.format(na = '[%d]' % new_owner, ga = rooms[new_owner]['gender'], nd = '[%d]' % prev_owner, gd = rooms[prev_owner]['gender'], r = rooms[room]['name'])
        else:
            s =  random.choice(sentences_conquer_no_defender)
            return s.format(n = '[%d]' % new_owner, g = rooms[new_owner]['gender'], r = rooms[room]['name'])
    elif description['type'] == 'heal':
        person = description['person']
        s = random.choice(sentences_heal)
        return s.format(n = '[%d]' % person, g = rooms[person]['gender'])
    elif description['type'] == 'infect':
        person = description['person']
        s = random.choice(sentences_infect)
        return s.format(n = '[%d]' % person, g = rooms[person]['gender'])
    else:
        assert False, 'action %s unknown' % description['type']

def pretty_report(state, description):
    report = generate_report(state, description)
    ans = ''
    for i, t in zip(itertools.count(), re.split('\[|\]', report)):
        if i % 2:
            ans += state['rooms'][int(t)]['person']
        else:
            ans += t
    return ans
