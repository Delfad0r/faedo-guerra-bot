from collections import deque
import numpy as np
import random
import time

from FGBconstants import *

def one_iteration(state):
    random.setstate(state['random_state'])
    np.random.set_state(state['np_random_state'])
    rooms = state['rooms']
    floors = state['floors']
    survivors = { r['owner'] for r in state['rooms'].values() if r['owner'] is not None }
    u, v = (*map(deque, zip(*((i, j) for i, j in zip(state['infected'], state['r0'][1]) if i in survivors))), deque(), deque())[: 2]
    state['infected'] = u
    state['r0'] = (state['r0'][0], v)
    # Healing
    healing_factor = .5 * (len(state['infected']) / len(survivors)) ** 1.5
    if random.random() < healing_factor or len(state['infected']) == len(survivors):
        healed_person = None
        x = random.randrange(1, 2 ** len(state['infected']))
        for i in range(len(state['infected'])):
            if x == 1:
                healed_person = state['infected'][-1 - i]
                state['infected'].remove(healed_person)
                state['r0'][1].remove(state['r0'][1][-1 - i])
                break
            x //= 2
        assert(healed_person is not None)
        state['immunity'][healed_person] = random.randrange(30, 50)
        description = { 'type' : 'heal', 'person' : healed_person }
    # Infection
    else:
        potential_infected_people = [x for x in survivors if x not in state['infected'] and state['immunity'][x] == 0]
        if len(potential_infected_people) and random.randrange(15) == 0 and len(survivors) > 1:
            infected_person = random.choice(potential_infected_people)
            if random.randrange(3) == 0 or len(state['infected']) == 0:
                state['r0'][0].append(1) # external source
            else:
                state['r0'][0][0] += 1 # internal source
            state['infected'].append(infected_person)
            state['r0'][1].append(len(state['r0'][0]))
            state['r0'][0].append(0)
            description = { 'type' : 'infect', 'person' : infected_person }
        # Conquer
        else:
            attacker = random.choice(list(r for r in rooms.values() if r['owner'] is not None and r['owner'] not in state['infected']))['owner']
            def compute_prob(r):
                sigma = one_meter * 0.6
                infection_coeff = .5 if r['owner'] in state['infected'] else 1
                return infection_coeff * sum(np.exp(-max(0, r['dist'][i] - one_meter) ** 2 / (2 * sigma ** 2)) for i, s in rooms.items() if s['owner'] == attacker)
            rooms_idx, rooms_prob = zip(*((i, compute_prob(r)) for i, r in rooms.items() if r['owner'] != attacker))
            rooms_prob /= sum(rooms_prob)
            defender = np.random.choice(rooms_idx, size = 1, replace = True, p = rooms_prob)[0]
            description = { 'type' : 'attack', 'room' : defender, 'prev_owner' : rooms[defender]['owner'], 'new_owner' : attacker }
            if rooms[defender]['owner'] in state['infected']:
                if state['immunity'][attacker] == 0:
                    state['infected'].append(attacker)
                    state['r0'][1].append(len(state['r0'][0]))
                    state['r0'][0].append(0)
                    i = state['infected'].index(rooms[defender]['owner'])
                    state['r0'][0][state['r0'][1][i]] += 1
            rooms[defender]['owner'] = attacker
    state['immunity'] = [max(i - 1, 0) for i in state['immunity']]
    state['iterations'] += 1
    state['random_state'] = random.getstate()
    state['np_random_state'] = np.random.get_state()
    return description

def check_game_over(state):
    survivors = { r['owner'] for r in state['rooms'].values() if r['owner'] is not None }
    if len(survivors) == 1:
        return survivors.pop()
    else:
        return None

def main_loop(state, wait_time, begin_func, end_func, save_func, prep_func, premain_func, main_func):
    if 'has_begun' not in state:
        begin_func(state)
        state['has_begun'] = True
        state['ready_for_main'] = False
        save_func(state)
    while True:
        if not state['ready_for_main']:
            state['description'] = one_iteration(state)
            prep_func(state, state['description'])
            state['ready_for_main'] = True
            save_func(state)
        if time.time() < state['next_iteration']:
            if time.time() > state['next_iteration'] - 120 and 'has_premain' not in state:
                premain_func(state, state['description'])
                state['has_premain'] = True
                save_func(state)
            else:
                time.sleep(1)
        else:
            state['next_iteration'] = state['next_iteration'] + wait_time
            main_func(state, state['description'])
            if 'has_premain' in state:
                del state['has_premain']
            state['ready_for_main'] = False
            save_func(state)
            survivor = check_game_over(state)
            if survivor:
                end_func(state, survivor)
                return
