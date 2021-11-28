import imghdr
from pathlib import Path

from PIL import Image

from modules import date_utils

IMAGES_PATH = 'images/'
THUMBNAIL_PATH = 'images/thumbnails/'
THUMBNAIL_DIM = 128
EXIF_MAKER = 271
EXIF_MODEL = 272
EXIF_CREATION_DATE = 306

def _image_size_to_str(raw_size):
    pointer = 0
    while raw_size // 1024 >= 1:
        raw_size = raw_size / 1024
        pointer += 1
    size_map = {0:'B', 1:'KB', 2:'MB', 4:'GB'}
    return f'{raw_size:.2f}'.rstrip('0').rstrip('.') + f' {size_map.get(pointer)}'

def db_data_to_html_template(image_data):
    for row in image_data:
        row['file_size'] = _image_size_to_str(row['file_size'])
        row['file_path'] = (IMAGES_PATH + row['file_name'])
        row['creation_date'] = date_utils.datetime_output(row['creation_date'])
        row['upload_date'] = date_utils.datetime_output(row['upload_date'])
        if row['thumbnail']:
            row['thumbnail_path'] = (THUMBNAIL_PATH + row['file_name'])
        else:
            row['thumbnail_path'] = row['file_path']
    return image_data

def valid_image_type(image_as_bytes):
    return imghdr.what(None, image_as_bytes)

def get_dot_type(image_as_bytes):
    return '.' + imghdr.what(None, image_as_bytes)

def save_image(data, filename):
        if not Path(THUMBNAIL_PATH).exists():
            Path(THUMBNAIL_PATH).mkdir(parents=True, exist_ok=True)
        with open(Path(IMAGES_PATH, filename), "w+b") as image:
            image.write(data)
        return Path(IMAGES_PATH, filename).stat().st_size

def get_exif_params(filename):
    with Image.open(Path(IMAGES_PATH, filename)) as image:
        image_exif = image.getexif()
        if image_exif is None : image_exif = {}
        d = dict(image_exif.items())
        output = {
            'maker' : d.get(EXIF_MAKER),
            'model' : d.get(EXIF_MODEL),
            'creation_date' : date_utils.str_to_datetime(d.get(EXIF_CREATION_DATE), '%Y:%m:%d %H:%M:%S')
        }
        return output

def create_thumbnail(filename):
    with Image.open(Path(IMAGES_PATH, filename)) as image:
        width, height = image.size
        if width > THUMBNAIL_DIM and height > THUMBNAIL_DIM:
            image.thumbnail((THUMBNAIL_DIM,THUMBNAIL_DIM))
            image.save(Path(THUMBNAIL_PATH, filename))
            return True
        return False

def delete_image(filename, thumbnail_flag):
    if thumbnail_flag:
        Path(THUMBNAIL_PATH, filename).unlink()
    Path(IMAGES_PATH, filename).unlink()