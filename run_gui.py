import os
import sys
import customtkinter as ctk
from customtkinter import filedialog
import threading
from PIL import Image, ImageTk
import platform
from tkinter import messagebox
from photosorter.core import PhotoSorter
from photosorter.rules import SortingRules


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)



ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class PreviewWindow(ctk.CTkToplevel):
    def __init__(self, parent, current_plan, on_exclude_callback):
        super().__init__(parent)

        self.parent = parent
        self.current_plan = current_plan
        self.on_exclude_callback = on_exclude_callback

        self.title("Предварительный просмотр")
        self.geometry("800x700")
        self.minsize(600, 500)

        self.preview_queue = []
        self.items_per_page = 100

        self.folder_widgets = {}

        self.tooltip = None
        self.tooltip_image = None

        self._create_widgets()
        self._prepare_queue()

        self.lift()
        self.focus_set()

    def _create_widgets(self):
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            info_frame,
            text="Наведите мышку на имя файла, чтобы увидеть превью. Нажмите ✕, чтобы исключить.",
            font=("Arial", 12, "italic")
        ).pack(side="left")

        self.scroll_preview = ctk.CTkScrollableFrame(self, label_text="Предварительный просмотр дерева папок")
        self.scroll_preview.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._bind_mouse_wheel(self.scroll_preview)

    def _prepare_queue(self):
        if not self.current_plan:
            lbl = ctk.CTkLabel(self.scroll_preview, text="План пуст или подходящие файлы не найдены.",
                               text_color="orange")
            lbl.pack(pady=20)
            return

        for target_folder, files in sorted(self.current_plan.items()):
            self.preview_queue.append(("folder", target_folder))
            for full_path, filename in files:
                self.preview_queue.append(("file", (target_folder, full_path, filename)))

        self.render_next_page()

    def render_next_page(self):
        for widget in self.scroll_preview.winfo_children():
            if getattr(widget, "is_load_more_btn", False):
                widget.destroy()

        if not self.preview_queue:
            return

        chunk = [self.preview_queue.pop(0) for _ in range(self.items_per_page) if self.preview_queue]

        for item_type, data in chunk:
            if item_type == "folder":
                folder_lbl = ctk.CTkLabel(
                    self.scroll_preview,
                    text=f"📁 {data}/",
                    font=("Arial", 13, "bold"),
                    text_color="#3498db"
                )
                folder_lbl.pack(anchor="w", padx=5, pady=(10, 2))
                self.folder_widgets[data] = folder_lbl

            elif item_type == "file":
                target_folder, full_path, filename = data

                item_frame = ctk.CTkFrame(self.scroll_preview, fg_color="transparent")
                item_frame.pack(fill="x", padx=20, pady=2)

                file_lbl = ctk.CTkLabel(item_frame, text=f"└── {filename}", font=("Courier New", 12), cursor="hand2")
                file_lbl.pack(side="left", padx=5)

                file_lbl.bind("<Enter>", lambda event, p=full_path: self.show_image_tooltip(event, p))
                file_lbl.bind("<Leave>", self.hide_image_tooltip)
                file_lbl.bind("<Motion>", self.move_image_tooltip)

                remove_btn = ctk.CTkButton(
                    item_frame,
                    text="✕",
                    width=20,
                    height=20,
                    fg_color="#e74c3c",
                    hover_color="#c0392b",
                    command=lambda p=full_path, f=filename, fol=target_folder, fr=item_frame: self.exclude_file(fol, p,
                                                                                                                f, fr)
                )
                remove_btn.pack(side="right", padx=10)

        if self.preview_queue:
            load_more_btn = ctk.CTkButton(
                self.scroll_preview,
                text=f"Показать еще ({len(self.preview_queue)} файлов осталось)...",
                fg_color="#34495e",
                hover_color="#2c3e50",
                command=self.render_next_page
            )
            load_more_btn.is_load_more_btn = True
            load_more_btn.pack(fill="x", padx=20, pady=15)

        self._bind_mouse_wheel(self.scroll_preview)

    def exclude_file(self, folder, full_path, filename, frame_widget):
        self.hide_image_tooltip(None)

        self.on_exclude_callback(folder, full_path, filename)

        frame_widget.destroy()

        if folder not in self.parent.current_plan:
            if folder in self.folder_widgets:
                self.folder_widgets[folder].destroy()
                del self.folder_widgets[folder]


    def show_image_tooltip(self, event, file_path):
        if self.tooltip:
            self.tooltip.destroy()

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ('.jpg', '.jpeg', '.png', '.bmp', '.webp'):
            return

        try:
            raw_img = Image.open(file_path)

            self.tooltip_image = ctk.CTkImage(light_image=raw_img, size=(200, 200))

            self.tooltip = ctk.CTkToplevel(self)
            self.tooltip.overrideredirect(True)

            lbl = ctk.CTkLabel(self.tooltip, image=self.tooltip_image, text="")
            lbl.pack(padx=3, pady=3)

            self.move_image_tooltip(event)

        except Exception as e:
            print(f"Ошибка чтения миниатюры {file_path}: {e}")
            if self.tooltip:
                self.tooltip.destroy()
                self.tooltip = None

    def move_image_tooltip(self, event):
        if self.tooltip:
            x = event.x_root + 20
            y = event.y_root + 20
            self.tooltip.geometry(f"+{x}+{y}")

    def hide_image_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
            self.tooltip_image = None

    def _bind_mouse_wheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mouse_wheel)
        for child in widget.winfo_children():
            self._bind_mouse_wheel(child)

    def _on_mouse_wheel(self, event):
        self.scroll_preview._canvas.yview_scroll(int(-1 * event.delta), "units")


class PhotoSorterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Сортировщик фото")
        self.geometry("650x420")
        self.minsize(600, 420)

        self.source_path = ctk.StringVar(value="")
        self.target_path = ctk.StringVar(value="")
        self.current_plan = None
        self.preview_window = None

        icon_png_path = os.path.join(BASE_DIR, "icon.png")
        icon_ico_path = os.path.join(BASE_DIR, "icon.ico")

        if platform.system() == "Windows":
            if os.path.exists(icon_ico_path):
                self.iconbitmap(icon_ico_path)
        else:
            if os.path.exists(icon_png_path):
                img = ctk.CTkImage(light_image=Image.open(icon_png_path))
                img_tk = ImageTk.PhotoImage(Image.open(icon_png_path))
                self.wm_iconphoto(False, img_tk)

        self._create_widgets()

    def _create_widgets(self):
        folder_frame = ctk.CTkFrame(self)
        folder_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(folder_frame, text="Откуда взять фото (источник):", font=("Arial", 12, "bold")).grid(row=0,
                                                                                                          column=0,
                                                                                                          sticky="w",
                                                                                                          padx=10,
                                                                                                          pady=(10, 2))
        self.source_entry = ctk.CTkEntry(folder_frame, textvariable=self.source_path, width=420)
        self.source_entry.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        ctk.CTkButton(folder_frame, text="Обзор...", width=100, command=self.browse_source).grid(row=1, column=1,
                                                                                                 padx=10, pady=(0, 10))

        ctk.CTkLabel(folder_frame, text="Куда переместить результат:", font=("Arial", 12, "bold")).grid(row=2,
                                                                                                          column=0,
                                                                                                          sticky="w",
                                                                                                          padx=10,
                                                                                                          pady=(5, 2))
        self.target_entry = ctk.CTkEntry(folder_frame, textvariable=self.target_path, width=420)
        self.target_entry.grid(row=3, column=0, padx=10, pady=(0, 15), sticky="ew")
        ctk.CTkButton(folder_frame, text="Обзор...", width=100, command=self.browse_target).grid(row=3, column=1,
                                                                                                 padx=10, pady=(0, 15))

        folder_frame.grid_columnconfigure(0, weight=1)

        settings_frame = ctk.CTkFrame(self)
        settings_frame.pack(fill="x", padx=20, pady=5)

        depth_subframe = ctk.CTkFrame(settings_frame, fg_color="transparent")
        depth_subframe.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(depth_subframe, text="Глубина структуры папок:", font=("Arial", 11, "bold")).pack(side="left",
                                                                                                       padx=(0, 10))
        self.depth_var = ctk.StringVar(value="Год и Месяц")
        self.depth_menu = ctk.CTkOptionMenu(
            depth_subframe,
            values=["Только Год", "Год и Месяц", "Год, Месяц и День"],
            variable=self.depth_var
        )
        self.depth_menu.pack(side="left")

        self.split_media_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(settings_frame, text="Разделять фото и видео по разным папкам",
                        variable=self.split_media_var).pack(anchor="w", padx=10, pady=4)

        self.screenshots_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(settings_frame, text="Отделять скриншоты в папку 'Screenshots'",
                        variable=self.screenshots_var).pack(anchor="w", padx=10, pady=4)

        self.copy_mode_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(settings_frame, text="Безопасный режим (копировать, а не перемещать)",
                        variable=self.copy_mode_var).pack(anchor="w", padx=10, pady=(4, 10))

        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=15)

        self.preview_btn = ctk.CTkButton(buttons_frame, text="Открыть предпросмотр", command=self.generate_preview,
                                         fg_color="#2c3e50", hover_color="#34495e")
        self.preview_btn.pack(side="left", expand=True, fill="x", padx=(0, 10))

        self.run_btn = ctk.CTkButton(buttons_frame, text="Запустить сортировку", command=self.run_sorting,
                                     fg_color="#27ae60", hover_color="#2ecc71")
        self.run_btn.pack(side="right", expand=True, fill="x", padx=(10, 0))

        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal")
        self.progress_bar.pack(fill="x", padx=20, pady=(5, 2))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(self, text="", font=("Arial", 11))
        self.progress_label.pack(anchor="w", padx=25, pady=(0, 10))

    def browse_source(self):
        directory = filedialog.askdirectory(title="Выберите папку с фото")
        if directory: self.source_path.set(directory)

    def browse_target(self):
        directory = filedialog.askdirectory(title="Выберите папку назначения")
        if directory: self.target_path.set(directory)

    def get_rules_from_gui(self) -> SortingRules:
        depth_map = {"Только Год": "year", "Год и Месяц": "year_month",
                     "Год, Месяц и День": "year_month_day"}
        return SortingRules(
            depth=depth_map.get(self.depth_var.get(), "year_month"),
            split_media=self.split_media_var.get(),
            separate_screenshots=self.screenshots_var.get()
        )

    def exclude_file_from_plan(self, folder: str, full_path: str, filename: str) -> None:
        if self.current_plan and folder in self.current_plan:
            self.current_plan[folder] = [item for item in self.current_plan[folder] if item[0] != full_path]
            if not self.current_plan[folder]:
                del self.current_plan[folder]

    def _bg_generate_preview(self, src: str, dst: str) -> None:
        rules = self.get_rules_from_gui()
        sorter = PhotoSorter(source_dir=src, target_dir=dst or src, rules=rules)
        self.current_plan = sorter.scan_and_plan()

        if self.preview_window and self.preview_window.winfo_exists():
            self.preview_window.destroy()

        self.preview_window = PreviewWindow(
            parent=self,
            current_plan=self.current_plan,
            on_exclude_callback=self.exclude_file_from_plan
        )

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
            if self.preview_window and self.preview_window.winfo_exists():
                self.preview_window.destroy()

            sorter.execute_sorting(self.current_plan, copy_mode=copy_mode, progress_callback=update_progress)

            mode_str = "скопированы" if copy_mode else "перенесены"
            self.show_message("Успех!", f"Все файлы успешно {mode_str} в папку:\n{dst}")
            self.current_plan = None
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
        messagebox.showinfo(title, text)


if __name__ == "__main__":
    app = PhotoSorterApp()
    app.mainloop()