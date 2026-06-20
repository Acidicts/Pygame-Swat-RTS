
class Sprite:
    def __init__(self, img, x, y, z_level=0):
        self.rect = img.get_rect(topleft=(x, y))
        self.img = img
        self.x = x
        self.y = y
        self.z_level = z_level

    def draw(self, surf):
        surf.blit(self.img, (self.x, self.y))

    def update(self, dt):
        self.rect = self.img.get_rect()
        self.rect.topleft = (self.x, self.y)

    def destroy(self):
        del self
