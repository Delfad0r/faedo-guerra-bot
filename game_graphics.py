import imageio
import itertools
import numpy as np
import random
import re
from scipy import ndimage
from skimage import transform, morphology, filters, draw
from PIL import Image, ImageDraw, ImageFont

import report
from FGBconstants import *


def get_corona_rectangle(w, h, color):
    wc, hc = 48, 48
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    corona = Image.open('corona.png').resize((200, 200))
    for i in range(int(w * h / (wc * hc))):
        wn = int(wc * random.uniform(.5, 1.5))
        hn = wn
        new_corona = corona.rotate(random.randrange(360), 3, True).resize((wn, hn))
        x = int(random.uniform(0, w))
        y = int(random.uniform(0, h))
        img.paste(new_corona, (x - wn // 2, y - hn // 2), new_corona)
    return img

#huge_corona_rectangle = get_corona_rectangle(*imageio.imread('data/floor0-walls.png').shape[1 : : -1], 'white')
#imageio.imwrite('data/huge-corona-rectangle.png', huge_corona_rectangle)
#print('I just saved you a hell lot of time')
huge_corona_rectangle = Image.open('data/huge-corona-rectangle.png')

def draw_outline_text(imagedraw, xy, t, fill, outline, thickness, **kwargs):
    x, y = xy
    for i in range(1, thickness + 1):
        imagedraw.text((x - i, y), t, fill = outline, **kwargs)
        imagedraw.text((x + i, y), t, fill = outline, **kwargs)
        imagedraw.text((x, y - i), t, fill = outline, **kwargs)
        imagedraw.text((x, y + i), t, fill = outline, **kwargs)
        imagedraw.text((x - i, y - i), t, fill = outline, **kwargs)
        imagedraw.text((x - i, y + i), t, fill = outline, **kwargs)
        imagedraw.text((x + i, y - i), t, fill = outline, **kwargs)
        imagedraw.text((x + i, y + i), t, fill = outline, **kwargs)
    imagedraw.text(xy, t, fill = fill, **kwargs)

def draw_enriched_text(state, img, xy, text, **kwargs):
    offset0 = 20
    offset1 = 14
    x, y = xy
    rooms = state['rooms']
    imagedraw = ImageDraw.Draw(img)
    for i, t in zip(itertools.count(), re.split('\[|\]', text)):
        if i % 2:
            x += offset0
            i = int(t)
            r = rooms[i]
            t = r['person']
            w, h = imagedraw.textsize(t, font = kwargs['font'])
            imagedraw.rectangle([x - offset0, y - offset0, x + w + offset0, y + h + offset0], fill = 'black')
            imagedraw.rectangle([x - offset1, y - offset1, x + w + offset1, y + h + offset1], fill = tuple(r['color']))
            if i in state['infected']:
                corona = get_corona_rectangle(w + 2 * offset1, h + 2 * offset1, 'white')
                img.paste(corona, (x - offset1, y - offset1), corona)
            draw_outline_text(imagedraw, (x, y), t, fill = 'white', outline = 'black', thickness = 3, **kwargs)
            x += w + offset0
        else:
            imagedraw.text((x, y), t, fill = 'black', **kwargs)
            x += imagedraw.textsize(t, font = kwargs['font'])[0]

def draw_floor(floor_id, state, description, is_large):
    rooms = state['rooms']
    floor = state['floors'][floor_id]
    # Rooms backgroud
    walls_img = imageio.imread('data/%s-walls.png' % floor_id)
    rooms_img = imageio.imread('data/%s-rooms.png' % floor_id)
    regions, num_regions = ndimage.label(walls_img[:, :, 3] == 0)
    palette = np.ones((num_regions + 1, 4), dtype = 'uint8') * 255
    palette[0] = [0, 0, 0, 255]
    infected_palette = np.ones(num_regions + 1, dtype = 'uint8') * 255
    for i in floor['rooms']:
        r = rooms[i]
        if r['owner']:
            palette[regions[r['inside_point']]] = rooms[r['owner']]['color']
            infected_palette[regions[r['inside_point']]] = 255 * (r['owner'] not in state['infected'])
        if description['type'] == 'attack' and description['room'] == i:
            palette[regions[r['inside_point']]] = rooms[description['prev_owner']]['color'] if description['prev_owner'] else np.array([255, 255, 255, 255], dtype = 'uint8')
            infected_palette[regions[r['inside_point']]] = 255 * (description['prev_owner'] not in state['infected'])
    img = palette[regions]
    infected_mask = infected_palette[regions]
    if description['type'] == 'attack' and description['room'] in floor['rooms']:
        r = rooms[description['room']]
        room_region = regions == regions[r['inside_point']]
        rc = r['center']
        update_mask = np.zeros(regions.shape, dtype = 'bool')
        bbox0 = np.where(np.any(room_region, axis = 1))[0][[0, -1]]
        bbox1 = np.where(np.any(room_region, axis = 0))[0][[0, -1]]
        m = update_mask[bbox0[0] - 2 * one_meter : bbox0[1] + 2 * one_meter, bbox1[0] - 2 * one_meter : bbox1[1] + 2 * one_meter]
        m[:, :] = morphology.binary_dilation(
            draw.random_shapes(
                m.shape,
                max_shapes = 2 * m.size // (one_meter * one_meter),
                min_shapes = 2 * m.size // (one_meter * one_meter),
                min_size = one_meter * 0.1,
                max_size = one_meter * 0.1,
                multichannel = False,
                shape = 'circle',
                allow_overlap = True
            )[0] < 255,
            morphology.disk(one_meter * 0.5)
            )
        img = np.where(np.logical_and(update_mask, room_region)[:, :, None], np.array((0, 0, 0, 255), dtype = 'uint8'), img)
        infected_mask = np.where(np.logical_and(update_mask, room_region), 255, infected_mask)
        m[:, :] = morphology.binary_erosion(m, morphology.disk(one_meter * 0.2))
        img = np.where(np.logical_and(update_mask, room_region)[:, :, None], rooms[description['new_owner']]['color'], img)
        infected_mask = np.where(np.logical_and(update_mask, room_region), 255 * (description['new_owner'] not in state['infected']), infected_mask)
    # Corona
    infected_mask = Image.fromarray(infected_mask)
    corona = huge_corona_rectangle.copy()
    corona.paste((0, 0, 0, 0), (0, 0), infected_mask)
    # Labels
    img_pillow = Image.fromarray(img)
    img_pillow.paste(corona, (0, 0), corona)
    draw_pillow = ImageDraw.Draw(img_pillow)
    font_rooms = ImageFont.truetype('Roboto-Bold.ttf', size = int(one_meter * 1))
    font_floor = ImageFont.truetype('Roboto-Bold.ttf', size = one_meter * 4)
    for i in floor['rooms']:
        r = rooms[i]
        y, x = r['center']
        if is_large:
            if not (description['type'] == 'attack' and description['room'] == i) and not (description['type'] != 'attack' and r['owner'] == description['person']):
                s = r['short_name']
                col = 'black' if r['owner'] is None else 'white'
                scol = 'white' if r['owner'] is None else 'black'
                x -= draw_pillow.textsize(s, font = font_rooms)[0] // 2
                y -= draw_pillow.textsize(s, font = font_rooms)[1] // 2
                draw_outline_text(draw_pillow, (x, y), s, fill = col, outline = scol, thickness = 6, font = font_rooms)
    draw_pillow.text((1000, 2350), floor['name'], fill = 'black', font = font_floor)
    img_pillow = img_pillow.resize((img_pillow.size[0] // 2, img_pillow.size[1] // 2), Image.BICUBIC)
    return img_pillow

def draw_report_section(width, state, description):
    rooms = state['rooms']
    img = Image.new('RGBA', (width, one_meter * 7), 'white')
    imagedraw = ImageDraw.Draw(img)
    font =  ImageFont.truetype('Roboto-Bold.ttf', size = int(0.8 * one_meter))
    for i, s in enumerate(report.generate_report(state, description).split('\n')):
        draw_enriched_text(state, img, (one_meter * 3, int(one_meter * (2 + 2.4 * i))), s, font = font)
    return img

def draw_leaderboard(height, state):
    rooms = state['rooms']
    font = ImageFont.truetype('Roboto-Bold.ttf', size = int(0.8 * one_meter))
    img = Image.new('RGBA', (0, 0), 'white')
    imagedraw = ImageDraw.Draw(img)
    width = 9 * one_meter+ imagedraw.textsize(' ha 999 stanze', font = font)[0] + max(imagedraw.textsize(r['person'], font = font)[0] for r in rooms.values() if 'person' in r)
    img = Image.new('RGBA', (width, height), 'white')
    imagedraw = ImageDraw.Draw(img)
    leaders = {r['owner'] : 0 for r in rooms.values() if r['owner']}
    for r in rooms.values():
        if r['owner']:
            leaders[r['owner']] += 1
    leaders = list(leaders.items())
    random.shuffle(leaders)
    leaders = sorted(leaders, key = lambda x: x[1], reverse = True)[0 : 10]
    for i, (l, c) in zip(itertools.count(), leaders):
        draw_enriched_text(state, img, (one_meter * 5, one_meter * (2 + 3 * i)), '[%d] ha %d stanz%s' % (l, c, 'a' if c == 1 else 'e'), font = font)
    return img

def draw_stats(width, height, state):
    rooms = state['rooms']
    font = ImageFont.truetype('Roboto-Bold.ttf', size = int(0.8 * one_meter))
    img = Image.new('RGBA', (width, height), 'white')
    imagedraw = ImageDraw.Draw(img)
    rectangle_w = width - 10 * one_meter
    rectangle_h = imagedraw.textsize('SNS', font = font)[1]
    offset0 = 28
    offset1 = 22
    x = one_meter * 5 + offset0
    y = one_meter * 2
    imagedraw.rectangle([x - offset0, y - offset0, x + rectangle_w + offset0, y + rectangle_h + offset0], fill = 'black')
    imagedraw.rectangle([x - offset1, y - offset1, x + rectangle_w + offset1, y + rectangle_h + offset1], fill = 'white')
    sns_rooms = len([() for r in rooms.values() if r['owner'] and r['owner'] <= 167 and r['owner'] % 2 == 1 and r['owner'] != 107])
    sssup_rooms = len([() for r in rooms.values() if r['owner'] and r['owner'] <= 167 and (r['owner'] % 2 == 0 or r['owner'] == 107)])
    imagedraw.rectangle([x - offset1, y - offset1, x + int(rectangle_w * sns_rooms / len(rooms)), y + rectangle_h + offset1], fill = 'blue')
    imagedraw.rectangle([x + int(rectangle_w * (1 - sssup_rooms / len(rooms))), y - offset1, x + rectangle_w + offset1, y + rectangle_h + offset1], fill = 'red')
    sns_text = 'SNS - %d%%' % round(100 * sns_rooms / len(rooms))
    draw_outline_text(imagedraw, (x, y), sns_text, fill = 'white', outline = 'black', thickness = 3, font = font)
    sssup_text = '%d%% - SSSUP' % round(100 * sssup_rooms / len(rooms))
    draw_outline_text(imagedraw, (x + rectangle_w - imagedraw.textsize(sssup_text, font = font)[0], y), sssup_text, fill = 'white', outline = 'black', thickness = 3, font = font)
    if len(state['r0'][0]):
        large_font = ImageFont.truetype('Roboto-Bold.ttf', size = int(1.2 * one_meter))
        subscript_font = ImageFont.truetype('Roboto-Bold.ttf', size = int(.7 * one_meter))
        r0 = sum(state['r0'][0]) / len(state['r0'][0])
        imagedraw.text((x - offset0, y + rectangle_h + offset0 + one_meter), 'R  = %.2f' % r0, fill = 'black', font = large_font)
        imagedraw.text((x - offset0 + imagedraw.textsize('R', font = large_font)[0] , y + rectangle_h + offset0 + int(one_meter * 1.8)), '0', fill = 'black', font = subscript_font)
    return img
    
def draw_full_image(state, description):
    #if len(state['r0'][0]):
        #print('R0 list:', state['r0'][0])
    rooms = state['rooms']
    floors = state['floors']
    if description['type'] == 'attack':
        large_floor = min((k for k, f in floors.items() if description['room'] in f['rooms']), key =
            lambda f: min((rooms[r]['dist'][description['room']]
                for r in floors[f]['rooms']
                if rooms[r]['owner'] == description['new_owner']
                    and r != description['room']
                    and description['room'] in floors[f]['rooms']
                ), default = float('inf'))
            )
    else:
        large_floor = max(floors, key = lambda f: sum(1 for r in floors[f]['rooms'] if rooms[r]['owner'] == description['person']))
    small_floors = sorted((f for f in floors.keys() if f != large_floor), key = lambda f: floors[f]['altitude'])
    large_floor_img = draw_floor(large_floor, state, description, True)
    large_w, large_h = large_floor_img.size
    small_w, small_h = large_w // 2, large_h // 2
    floors_w = large_w + 2 * small_w
    leaderboard = draw_leaderboard(large_h, state)
    leaderboard_w = leaderboard.size[0]
    w = floors_w + leaderboard_w
    report = draw_report_section(floors_w, state, description)
    report_h = report.size[1]
    h = large_h + report_h
    sns_vs_sssup = draw_stats(leaderboard_w, report_h, state)
    img = Image.new('RGBA', (w, h), 'white')
    img.paste(report, (0, 0))
    img.paste(large_floor_img, (0, report_h))
    img.paste(leaderboard, (floors_w, report_h))
    img.paste(sns_vs_sssup, (floors_w, 0))
    for i, f in zip(itertools.count(), small_floors):
        small_floor_img = draw_floor(f, state, description, False)
        small_floor_img = small_floor_img.resize((small_w, small_h), Image.BICUBIC)
        img.paste(small_floor_img, (large_w + (i % 2) * small_w, report_h + (i // 2) * small_h))
    flag = Image.open('italian-flag.png')
    img.paste(flag, (2856, 165), flag)
    return img

def draw_players_list(state):
    rooms = state['rooms']
    font = ImageFont.truetype('Roboto-Bold.ttf', size = int(0.8 * one_meter))
    img = Image.new('RGBA', (0, 0), 'white')
    imagedraw = ImageDraw.Draw(img)
    width = 8 * one_meter + max(imagedraw.textsize(r['person'] + r['name'], font = font)[0] for r in rooms.values() if 'person' in r)
    height = 62 * one_meter
    players = ['[%d] %s' % (i, r['name']) for i, r in rooms.items() if 'person' in r]
    cols = ((len(players) - 1) // 20) + 1
    img = Image.new('RGBA', (width * cols, height), 'white')
    imagedraw = ImageDraw.Draw(img)
    for i, s in zip(itertools.count(), players):
        draw_enriched_text(state, img, (4 * one_meter + width * (i // 20), one_meter * (2 + 3 * (i % 20))), s, font = font)
    return img
    
    
