import itertools
import random
from PIL import Image
import cassiopeia as cass
# import settings

OUTLINE = 10
CHAMPS = 3

with open("apikey.txt") as f:
    cass.set_riot_api_key(f.read())
cass.set_default_region("EUW")
# cass.apply_settings(settings.sd)


class LazyImage:
    def __init__(self):
        self.to_draw = []
        self.width = 0
        self.height = 0
        self.mode = None

    def paste(self, img, pos):
        self.to_draw.append([img, pos])
        if self.mode is None:
            self.mode = img.mode
        self.width = max(self.width, pos[0] + img.width)
        self.height = max(self.height, pos[1] + img.height)

    def draw(self, color=0, outline=0):
        out_img = Image.new(self.mode, (self.width + outline * 2, self.height + outline * 2), color)
        for img, pos in self.to_draw:
            out_img.paste(img, (pos[0] + outline, pos[1] + outline))
        return out_img


class StitchImage(LazyImage):
    def add_right(self, img):
        self.paste(img, (self.width, 0))

    def add_gap_right(self, width):
        self.width += width

    def add_below(self, img):
        self.paste(img, (0, self.height))

    def add_gap_below(self, height):
        self.height += height


def side(players, banned, color):
    champs = []
    images_by_player = []
    icons = []
    # collect
    for player in players:
        s = cass.get_summoner(name=player)
        champs.append([c.champion for c in s.champion_masteries
                       if c.level > 0 and c.champion.name.lower() not in banned])
        images_by_player.append([])
        icons.append(s.profile_icon.image)
    # choose
    chosen = set()
    for i in range(len(champs) * 3):
        choices, out = champs[i % len(champs)], images_by_player[i % len(champs)]
        choice = random.choice([c for c in choices if c not in chosen])
        chosen.add(choice)
        out.append(choice.image.image)
    # resize
    all_images = list(itertools.chain(itertools.chain.from_iterable(images_by_player), icons))
    size = (min(i.width for i in all_images),
            min(i.height for i in all_images))
    for image in all_images:
        if image.size != size:
            image.thumbnail(size)
    # draw
    out_img = StitchImage()
    for images, icon in zip(images_by_player, icons):
        strip = StitchImage()
        strip.add_below(icon)
        strip.add_gap_below(OUTLINE)
        for img in images:
            strip.add_below(img)
        out_img.add_right(strip.draw(color))

    return out_img.draw(color, OUTLINE)


def make_image(blue_team, red_team, banned):
    both_img = StitchImage()
    print("---Blue team---")
    both_img.add_right(side(blue_team, banned, "DeepSkyBlue"))
    print("---Red team---")
    both_img.add_right(side(red_team, banned, "DarkRed"))
    out = both_img.draw()
    out.save("out.png")
    out.show()


def get_teams():
    blue_team = []
    red_team = []
    banned = set()
    with open("players.txt", encoding="utf-8") as f:
        for line in f:
            player, champ, team = line.strip().split("|")
            if team == "b":
                blue_team.append(player)
            elif team == "r":
                red_team.append(player)
            else:
                continue
            banned.add(champ.lower())
    return blue_team, red_team, banned


def main():
    while True:
        make_image(*get_teams())
        if input("Again? (y/n): ") != "y":
            break


if __name__ == '__main__':
    main()
