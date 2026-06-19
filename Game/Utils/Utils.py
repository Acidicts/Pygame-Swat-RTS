import os
import json
import pygame
from pathlib import Path

BASE_PATH = str(Path(__file__).resolve().parent.parent)
BASE_IMG_PATH = str(Path(BASE_PATH) / 'Assets' / 'Images')

zIndex = {
    "Floors": 0,
    "Walls": 1,
    "GroundFurniture": 2,
    "Characters": 3,
    "Bullets": 4,
    "StandingFurniture": 5
}

penetration_levels = {
    "Wood": 1,
    "Metal": 3,
    "Concrete": 8
}

characterColours = {
    "Squad" : (0, 0, 200),
    "Commander" : (200, 200, 0),
    "Enemy" : (200, 10, 10)
}


def json_to_dict(file_path):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("JSON content is not a dictionary.")

    return data


def load_image(path):
    img = pygame.image.load(os.path.join(BASE_IMG_PATH, path)).convert()
    img.set_colorkey((0, 0, 0))
    if "icon_" in path:
        img = pygame.transform.scale(img, (16, 16))
    return img


def load_images(path):
    images = []
    for img_name in os.listdir(os.path.join(BASE_IMG_PATH, path)):
        images.append(load_image(os.path.join(path, str(img_name))))
    return images


def scale(img, s=(1, 1), smooth=False):
    if isinstance(s, (int, float)):
        s = (s, s)
    w, h = img.get_size()
    scaler = pygame.transform.smoothscale if smooth else pygame.transform.scale
    return scaler(img, (w * s[0], h * s[1]))

def scale_to(img, s=(1, 1)):
    return pygame.transform.scale(img, s)


def create_character(colour):
    img = pygame.Surface((256, 256))
    pygame.draw.aacircle(img, colour, img.get_rect().center, 128, 8)
    pygame.draw.aacircle(img, colour, img.get_rect().center, 100)

    return img
