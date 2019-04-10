import imageio
import pickle
import numpy as np 
from scipy import ndimage, spatial
from skimage import morphology, transform
import random
import colorsys

from constants import *

with open(rooms_file, 'rb') as fin:
    rooms = pickle.load(fin)

with open(floors_file, 'rb') as fin:
    floors = pickle.load(fin)

with open(stairs_file, 'rb') as fin:
    stairs = pickle.load(fin)

print(floors)

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
        #r['dist'].update({k : np.linalg.norm(np.array(r['center']) - np.array(s['center'])) + np.min(spatial.distance.cdist(boundary[j], boundary[k])) for k, s in
        r['dist'].update({k : np.min(spatial.distance.cdist(boundary[j], boundary[k])) / 2 for k in f['rooms']})

for s in stairs:
    for i in range(len(s) - 1):
        rooms[s[i]]['dist'][s[i + 1]] = 0
        rooms[s[i + 1]]['dist'][s[i]] = 0

'''colors = []
for i in np.linspace(0, 1, 14, endpoint = False):
    for j in np.linspace(0, 1, 14, endpoint = False):
        if abs(i - j) > 1e-3:
            colors.append(
                ((np.array(colorsys.hsv_to_rgb(i, 0.9, 0.75) + (1, )) * 255).astype('uint8'),
                 (np.array(colorsys.hsv_to_rgb(j, 1, 1) + (1, )) * 255).astype('uint8'))
                )
'''
colors = [
    ((np.array(colorsys.hsv_to_rgb(i / 15, 0.9, 0.75) + (1, )) * 255).astype('uint8'),
    (np.array(colorsys.hsv_to_rgb(j / 15, 1, 1) + (1, )) * 255).astype('uint8'))
    for i in range(15) for j in range(15) if 1 < (j - i) % 15 < 14
    ]

random.shuffle(colors)

for k, r in rooms.items():
    if 'neutral' in r:
        r['owner'] = None
    else:
        r['owner'] = k
        r['color'], r['boundary_color'] = colors.pop()

state = {'rooms' : rooms, 'floors' : floors, 'iterations' : 0}

with open(save_file, 'wb') as fout:
    pickle.dump(state, fout)