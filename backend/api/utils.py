import base64

from django.core.files.base import ContentFile


def decode_img(img_data, user):
    format, imgstr = img_data.split(';base64,')
    ext = format.split('/')[-1]
    file_name = f'img_{user.id}.{ext}'
    file_content = ContentFile(base64.b64decode(imgstr), name=file_name)
    return file_name, file_content
