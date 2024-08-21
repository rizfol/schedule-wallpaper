import os
from PIL import Image
import sys
from dotenv import load_dotenv, dotenv_values

load_dotenv()
width = int(os.getenv("SCREEN_WIDTH"))
height = int(os.getenv("SCREEN_HEIGHT"))

# joins the extracted images together
idx = 0
my_list = os.listdir("Output")
my_list.sort()
my_list.pop(0)
my_list = [f"Output/{i}" for i in my_list]

images = [Image.open(x) for x in my_list]

times_widths, times_heights = images[-1].size[0], images[-1].size[1]


for im in images[:-1]:
    idx += 1
    new_im_width = times_widths + im.size[0]
    new_im = Image.new("RGB", (new_im_width, times_heights))
    new_im.paste(images[-1], (0, 0))
    new_im.paste(im, (times_widths,0))
    # new_im.save(f'Joined/{idx}.png', format="PNG")
    background = Image.new('RGBA', (width, height), (255, 255, 255, 255))
    offset = (int(round(((width - new_im_width) / 2), 0)), int(round(((height - times_heights)/2) + int(0.05 * height), 0)))
    background.paste(new_im, offset)
    background.save(f'Joined/{idx}.png', format="PNG")
