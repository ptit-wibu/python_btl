import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class WaveformView:
    def __init__(self, parent, controller, languages, current_lang):
        self.controller = controller
        self.languages = languages
        self.current_lang = current_lang
        self.is_manual_sliding = False  # Trạng thái khi người dùng kéo thanh trượt

        self.fig, self.ax = plt.subplots(figsize=(10, 3), facecolor="#FFFFFF")
        self.ax.set_facecolor("#D9E6F2")
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().grid(row=1, column=0, pady=10, sticky=tk.EW)
        parent.columnconfigure(0, weight=1)
        self.fig.tight_layout()

        self.timeline_frame = ttk.Frame(parent)
        self.timeline_frame.grid(row=2, column=0, pady=5, sticky=tk.EW)
        self.timeline_label = ttk.Label(self.timeline_frame, text=self.languages[self.current_lang]["timeline"])
        self.timeline_label.grid(row=0, column=0, padx=5)
        self.timeline_slider = ttk.Scale(self.timeline_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=600)
        self.timeline_slider.grid(row=0, column=1, padx=5)
        self.timeline_position_label = ttk.Label(self.timeline_frame, text="0.00s / 0.00s", anchor=tk.CENTER)
        self.timeline_position_label.grid(row=0, column=2, padx=5)
        self.timeline_frame.columnconfigure(1, weight=1)

    def bind_timeline_event(self):
        def on_slider_change(value):
            if not self.is_manual_sliding:
                return
            self.controller.seek_timeline(value)

        def on_slider_press(event):
            self.is_manual_sliding = True

        def on_slider_release(event):
            self.is_manual_sliding = False

        self.timeline_slider.config(command=on_slider_change)
        self.timeline_slider.bind("<Button-1>", on_slider_press)
        self.timeline_slider.bind("<ButtonRelease-1>", on_slider_release)

    def update_waveform(self, audio_array, sr, beat_times=None):
        self.ax.clear()
        if len(audio_array.shape) > 1:
            audio_array = audio_array[0]
        time_axis = np.linspace(0, len(audio_array) / sr, len(audio_array))
        self.ax.plot(time_axis, audio_array, color="#FF6200")
        if beat_times is not None:
            for beat in beat_times:
                self.ax.axvline(x=beat, color='r', linestyle='--', alpha=0.5)
        self.ax.set_title(self.languages[self.current_lang]["waveform"], fontsize=14, color="black")
        self.ax.tick_params(axis='both', colors='black')
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_facecolor("#D9E6F2")
        self.fig.set_facecolor("#FFFFFF")
        self.canvas.draw()

    def update_timeline(self, duration):
        self.timeline_slider.configure(to=duration)
        self.timeline_position_label.config(text=f"0.00s / {duration:.2f}s")

    def update_timeline_position(self, position, duration):
        self.timeline_position_label.config(text=f"{position:.2f}s / {duration:.2f}s")