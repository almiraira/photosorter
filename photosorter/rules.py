import os
from datetime import datetime

RU_MONTHS = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь",
    7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

class SortingRules:
    def __init__(
            self,
            depth: str = "year_month",
            split_media: bool = True,
            separate_screenshots: bool = True
    ):
        self.depth = depth
        self.split_media = split_media
        self.separate_screenshots = separate_screenshots

    def is_video(self, file_path: str) -> bool:
        ext = os.path.splitext(file_path.lower())[1]
        return ext in ('.mp4', '.mov', '.avi', '.mkv', '.3gp')

    def is_screenshot(self, file_path: str) -> bool:
        name = os.path.basename(file_path).lower()
        return "screenshot" in name or "скриншот" in name or "screen shot" in name

    def determine_target_path(self, file_path: str, file_date: datetime) -> str:
        parts = []

        if self.separate_screenshots and self.is_screenshot(file_path):
            parts.append("Screenshots")
            parts.append(file_date.strftime("%Y"))
            return os.path.join(*parts)

        if self.split_media:
            parts.append("Видео" if self.is_video(file_path) else "Фото")

        if self.depth in ("year", "year_month", "year_month_day"):
            parts.append(file_date.strftime("%Y"))

        month_num = file_date.month
        month_ru = RU_MONTHS[month_num]

        if self.depth in ("year_month", "year_month_day"):
            parts.append(f"{month_num:02d}-{month_ru}")

        if self.depth == "year_month_day":
            parts.append(file_date.strftime("%d.%m.%Y"))

        return os.path.join(*parts)