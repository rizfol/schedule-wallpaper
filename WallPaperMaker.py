import cv2
import numpy as np
import pymupdf
import os
from dotenv import load_dotenv, dotenv_values
from PIL import Image

def convert_pdf_to_png(pdf_path):
    doc = pymupdf.open(pdf_path) # open a document
    for page in doc: # iterate the document pages
        pix = page.get_pixmap(dpi=250)
        pix.save(pdf_path[:len(pdf_path)-3]+"png")

def sort_contours(cnts, method="left-to-right"):
    # initialize the reverse flag and sort index
    reverse = False
    i = 0

    # handle if we need to sort in reverse
    if method == "right-to-left" or method == "bottom-to-top":
        reverse = True

    # handle if we are sorting against the y-coordinate rather than
    # the x-coordinate of the bounding box
    if method == "top-to-bottom" or method == "bottom-to-top":
        i = 1

    # construct the list of bounding boxes and sort them from top to
    # bottom
    boundingBoxes = [cv2.boundingRect(c) for c in cnts]
    (cnts, boundingBoxes) = zip(*sorted(zip(cnts, boundingBoxes),
                                        key=lambda b: b[1][i], reverse=reverse))

    # return the list of sorted contours and bounding boxes
    return (cnts, boundingBoxes)


#Functon for extracting the box
def box_extraction(img_for_box_extraction_path, cropped_dir_path):

    print("Reading image..")
    img = cv2.imread(img_for_box_extraction_path)  # Read the image

    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    (thresh, img_bin) = cv2.threshold(img_gray, 230, 255,
                                      cv2.THRESH_BINARY)  # Thresholding the image
    img_bin = 255-img_bin  # Invert the image

    print("Storing binary image to Images/Image_bin.jpg..")
    cv2.imwrite("Images/Image_bin.jpg",img_bin)

    print("Applying Morphological Operations..")
    # Defining a kernel length
    kernel_length = np.array(img_gray).shape[1]//40
     
    # A verticle kernel of (1 X kernel_length), which will detect all the verticle lines from the image.
    verticle_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_length))
    # A horizontal kernel of (kernel_length X 1), which will help to detect all the horizontal line from the image.
    hori_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length, 1))
    # A kernel of (3 X 3) ones.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    # Morphological operation to detect verticle lines from an image
    img_temp1 = cv2.erode(img_bin, verticle_kernel, iterations=3)
    verticle_lines_img = cv2.dilate(img_temp1, verticle_kernel, iterations=3)
    cv2.imwrite("Images/verticle_lines.jpg",verticle_lines_img)

    # Morphological operation to detect horizontal lines from an image
    img_temp2 = cv2.erode(img_bin, hori_kernel, iterations=3)
    horizontal_lines_img = cv2.dilate(img_temp2, hori_kernel, iterations=3)
     # Find contours of the horizontal lines
    contours, _ = cv2.findContours(horizontal_lines_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Sort contours by y-coordinate to identify top and bottom lines
    sorted_contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])

    # Create a mask to keep only the topmost and bottommost lines
    mask = np.zeros_like(horizontal_lines_img)
    if len(sorted_contours) >= 2:
        cv2.drawContours(mask, [sorted_contours[0]], -1, 255, thickness=cv2.FILLED)  # Topmost line
        cv2.drawContours(mask, [sorted_contours[-1]], -1, 255, thickness=cv2.FILLED)  # Bottommost line
    elif len(sorted_contours) == 1:
        cv2.drawContours(mask, [sorted_contours[0]], -1, 255, thickness=cv2.FILLED)  # Only one line

    # Apply the mask to keep only top and bottom lines
    filtered_horizontal_lines_img = cv2.bitwise_and(horizontal_lines_img, mask)
    cv2.imwrite("Images/filtered_horizontal_lines.jpg", filtered_horizontal_lines_img)
    # cv2.imwrite("Images/horizontal_lines.jpg",horizontal_lines_img)

    # Weighting parameters, this will decide the quantity of an image to be added to make a new image.
    alpha = 0.5
    beta = 1.0 - alpha
    # This function helps to add two image with specific weight parameter to get a third image as summation of two image.
    img_final_bin = cv2.addWeighted(verticle_lines_img, alpha, filtered_horizontal_lines_img, beta, 0.0)
    img_final_bin = cv2.erode(~img_final_bin, kernel, iterations=2)
    (thresh, img_final_bin) = cv2.threshold(img_final_bin, 128, 255, cv2.THRESH_BINARY)

    # For Debugging
    # Enable this line to see verticle and horizontal lines in the image which is used to find boxes
    print("Binary image which only contains boxes: Images/img_final_bin.jpg")
    cv2.imwrite("Images/img_final_bin.jpg",img_final_bin)
    # Find contours for image, which will detect all the boxes
    contours, hierarchy = cv2.findContours(
        img_final_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # Sort all the contours by top to bottom.
    (contours, boundingBoxes) = sort_contours(contours, method="top-to-bottom")

    print("Output stored in Output directiory!")

    idx = 0
    for c in contours:
        # Returns the location and width,height for every contour
        x, y, w, h = cv2.boundingRect(c)

        # Expand the bounding box slightly to include the black lines
        pad = 4  # Padding size

        x = max(0, x - pad)
        y = max(0, y - pad)
        w = min(img.shape[1] - x, w + 2 * pad)
        h = min(img.shape[0] - y, h + 2 * pad)
 
        if (w < 400 and h > 850):
            idx += 1
            new_img = img[y:y+h, x:x+w]
            cv2.imwrite(cropped_dir_path+str(idx) + '.png', new_img)

    # For Debugging
    # Enable this line to see all contours.
    # cv2.drawContours(img, contours, -1, (0, 0, 255), 3)
    # cv2.imwrite("./Temp/img_contour.jpg", img)

#Input image path and out folder
load_dotenv()

file_path = os.getenv("FILE_PATH")
convert_pdf_to_png(file_path+".pdf")
box_extraction(file_path+".png", "Output/")

width = int(os.getenv("SCREEN_WIDTH"))
height = int(os.getenv("SCREEN_HEIGHT"))

# joins the extracted images together
idx = 0
my_list = os.listdir("Output")
my_list.sort()
my_list.pop(0)
# putting Output/ in front makes it so that Image.open has the correct relative path
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
