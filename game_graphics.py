import imageio
import itertools
import numpy as np
import re
from scipy import ndimage
from skimage import transform, morphology, filters, draw
from PIL import Image, ImageDraw, ImageFont

import report
from constants import *

def draw_centered_text(imagedraw, xy, *args, **kwargs):
    w, h = imagedraw.textsize(args[0], font = kwargs['font'])
    imagedraw.text((xy[0] - w / 2, xy[1] - h / 2), *args, **kwargs)

def draw_enriched_text(rooms, imagedraw, xy, text, **kwargs):
    offset0 = 20
    offset1 = 16
    offset2 = 9
    x, y = xy
    for i, t in zip(itertools.count(), re.split('\[|\]', text)):
        if i % 2:
            x += offset0
            r = rooms[int(t)]
            t = r['name']
            w, h = imagedraw.textsize(t, font = kwargs['font'])
            imagedraw.rectangle([x - offset0, y - offset0, x + w + offset0, y + h + offset0], fill = 'black')
            imagedraw.rectangle([x - offset1, y - offset1, x + w + offset1, y + h + offset1], fill = tuple(r['boundary_color']))
            imagedraw.rectangle([x - offset2, y - offset2, x + w + offset2, y + h + offset2], fill = tuple(r['color']))
            imagedraw.text((x, y), t, fill = 'white', **kwargs)
            x += w + offset0
        else:
            imagedraw.text((x, y), t, fill = 'black', **kwargs)
            x += imagedraw.textsize(t, font = kwargs['font'])[0]

def draw_floor(floor_id, floor, rooms, description, is_large):
    # Rooms backgroud
    walls_img = imageio.imread('data/%s-walls.png' % floor_id)
    rooms_img = imageio.imread('data/%s-rooms.png' % floor_id)
    regions, num_regions = ndimage.label(walls_img[:, :, 3] == 0)
    palette = np.ones((num_regions + 2, 4), dtype = 'uint8') * 255
    palette_boundary = np.ones((num_regions + 2, 4), dtype = 'uint8') * 255
    palette[0] = [0, 0, 0, 255]
    palette_boundary[0] = [0, 0, 0, 255]
    for i in floor['rooms']:
        r = rooms[i]
        if r['owner']:
            palette[regions[r['inside_point']]] = rooms[r['owner']]['color']
            palette_boundary[regions[r['inside_point']]] = rooms[r['owner']]['boundary_color']
    boundary_mask = filters.gaussian(morphology.binary_dilation(walls_img[:, :, 3] > 0, morphology.disk(one_meter * 0.5)), one_meter / 10)
    if description['room'] in floor['rooms']:
        r = rooms[description['room']]
        room_region = regions == regions[r['inside_point']]
        rc = r['center']
        update_mask = np.zeros(boundary_mask.shape, dtype = 'bool')
        bbox0 = np.where(np.any(room_region, axis = 1))[0][[0, -1]]
        bbox1 = np.where(np.any(room_region, axis = 0))[0][[0, -1]]
        #m = update_mask[max(0, rc[0] - 6 * one_meter) : rc[0] + 6 * one_meter, max(0, rc[1] - 15 * one_meter) : rc[1] + 15 * one_meter]
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
            morphology.disk(one_meter * 0.4)
            )
        update_mask = 1 - update_mask
        boundary_mask = np.where(update_mask + 1 - room_region, boundary_mask, filters.gaussian(morphology.binary_dilation(update_mask, morphology.disk(one_meter // 3)), one_meter / 10))
        regions = np.where(update_mask * room_region, num_regions + 1, regions)
        if description['prev_owner']:
            oldr = rooms[description['prev_owner']]
            palette[num_regions + 1] = oldr['color']
            palette_boundary[num_regions + 1] = oldr['boundary_color']
    img = (boundary_mask[:, :, None] * palette_boundary[regions] + (1 - boundary_mask[:, :, None]) * palette[regions]).astype('uint8')
    #img = transform.downscale_local_mean(img.astype('uint8'), (2, 2, 1), 255).astype('uint8')
    #return img
    # Labels
    img_pillow = Image.fromarray(img)
    draw_pillow = ImageDraw.Draw(img_pillow)
    font_rooms = ImageFont.truetype('Roboto-Bold.ttf', size = one_meter)
    font_floor = ImageFont.truetype('Roboto-Bold.ttf', size = one_meter * 4)
    if is_large:
        for i in floor['rooms']:
            r = rooms[i]
            if description['room'] != i:
                s = r['short_name'] if 'short_name' in r else r['name']
                col = 'black' if r['owner'] is None else 'white'
                draw_centered_text(draw_pillow, (r['center'][1], r['center'][0]), s, fill = col, font = font_rooms)
    draw_pillow.text((1000, 2350), floor['name'], fill = 'black', font = font_floor)
    img_pillow = img_pillow.resize((img_pillow.size[0] // 2, img_pillow.size[1] // 2), Image.BICUBIC)
    return img_pillow

def draw_report_section(width, rooms, description):
    img = Image.new('RGBA', (width, one_meter * 4))
    imagedraw = ImageDraw.Draw(img)
    font =  ImageFont.truetype('Roboto-Bold.ttf', size = int(0.8 * one_meter))
    draw_enriched_text(rooms, imagedraw, (one_meter * 3, one_meter * 2), report.generate_report(rooms, description), font = font)
    return img
    
def draw_full_image(state, description):
    rooms = state['rooms']
    floors = state['floors']
    large_floor = min((k for k, f in floors.items() if description['room'] in f['rooms']), key =
        lambda f: min((rooms[r]['dist'][description['room']]
            for r in floors[f]['rooms']
            if rooms[r]['owner'] == description['new_owner']
                and r != description['room']
                and description['room'] in floors[f]['rooms']
            ), default = float('inf'))
        )
    small_floors = sorted((f for f in floors.keys() if f != large_floor), key = lambda f: floors[f]['altitude'])
    large_floor_img = draw_floor(large_floor, floors[large_floor], rooms, description, True)
    large_w, large_h = large_floor_img.size
    small_w, small_h = large_w // 2, large_h // 2
    w = large_w + 2 * small_w
    report = draw_report_section(w, rooms, description)
    report_h = report.size[1]
    h = large_h + report_h
    img = Image.new('RGBA', (w, h), (255, 255, 255, 255))
    img.paste(report, (0, 0))
    img.paste(large_floor_img, (0, report_h))
    for i, f in zip(itertools.count(), small_floors):
        small_floor_img = draw_floor(f, floors[f], rooms, description, False)
        small_floor_img = small_floor_img.resize((small_w, small_h), Image.BICUBIC)
        img.paste(small_floor_img, (large_w + (i % 2) * small_w, report_h + (i // 2) * small_h))
    return img
    
