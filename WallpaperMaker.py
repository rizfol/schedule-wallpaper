import os
from PIL import Image
import sys

# joins the extracted images together
idx = 0
my_list = os.listdir("Output")
my_list.sort()
my_list.pop(0)
my_list = [f"Output/{i}" for i in my_list]
print(my_list)

images = [Image.open(x) for x in my_list]

times_widths, times_heights = images[-1].size[0], images[-1].size[1]


for im in images[:-1]:
    idx += 1
    new_im = Image.new("RGB", (times_widths + im.size[0], times_heights))
    new_im.paste(images[-1], (0, 0))
    new_im.paste(im, (times_widths,0))
    new_im.save(f'Joined/{idx}.png', format="PNG")

