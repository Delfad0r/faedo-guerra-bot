import numpy as np
import random
import time

from constants import *

def one_iteration(state):
    random.setstate(state['random_state'])
    np.random.set_state(state['np_random_state'])
    rooms = state['rooms']
    floors = state['floors']
    attacker = random.choice(list(r for r in rooms.values() if r['owner'] is not None))['owner']
    def compute_prob(r):
        sigma = one_meter * 0.6
        return sum(np.exp(-max(0, r['dist'][i] - one_meter) ** 2 / (2 * sigma ** 2)) for i, s in rooms.items() if s['owner'] == attacker)
    rooms_idx, rooms_prob = zip(*((i, compute_prob(r)) for i, r in rooms.items() if r['owner'] != attacker))
    rooms_prob /= sum(rooms_prob)
    defender = np.random.choice(rooms_idx, size = 1, replace = True, p = rooms_prob)[0]
    #print(list(zip(rooms_idx, rooms_prob)))
    #print([p for i, p in zip(rooms_idx, rooms_prob) if i == defender][0])
    description = {'room' : defender, 'prev_owner' : rooms[defender]['owner'], 'new_owner' : attacker}
    #description = "%s ha conquistato %s, sottraendola a %s" % (rooms[attacker]['name'], rooms[defender]['name'], rooms[rooms[defender]['owner']]['name'])
    rooms[defender]['owner'] = attacker
    state['iterations'] += 1
    state['random_state'] = random.getstate()
    state['np_random_state'] = np.random.get_state()
    return description

def check_game_over(state):
    survivors = {r['owner'] for r in state['rooms'].values()}
    if len(survivors) == 1:
        return survivors.pop()
    else:
        return None

def main_loop(state, wait_time, begin_func, end_func, save_func, prep_func, main_func):
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
            time.sleep(1)
        else:
            state['next_iteration'] += wait_time
            main_func(state, state['description'])
            state['ready_for_main'] = False
            save_func(state)
            survivor = check_game_over(state)
            if survivor:
                end_func(state, survivor)
                return