import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import DND_FILES

class MainView:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.languages = {
            "vi": {
                "title": "Audio Editor - Inspired by VocalRemover",
                "status": "Vui lòng tải file âm thanh",
                "language": "Ngôn ngữ:",
                "load": "Tải âm thanh",
                "format": "Định dạng:",
                "export": "Xuất âm thanh",
                "cut": "Cắt (giây):",
                "apply_cut": "Áp dụng cắt",
                "volume": "Âm lượng (dB):",
                "speed": "Tốc độ:",
                "pitch": "Cao độ (semitones):",
                "apply": "Áp dụng tất cả",
                "reverb": "Thêm Reverb",
                "echo": "Thêm Echo",
                "fade": "Fade In/Out",
                "eq": "Equalizer",
                "vocal": "Tách giọng hát",
                "preview": "Nghe thử",
                "stop": "Dừng",
                "undo": "Undo",
                "redo": "Redo",
                "control_frame": "Điều khiển âm thanh",
                "waveform": "Dạng sóng",
                "file_info": "Thông tin file: Chưa tải file",
                "timeline": "Thanh thời gian:",
                "bass": "Bass:",
                "mid": "Mid:",
                "treble": "Treble:"
            },
            "en": {
                "title": "Audio Editor - Inspired by VocalRemover",
                "status": "Please load an audio file",
                "language": "Language:",
                "load": "Load Audio",
                "format": "Format:",
                "export": "Export Audio",
                "cut": "Cut (seconds):",
                "apply_cut": "Apply Cut",
                "volume": "Volume (dB):",
                "speed": "Speed:",
                "pitch": "Pitch (semitones):",
                "apply": "Apply All",
                "reverb": "Add Reverb",
                "echo": "Add Echo",
                "fade": "Fade In/Out",
                "eq": "Equalizer",
                "vocal": "Separate Vocal",
                "preview": "Preview",
                "stop": "Stop",
                "undo": "Undo",
                "redo": "Redo",
                "control_frame": "Audio Controls",
                "waveform": "Waveform",
                "file_info": "File Info: No file loaded",
                "timeline": "Timeline:",
                "bass": "Bass:",
                "mid": "Mid:",
                "treble": "Treble:"
            }
        }
        self.current_lang = "vi"

        self.root.title(self.languages[self.current_lang]["title"])
        self.root.geometry("1200x800")
        self.root.state('zoomed')
        self.root.configure(bg="#E6E6E6")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=10, font=("Arial", 12), background="#FF6200", foreground="#000000")
        style.map("TButton",
                  background=[('!disabled', '#FF6200'), ('active', '#E65C00'), ('disabled', '#A3A3A3')],
                  foreground=[('!disabled', '#000000'), ('active', '#000000'), ('disabled', '#666666')])
        style.configure("TLabel", padding=5, font=("Arial", 12), background="#E6E6E6", foreground="black")
        style.configure("TLabelframe", background="#F5F5F5", foreground="black")
        style.configure("TLabelframe.Label", font=("Arial", 14, "bold"), background="#F5F5F5", foreground="black")
        style.configure("TScale", background="#E6E6E6", troughcolor="#B3C7D6", sliderrelief="flat")
        style.configure("TProgressbar", background="#FF6200", troughcolor="#B3C7D6")
        style.configure("TEntry", fieldbackground="#FFFFFF", foreground="#000000")
        style.configure("TCombobox", fieldbackground="#FFFFFF", foreground="#000000")
        style.configure("Custom.TFrame", background="#E6E6E6")

        self.main_frame = ttk.Frame(self.root, padding="20", style="Custom.TFrame")
        self.main_frame.grid(row=0, column=0, sticky=(tk.N, tk.S), padx=20, pady=20)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.lang_frame = ttk.Frame(self.main_frame)
        self.lang_frame.grid(row=0, column=0, sticky=tk.E, pady=5)
        self.lang_label = ttk.Label(self.lang_frame, text=self.languages[self.current_lang]["language"])
        self.lang_label.grid(row=0, column=0, padx=5)
        self.lang_combobox = ttk.Combobox(self.lang_frame, values=["Tiếng Việt", "English"], state="readonly", width=10, font=("Arial", 12))
        self.lang_combobox.set("Tiếng Việt")
        self.lang_combobox.grid(row=0, column=1, padx=5)

        self.status = ttk.Label(self.main_frame, text=self.languages[self.current_lang]["status"], relief=tk.SUNKEN, anchor=tk.CENTER, font=("Arial", 12), background="#B3C7D6", foreground="black")
        self.status.grid(row=5, column=0, sticky=tk.EW, pady=10)

    def bind_drop_event(self):
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.controller.handle_drop)

    def bind_language_event(self):
        self.lang_combobox.bind("<<ComboboxSelected>>", self.controller.change_language)

    def update_status(self, message):
        self.status.config(text=message)