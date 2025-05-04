import tkinter as tk
from tkinter import ttk

class ControlPanel:
    def __init__(self, parent, controller, languages, current_lang):
        self.controller = controller
        self.languages = languages
        self.current_lang = current_lang

        style = ttk.Style()
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

        self.control_frame = ttk.LabelFrame(parent, text=self.languages[self.current_lang]["control_frame"], padding="15")
        self.control_frame.grid(row=3, column=0, sticky=tk.EW, pady=10)
        self.control_frame.columnconfigure(0, weight=1)

        self.file_info_label = ttk.Label(self.control_frame, text=self.languages[self.current_lang]["file_info"], anchor=tk.CENTER)
        self.file_info_label.grid(row=0, column=0, columnspan=3, sticky=tk.EW, pady=5)

        self.load_button = ttk.Button(self.control_frame, text=self.languages[self.current_lang]["load"], style="TButton")
        self.load_button.grid(row=1, column=0, padx=10, pady=5, sticky=tk.EW)

        self.export_frame = ttk.Frame(self.control_frame)
        self.export_frame.grid(row=1, column=1, padx=10, pady=5, sticky=tk.EW)
        self.format_label = ttk.Label(self.export_frame, text=self.languages[self.current_lang]["format"])
        self.format_label.grid(row=0, column=0, padx=5)
        self.format_combobox = ttk.Combobox(self.export_frame, values=["mp3", "wav", "ogg", "flac", "aac"], state="readonly", width=10, font=("Arial", 12))
        self.format_combobox.set("mp3")
        self.format_combobox.grid(row=0, column=1, padx=5)
        self.export_button = ttk.Button(self.export_frame, text=self.languages[self.current_lang]["export"], style="TButton")
        self.export_button.grid(row=0, column=2, padx=5, sticky=tk.EW)
        self.export_frame.columnconfigure(2, weight=1)

        self.undo_redo_frame = ttk.Frame(self.control_frame)
        self.undo_redo_frame.grid(row=1, column=2, padx=10, pady=5, sticky=tk.EW)
        self.undo_button = ttk.Button(self.undo_redo_frame, text=self.languages[self.current_lang]["undo"], style="TButton")
        self.undo_button.grid(row=0, column=0, padx=5, sticky=tk.EW)
        self.redo_button = ttk.Button(self.undo_redo_frame, text=self.languages[self.current_lang]["redo"], style="TButton")
        self.redo_button.grid(row=0, column=1, padx=5, sticky=tk.EW)
        self.undo_redo_frame.columnconfigure(0, weight=1)
        self.undo_redo_frame.columnconfigure(1, weight=1)

        self.cut_label = ttk.Label(self.control_frame, text=self.languages[self.current_lang]["cut"])
        self.cut_label.grid(row=2, column=0, sticky=tk.EW)
        self.start_entry = ttk.Entry(self.control_frame, width=10, font=("Arial", 12), justify=tk.CENTER)
        self.end_entry = ttk.Entry(self.control_frame, width=10, font=("Arial", 12), justify=tk.CENTER)
        self.start_entry.grid(row=2, column=1, padx=5, sticky=tk.EW)
        self.end_entry.grid(row=2, column=2, padx=5, sticky=tk.EW)
        self.apply_cut_button = ttk.Button(self.control_frame, text=self.languages[self.current_lang]["apply_cut"], style="TButton")
        self.apply_cut_button.grid(row=2, column=3, padx=10, sticky=tk.EW)

        self.volume_label = ttk.Label(self.control_frame, text=self.languages[self.current_lang]["volume"])
        self.volume_label.grid(row=3, column=0, sticky=tk.EW)
        self.volume_slider = ttk.Scale(self.control_frame, from_=-20, to=20, orient=tk.HORIZONTAL, length=200)
        self.volume_slider.grid(row=3, column=1, columnspan=3, padx=5, sticky=tk.EW)

        self.speed_label = ttk.Label(self.control_frame, text=self.languages[self.current_lang]["speed"])
        self.speed_label.grid(row=4, column=0, sticky=tk.EW)
        self.speed_slider = ttk.Scale(self.control_frame, from_=0.5, to=2.0, orient=tk.HORIZONTAL, length=200)
        self.speed_slider.set(1.0)
        self.speed_slider.grid(row=4, column=1, columnspan=3, padx=5, sticky=tk.EW)

        self.pitch_label = ttk.Label(self.control_frame, text=self.languages[self.current_lang]["pitch"])
        self.pitch_label.grid(row=5, column=0, sticky=tk.EW)
        self.pitch_slider = ttk.Scale(self.control_frame, from_=-12, to=12, orient=tk.HORIZONTAL, length=200)
        self.pitch_slider.set(0)
        self.pitch_slider.grid(row=5, column=1, columnspan=3, padx=5, sticky=tk.EW)

        self.apply_all_button = ttk.Button(self.control_frame, text=self.languages[self.current_lang]["apply"], style="TButton")
        self.apply_all_button.grid(row=5, column=4, padx=10, sticky=tk.EW)

        self.eq_frame = ttk.LabelFrame(self.control_frame, text=self.languages[self.current_lang]["eq"], padding="10")
        self.eq_frame.grid(row=6, column=0, columnspan=5, pady=5, sticky=tk.EW)
        self.bass_label = ttk.Label(self.eq_frame, text=self.languages[self.current_lang]["bass"])
        self.bass_label.grid(row=0, column=0, sticky=tk.EW)
        self.bass_slider = ttk.Scale(self.eq_frame, from_=-12, to=12, orient=tk.HORIZONTAL, length=150)
        self.bass_slider.grid(row=0, column=1, padx=5, sticky=tk.EW)
        self.mid_label = ttk.Label(self.eq_frame, text=self.languages[self.current_lang]["mid"])
        self.mid_label.grid(row=0, column=2, sticky=tk.EW)
        self.mid_slider = ttk.Scale(self.eq_frame, from_=-12, to=12, orient=tk.HORIZONTAL, length=150)
        self.mid_slider.grid(row=0, column=3, padx=5, sticky=tk.EW)
        self.treble_label = ttk.Label(self.eq_frame, text=self.languages[self.current_lang]["treble"])
        self.treble_label.grid(row=0, column=4, sticky=tk.EW)
        self.treble_slider = ttk.Scale(self.eq_frame, from_=-12, to=12, orient=tk.HORIZONTAL, length=150)
        self.treble_slider.grid(row=0, column=5, padx=5, sticky=tk.EW)
        self.eq_frame.columnconfigure(1, weight=1)
        self.eq_frame.columnconfigure(3, weight=1)
        self.eq_frame.columnconfigure(5, weight=1)

        self.effects_frame = ttk.Frame(self.control_frame)
        self.effects_frame.grid(row=7, column=0, columnspan=5, pady=5, sticky=tk.EW)
        self.reverb_button = ttk.Button(self.effects_frame, text=self.languages[self.current_lang]["reverb"], style="TButton")
        self.reverb_button.grid(row=0, column=0, padx=10, sticky=tk.EW)
        self.echo_button = ttk.Button(self.effects_frame, text=self.languages[self.current_lang]["echo"], style="TButton")
        self.echo_button.grid(row=0, column=1, padx=10, sticky=tk.EW)
        self.fade_button = ttk.Button(self.effects_frame, text=self.languages[self.current_lang]["fade"], style="TButton")
        self.fade_button.grid(row=0, column=2, padx=10, sticky=tk.EW)
        self.vocal_button = ttk.Button(self.effects_frame, text=self.languages[self.current_lang]["vocal"], style="TButton")
        self.vocal_button.grid(row=0, column=3, padx=10, sticky=tk.EW)
        self.preview_button = ttk.Button(self.effects_frame, text=self.languages[self.current_lang]["preview"], style="TButton")
        self.preview_button.grid(row=0, column=4, padx=10, sticky=tk.EW)
        self.stop_button = ttk.Button(self.effects_frame, text=self.languages[self.current_lang]["stop"], style="TButton")
        self.stop_button.grid(row=0, column=5, padx=10, sticky=tk.EW)
        self.effects_frame.columnconfigure(0, weight=1)
        self.effects_frame.columnconfigure(1, weight=1)
        self.effects_frame.columnconfigure(2, weight=1)
        self.effects_frame.columnconfigure(3, weight=1)
        self.effects_frame.columnconfigure(4, weight=1)
        self.effects_frame.columnconfigure(5, weight=1)

        self.progress = ttk.Progressbar(parent, orient=tk.HORIZONTAL, length=400, mode='indeterminate', style="TProgressbar")
        self.progress.grid(row=4, column=0, pady=5, sticky=tk.EW)

    def bind_button_events(self):
        if self.controller is not None:
            self.load_button.config(command=self.controller.load_file)
            self.export_button.config(command=self.controller.export_audio)
            if hasattr(self.controller, 'undo'):
                self.undo_button.config(command=self.controller.undo)
            else:
                print("Warning: undo method not found in AudioController")
            if hasattr(self.controller, 'redo'):
                self.redo_button.config(command=self.controller.redo)
            else:
                print("Warning: redo method not found in AudioController")
            self.apply_cut_button.config(command=self.controller.cut_audio)
            self.apply_all_button.config(command=self.controller.apply_all)
            self.reverb_button.config(command=self.controller.toggle_reverb)
            self.echo_button.config(command=self.controller.toggle_echo)
            self.fade_button.config(command=self.controller.toggle_fade)
            self.vocal_button.config(command=self.controller.separate_vocal)
            self.preview_button.config(command=self.controller.preview_audio)
            self.stop_button.config(command=self.controller.stop_preview)

    def start_progress(self):
        self.progress['value'] = 0
        self.progress.start()

    def stop_progress(self):
        self.progress.stop()
        self.progress['value'] = 100

    def get_export_format(self):
        return self.format_combobox.get()

    def set_cut_defaults(self, duration):
        self.start_entry.delete(0, tk.END)
        self.end_entry.delete(0, tk.END)
        self.start_entry.insert(0, "0.000")
        self.end_entry.insert(0, f"{duration:.3f}")

    def update_file_info(self, duration, channels, sample_rate, bitrate, metadata):
        info = (f"Thời lượng: {duration:.2f}s | Kênh: {channels} | Tần số: {sample_rate} Hz | "
                f"Bitrate: {bitrate/1000:.1f} kbps | Tựa đề: {metadata['title']} | "
                f"Nghệ sĩ: {metadata['artist']} | Kích thước: {metadata['size']:.2f} MB"
                if self.current_lang == "vi" else
                f"Duration: {duration:.2f}s | Channels: {channels} | Sample Rate: {sample_rate} Hz | "
                f"Bitrate: {bitrate/1000:.1f} kbps | Title: {metadata['title']} | "
                f"Artist: {metadata['artist']} | Size: {metadata['size']:.2f} MB")
        self.file_info_label.config(text=info)