import os
import sys
import customtkinter as ctk
from customtkinter import filedialog
import threading

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

from photosorter.core import PhotoSorter
from photosorter.rules import SortingRules


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class PhotoSorterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Сортировщик фото")
        self.geometry("700x700")
        self.minsize(600, 550)

        self.source_path = ctk.StringVar(value="")
        self.target_path = ctk.StringVar(value="")

        self.current_plan = None

        self._create_widgets()

    def _create_widgets(self):
        folder_frame = ctk.CTkFrame(self)
        folder_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(folder_frame, text="Откуда взять фото (источник):", font=("Arial", 12, "bold")).grid(row=0,
                                                                                                          column=0,
                                                                                                          sticky="w",
                                                                                                          padx=10,
                                                                                                          pady=(10, 2))
        self.source_entry = ctk.CTkEntry(folder_frame, textvariable=self.source_path, width=450)
        self.source_entry.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        ctk.CTkButton(folder_frame, text="Обзор...", width=100, command=self.browse_source).grid(row=1, column=1,
                                                                                                 padx=10, pady=(0, 10))

        ctk.CTkLabel(folder_frame, text="Куда переместить (результат):", font=("Arial", 12, "bold")).grid(row=2,
                                                                                                          column=0,
                                                                                                          sticky="w",
                                                                                                          padx=10,
                                                                                                          pady=(5, 2))
        self.target_entry = ctk.CTkEntry(folder_frame, textvariable=self.target_path, width=450)
        self.target_entry.grid(row=3, column=0, padx=10, pady=(0, 15), sticky="ew")
        ctk.CTkButton(folder_frame, text="Обзор...", width=100, command=self.browse_target).grid(row=3, column=1,
                                                                                                 padx=10, pady=(0, 15))

        folder_frame.grid_columnconfigure(0, weight=1)

        settings_frame = ctk.CTkFrame(self)
        settings_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(settings_frame, text="Настройки сортировки:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10,
                                                                                                    pady=5)

        depth_subframe = ctk.CTkFrame(settings_frame, fg_color="transparent")
        depth_subframe.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(depth_subframe, text="Глубина структуры папок:").pack(side="left", padx=(0, 10))
        self.depth_var = ctk.StringVar(value="Год и Месяц")
        self.depth_menu = ctk.CTkOptionMenu(
            depth_subframe,
            values=["Только Год", "Год и Месяц", "Год, Месяц и День"],
            variable=self.depth_var
        )
        self.depth_menu.pack(side="left")

        self.split_media_var = ctk.BooleanVar(value=True)
        self.split_media_cb = ctk.CTkCheckBox(settings_frame, text="Разделять фото и видео по разным папкам",
                                              variable=self.split_media_var)
        self.split_media_cb.pack(anchor="w", padx=10, pady=5)

        self.screenshots_var = ctk.BooleanVar(value=True)
        self.screenshots_cb = ctk.CTkCheckBox(settings_frame, text="Отделять скриншоты в папку 'Screenshots'",
                                              variable=self.screenshots_var)
        self.screenshots_cb.pack(anchor="w", padx=10, pady=5)

        self.copy_mode_var = ctk.BooleanVar(value=True)
        self.copy_mode_cb = ctk.CTkCheckBox(settings_frame,
                                            text="Безопасный режим (копировать, а не перемещать оригиналы)",
                                            variable=self.copy_mode_var)
        self.copy_mode_cb.pack(anchor="w", padx=10, pady=(5, 10))

        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=10)

        self.preview_btn = ctk.CTkButton(buttons_frame, text="Показать превью", command=self.generate_preview,
                                         fg_color="#2c3e50", hover_color="#34495e")
        self.preview_btn.pack(side="left", expand=True, fill="x", padx=(0, 10))

        self.run_btn = ctk.CTkButton(buttons_frame, text="Запустить сортировку", command=self.run_sorting,
                                     fg_color="#27ae60", hover_color="#2ecc71")
        self.run_btn.pack(side="right", expand=True, fill="x", padx=(10, 0))

        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal")
        self.progress_bar.pack(fill="x", padx=20, pady=(10, 2))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(self, text="", font=("Arial", 11))
        self.progress_label.pack(anchor="w", padx=25, pady=(0, 5))

        preview_label_frame = ctk.CTkFrame(self, fg_color="transparent")
        preview_label_frame.pack(fill="x", padx=20)
        ctk.CTkLabel(preview_label_frame, text="План сортировки (будущая структура):", font=("Arial", 11, "bold")).pack(
            side="left")

        self.text_preview = ctk.CTkTextbox(self, font=("Courier New", 12))
        self.text_preview.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        self.text_preview.insert("0.0",
                                 "Здесь появится будущая структура папок после нажатия на кнопку 'Показать превью'.")

    def browse_source(self):
        directory = filedialog.askdirectory(title="Выберите папку с неотсортированными фото")
        if directory:
            self.source_path.set(directory)

    def browse_target(self):
        directory = filedialog.askdirectory(title="Выберите папку назначения")
        if directory:
            self.target_path.set(directory)

    def get_rules_from_gui(self) -> SortingRules:
        depth_map = {
            "Только Год": "year",
            "Год и Месяц": "year_month",
            "Год, Месяц и День": "year_month_day"
        }
        raw_depth = self.depth_var.get()
        depth_val = depth_map.get(raw_depth, "year_month")

        return SortingRules(
            depth=depth_val,
            split_media=self.split_media_var.get(),
            separate_screenshots=self.screenshots_var.get()
        )

    def _bg_generate_preview(self, src: str, dst: str) -> None:
        rules = self.get_rules_from_gui()
        sorter = PhotoSorter(source_dir=src, target_dir=dst or src, rules=rules)

        self.current_plan = sorter.scan_and_plan()

        self.text_preview.delete("0.0", "end")

        if not self.current_plan:
            self.text_preview.insert("insert", "Подходящие медиафайлы (фото/видео) в папке источника не найдены.")
        else:
            tree_text = "[Будущая структура папок]:\n"
            for target_folder, files in sorted(self.current_plan.items()):
                tree_text += f"├── {target_folder}/\n"
                for _, filename in files:
                    tree_text += f"│   └── {filename}\n"
            self.text_preview.insert("insert", tree_text)

        self.preview_btn.configure(state="normal")
        self.run_btn.configure(state="normal")
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)

    def generate_preview(self) -> None:
        src = self.source_path.get()
        dst = self.target_path.get()

        if not src or not os.path.exists(src):
            self.show_message("Ошибка", "Пожалуйста, выберите существующую папку-источник!")
            return

        self.preview_btn.configure(state="disabled")
        self.run_btn.configure(state="disabled")

        self.text_preview.delete("0.0", "end")
        self.text_preview.insert("insert",
                                 "Сканирование папки и извлечение метаданных в фоновом режиме...\nПожалуйста, подождите.")

        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        threading.Thread(target=self._bg_generate_preview, args=(src, dst), daemon=True).start()

    def _bg_run_sorting(self, src: str, dst: str) -> None:
        rules = self.get_rules_from_gui()
        sorter = PhotoSorter(source_dir=src, target_dir=dst, rules=rules)

        if not self.current_plan:
            self.current_plan = sorter.scan_and_plan()

        if not self.current_plan:
            self.show_message("Инфо", "Нечего сортировать.")
            self.preview_btn.configure(state="normal")
            self.run_btn.configure(state="normal")
            return

        copy_mode = self.copy_mode_var.get()

        def update_progress(current, total):
            percent = current / total
            self.progress_bar.set(percent)
            self.progress_label.configure(text=f"Обработано файлов: {current} из {total} ({int(percent * 100)}%)")

        try:
            sorter.execute_sorting(self.current_plan, copy_mode=copy_mode, progress_callback=update_progress)

            mode_str = "скопированы" if copy_mode else "перенесены"
            self.show_message("Успех!", f"Все файлы успешно {mode_str} в папку:\n{dst}")
            self.current_plan = None
            self.text_preview.delete("0.0", "end")
            self.text_preview.insert("0.0", "Готово! Можете выбрать новые папки.")

            self.progress_bar.set(0)
            self.progress_label.configure(text="")

        except Exception as e:
            self.show_message("Ошибка", f"Произошла ошибка при сортировке:\n{e}")
            self.progress_bar.set(0)
            self.progress_label.configure(text="")

        self.preview_btn.configure(state="normal")
        self.run_btn.configure(state="normal")

    def run_sorting(self) -> None:
        src = self.source_path.get()
        dst = self.target_path.get()

        if not src or not os.path.exists(src):
            self.show_message("Ошибка", "Выберите корректную папку-источник!")
            return
        if not dst:
            self.show_message("Ошибка", "Пожалуйста, выберите папку назначения!")
            return

        self.preview_btn.configure(state="disabled")
        self.run_btn.configure(state="disabled")

        threading.Thread(target=self._bg_run_sorting, args=(src, dst), daemon=True).start()

    def show_message(self, title: str, text: str):
        from tkinter import messagebox
        messagebox.showinfo(title, text)


if __name__ == "__main__":
    app = PhotoSorterApp()
    app.mainloop()