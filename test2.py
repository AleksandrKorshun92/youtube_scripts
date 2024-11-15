""" Программа для скачивания видео с YouTube по ссылки. 
Видео сохраняется в 

"""


import tkinter as tk
import yt_dlp as youtube_dl
from tkinter import messagebox
from tkinter import ttk


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Youtube")
        self.geometry("700x350")
        self.config(bg='#50b5e8')
        self.lb = tk.Label(self, text="Загрузчик видео с YouTube", font=('Raleway', 25, 'bold'), bg='#50b5e8', justify='center')
        self.lb.pack(pady=15)

        self.lb2 = tk.Label(self, text="Ссылка для скачивания видео:", font=('Arvo', 15, 'bold'), bg='#50b5e8', justify='center')
        self.lb2.pack(pady=10)

        # Поле для ввода ссылки
        self.link2 = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.link2, width=70, justify='center')
        self.entry.pack(pady=5)
        
        # Поле для ввода названия файла
        self.link3 = tk.StringVar()
        self.entry3 = tk.Entry(self, textvariable=self.link3, width=70, justify='center')
        self.entry3.pack(pady=10)
        
        # Кнопка для начала скачивания видео
        self.load_button = tk.Button(self, text="Скачать", justify='center', command=self.on_load_clicked)
        self.load_button.pack(pady=15)
        
        # Кнопка закрытия окна
        close_button = tk.Button(self, text="Закрыть", command=self.destroy)
        close_button.pack(pady=10)

    def on_load_clicked(self):
        url = self.entry.get()
        if not url.startswith('http') or 'youtube' not in url.lower():
            messagebox.showerror("Ошибка", "Некорректная ссылка на YouTube")
            return

        # Создаем новое окно для отображения прогресса
        self.progress_window = ProgressWindow()
 # Обнуляем прогресс
        
        name_file = self.entry3.get()
        ydl_opts = {
            'format': 'best',
            'outtmpl': name_file+'.%(ext)s',
            'progress_hooks': [self.progress_window.update_progress]
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([url])
            finally:
                self.progress_window.finished()

        # result = "Загрузка завершена"
        # ResultWindow(result)
        
    def close_progress_window(self):
        self.progress_window.destroy()


class ProgressWindow(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("Загрузка")
        self.geometry("400x200")
        self.config(bg='#50b5e8')

        # Создаем полосу прогресса
        self.progress = ttk.Progressbar(self, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=40)

        # Подпись для отображения процентов
        self.percent_label = tk.Label(self, text="0% завершено", font=('Arvo', 12, 'bold'), bg='#50b5e8')
        self.percent_label.pack()

        # Кнопка остановки загрузки
        self.stop_button = tk.Button(self, text="Остановить", command=self.stop_download)
        self.stop_button.pack(pady=10)
        
        # Прерывание, если окно закрыто
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.is_downloading = True  # Флаг для контроля загрузки

    def update_progress(self, d):
        if 'status' in d:
            if d['status'] == 'downloading':
                if 'downloaded_bytes' in d and 'total_bytes' in d:
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                    self.progress['value'] = percent
                    self.percent_label['text'] = f"{int(percent)}% завершено"
                    self.update_idletasks()

    def finished(self):
        self.is_downloading = False
        self.progress['value'] = 100  # Устанавливаем полосу в 100%, когда загрузка завершена
        self.percent_label['text'] = "Загрузка завершена!"
        self.update_idletasks()
        messagebox.showinfo("Готово", "Загрузка завершена!")

    def stop_download(self):
        self.is_downloading = False
        messagebox.showinfo("Остановлено", "Загрузка остановлена!")
        self.destroy()

    def on_closing(self):
        self.destroy()


class ResultWindow(tk.Toplevel):
    def __init__(self, results):
        super().__init__()
        self.title("Результаты скачивания")
        self.geometry("700x350")
        self.config(bg='#50b5e8')

        # Отображение результатов поиска
        result_label = tk.Label(self, text=results, wraplength=350, justify='left')
        result_label.pack(padx=20, pady=20)

        # Кнопка закрытия окна
        close_button = tk.Button(self, text="Закрыть", command=self.destroy)
        close_button.pack(pady=10)


if __name__ == '__main__':
    app = MainWindow()
    app.mainloop()