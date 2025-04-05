import os

from django.core.exceptions import ValidationError
from PIL import Image


def validate_icon_image_size(image):
    if image:
        with Image.open(image) as img:
            if img.width > 70 or img.height > 70:
                raise ValidationError(
                    f"THe maximum allowed dimentions for the image are 70*70 - size of image you uploaded:{img.size}"
                )


def validate_image_file_exstention(value):
    ext = os.path.splitext(value.name)[1]
    valid_exts = [".jpg", ".jpeg", ".png", ".gif", ".webp"]

    if not ext.lower() in valid_exts:
        raise ValidationError("Unsupported file exstention")
