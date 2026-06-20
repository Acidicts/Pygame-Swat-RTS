
class SpriteGroup:
    def __init__(self):
        self.sprites = {}

    def add(self, sprite):
        self.sprites[str(len(self.sprites))] = sprite

    def remove(self, sprite):
        del self.sprites[str(len(self.sprites))]

    def draw(self, surface):
        for sprite in sorted(self.sprites.values(), key=lambda s: s.z_level):
            sprite.draw(surface)

    def update(self, dt):
        for sprite in list(self.sprites.values()):
            sprite.update(dt)

    def clear(self):
        self.sprites = {}
