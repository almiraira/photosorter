import os
import re
from datetime import datetime
from exif import Image


def get_exif_date(file_path: str) -> datetime | None:
    try:
        with open(file_path, 'rb') as image_file:
            my_image = Image(image_file)

            if my_image.has_exif:
                if hasattr(my_image, 'datetime_original'):
                    raw_date = my_image.datetime_original
                    return datetime.strptime(raw_date.strip(), "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None


def parse_date_from_filename(filename: str) -> datetime | None:
    patterns = [
        r'(\d{4})[-_]?(\d{2})[-_]?(\d{2})',
    ]
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                year, month, day = map(int, match.groups())
                return datetime(year, month, day)
            except ValueError:
                continue
    return None


def get_file_date(file_path: str) -> datetime:
    ext = os.path.splitext(file_path.lower())[1]

    if ext in ('.jpg', '.jpeg'):
        exif_date = get_exif_date(file_path)
        if exif_date:
            return exif_date

    filename = os.path.basename(file_path)
    filename_date = parse_date_from_filename(filename)
    if filename_date:
        return filename_date

    mtime = os.path.getmtime(file_path)
    return datetime.fromtimestamp(mtime)