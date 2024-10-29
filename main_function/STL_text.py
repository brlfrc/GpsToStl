from PIL import Image, ImageDraw, ImageFont

from main_function.STL_function import numpy2stl


def generate_text_image(text, font = "arial.ttf",  font_size=50, padding=20):
    """
    Genera un'immagine in scala di grigi del testo fornito.
    :param text: Il testo da visualizzare.
    :param font_size: La dimensione del font.
    :return: Immagine del testo in scala di grigi.
    """
    font = ImageFont.truetype(font, font_size)

    dummy_image = Image.new('L', (1, 1), color=0)
    draw = ImageDraw.Draw(dummy_image)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

    image_width = text_width + padding * 2
    image_height = text_height + padding * 2

    image = Image.new('L', (image_width, image_height), color=0)
    draw = ImageDraw.Draw(image)
    
    draw.text((padding, padding), text, font=font, fill=255)

    return image



def generate_text_STL (text= 'Example 1', font = "arial.ttf",  font_size=50 ):
    text_image = generate_text_image(text, font,  font_size)

    return numpy2stl(text_image, scale=5, solid=True)