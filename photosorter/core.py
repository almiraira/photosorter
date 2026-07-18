import os
import shutil
from typing import Dict, List, Tuple
from photosorter.utils import get_file_date
from photosorter.rules import SortingRules


class PhotoSorter:
    def __init__(self, source_dir: str, target_dir: str, rules: SortingRules):
        self.source_dir = os.path.abspath(source_dir)
        self.target_dir = os.path.abspath(target_dir)
        self.rules = rules

        self.valid_extensions = {
            '.jpg', '.jpeg', '.png', '.heic', '.tiff', '.gif',
            '.mp4', '.mov', '.avi', '.mkv', '.3gp'
        }

    def scan_and_plan(self) -> Dict[str, List[Tuple[str, str]]]:
        plan = {}

        if not os.path.exists(self.source_dir):
            return plan

        for root, _, files in os.walk(self.source_dir):
            for file in files:
                if file.startswith('.') or file.startswith('._'):
                    continue

                _, ext = os.path.splitext(file.lower())
                if ext not in self.valid_extensions:
                    continue

                full_path = os.path.join(root, file)

                file_date = get_file_date(full_path)
                rel_target_dir = self.rules.determine_target_path(full_path, file_date)

                if rel_target_dir not in plan:
                    plan[rel_target_dir] = []

                plan[rel_target_dir].append((full_path, file))

        return plan

    def execute_sorting(self, plan: dict, copy_mode: bool = True, progress_callback=None) -> None:
        total_files = sum(len(files) for files in plan.values())
        processed_files = 0

        for rel_target_dir, files in plan.items():
            target_dir = os.path.join(self.target_dir, rel_target_dir)
            os.makedirs(target_dir, exist_ok=True)

            for full_path, filename in files:
                dest_path = os.path.join(target_dir, filename)

                if os.path.exists(dest_path):
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(target_dir, f"{base}_{counter}{ext}")
                        counter += 1

                if copy_mode:
                    shutil.copy2(full_path, dest_path)
                else:
                    shutil.move(full_path, dest_path)

                processed_files += 1
                if progress_callback:
                    progress_callback(processed_files, total_files)