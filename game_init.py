from collections import deque
import imageio
import itertools
import pickle
import numpy as np 
from scipy import ndimage, spatial
from skimage import morphology, transform
import sys
import time
import random

from FGBconstants import *

first_iteration = time.mktime(time.strptime(sys.argv[1], '%d/%m/%y %H:%M'))

with open(rooms_file, 'rb') as fin:
    rooms = pickle.load(fin)

with open(floors_file, 'rb') as fin:
    floors = pickle.load(fin)

with open(stairs_file, 'rb') as fin:
    stairs = pickle.load(fin)

people = {}
with open(people_file, 'r') as fin:
    for i, p in zip(itertools.count(1), fin.read().splitlines()):
        people[i] = p
gender = {}
with open(gender_file, 'r') as fin:
    for i, g in zip(itertools.count(1), fin.read().splitlines()):
        g = g.strip()
        if g:
            gender[i] = 'oa'['MF'.index(g)]

with open(colors_file, 'r') as fin:
    colors = [np.array(tuple(map(int, c.split())) + (255, ), dtype = 'uint8') for c in fin]
    colors = [c for c in colors if 255 * 4 - 100 >= c.sum() >= 255 + 100][: len([p for p in people.values() if p])]
    random.shuffle(colors)

for r in rooms.values():
    r['dist'] = {i : float('inf') for i in rooms}

for i, f in floors.items():
    walls_img = imageio.imread('data/%s-walls-large.png' % i)
    rooms_img = imageio.imread('data/%s-rooms.png' % i)
    imageio.imwrite('data/%s-walls.png' % i, walls_img[: : 2, : : 2])
    regions, num_regions = ndimage.label(walls_img[:, :, 3] == 0)
    com = ndimage.measurements.center_of_mass(np.ones(regions.shape), regions, range(num_regions + 1))
    boundary_list = np.where(morphology.binary_dilation(regions == 0), regions, 0).nonzero()
    boundary = {}
    for y, x in np.transpose(rooms_img[:, :, 3].nonzero()):
        r = rooms_img[y][x][0]
        reg = regions[y][x]
        rooms[r]['center'] = tuple(map(lambda x : int(x / 2), com[reg]))
        rooms[r]['inside_point'] = (y // 2, x // 2)
        boundary[r] = np.transpose(boundary_list)[np.where(regions[boundary_list] == reg)]
    for j in f['rooms']:
        r = rooms[j]
        r['dist'].update({k : np.min(spatial.distance.cdist(boundary[j], boundary[k])) / 2 for k in f['rooms']})
        print(r['name'])

for s in stairs:
    for i in range(len(s) - 1):
        rooms[s[i]]['dist'][s[i + 1]] = 0
        rooms[s[i + 1]]['dist'][s[i]] = 0
for i, r in rooms.items():
    if i in people and people[i]:
        r['owner'] = i
        r['color'] = colors.pop()
        r['person'] = people[i]
        r['gender'] = gender[i]
        print(i, people[i], gender[i])
    else:
        r['owner'] = None

state = {
    'rooms' : rooms,
    'floors' : floors,
    'infected' : deque(),
    'immunity' : [0] * len(rooms),
    'r0' : ([], deque()),
    'iterations' : 0,
    'next_iteration' : first_iteration}

with open(save_file, 'wb') as fout:
    pickle.dump(state, fout)
