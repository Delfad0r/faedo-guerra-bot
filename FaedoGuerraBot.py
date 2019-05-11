import numpy as np
import pickle
import time
import shutil
import os
import random

from constants import *
import game_engine, game_graphics, telegram_bot, report

import copy

channel_name = '@FaedoGuerraBotTestChannel'

def loop_func(state, description):
    img = game_graphics.draw_full_image(state, description)
    rep = report.pretty_report(state['rooms'], description)
    img.save('img.png', 'PNG')
    telegram_bot.send_photo(channel_name, open('img.png', 'rb'), caption = rep)
    os.remove('img.png')
    print('Iteration %d' % state['iterations'])
    print(rep)
    shutil.copy(save_file, save_backup_file)
    pickle.dump(state, open(save_file, 'wb'))

def fast_loop_func(state, description):
    pass

state0 = pickle.load(open(save_file, 'rb'))
state = copy.deepcopy(state0)
# Watch out: game_graphics uses random!
'''if not 'next_iteration' in state:
    state['next_iteration'] = time.time()
random_state = random.getstate()
np_random_state = np.random.get_state()
game_engine.main_loop(state, 0, fast_loop_func)
print('This game will take %d iterations' % state['iterations'])
input()
state = state0
random.setstate(random_state)
np.random.set_state(np_random_state)'''
if not 'next_iteration' in state:
    state['next_iteration'] = time.time()
game_engine.main_loop(state, 0, loop_func)