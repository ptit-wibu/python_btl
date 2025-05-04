import os
import threading
import multiprocessing as mp
import numpy as np
from tkinter import messagebox
from pydub import AudioSegment
import soundfile as sf
import tkinter as tk
import time
import logging
import ffmpeg

from controllers.effect_controller import separate_vocal_worker

# Thiết lập logging để theo dõi hiệu suất
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AudioController:
    def __init__(self, loader, processor, exporter, main_view, control_panel, waveform_view, effect_controller):
        self.loader = loader
        self.processor = processor
        self.exporter = exporter
        self.main_view = main_view
        self.control_panel = control_panel
        self.waveform_view = waveform_view
        self.effect_controller = effect_controller
        self.project_controller = None  # Sẽ được gán trong main.py
        self.audio = None
        self.original_audio = None  # Lưu trữ âm thanh gốc
        self.audio_array = None
        self.sample_rate = None
        self.channels = None
        self.file_path = None
        self.duration = 0
        self.bitrate = None
        self.metadata = {}
        self.preview_process = None
        self.undo_stack = []
        self.redo_stack = []
        self.beat_times = None
        self.tempo = None
        self.is_processing = False
        self.is_seeking = False  # Trạng thái tua
        self.queue = mp.Queue()
        self.volume_gain = 0.0
        self.speed = 1.0
        self.pitch_steps = 0.0
        self.reverb_enabled = False
        self.echo_enabled = False
        self.fade_enabled = False
        self.bass_gain = 0.0
        self.mid_gain = 0.0
        self.treble_gain = 0.0
        self._after_id = None
        self._apply_lock = threading.Lock()
        self.preview_start_offset = 0
        self.last_timeline_position = 0
        self.temp_preview_file = None  # Lưu đường dẫn file WAV tạm thời
        # Gắn sự kiện tua cho thanh trượt
        self.waveform_view.timeline_slider.bind("<ButtonPress-1>", self.start_seeking)
        self.waveform_view.timeline_slider.bind("<ButtonRelease-1>", self.seek_audio)

    def _update_audio_arrays(self, audio_segment):
        self.audio_array = np.array(audio_segment.get_array_of_samples())
        if self.channels == 2:
            self.audio_array = self.audio_array.reshape(-1, 2).T
        else:
            self.audio_array = self.audio_array.reshape(-1)
        self.audio_array = self.audio_array / (2**15)
        self.sample_rate = audio_segment.frame_rate
        self.duration = len(audio_segment) / 1000.0

    def handle_drop(self, event):
        if self.is_processing:
            messagebox.showwarning(
                "Cảnh báo" if self.main_view.current_lang == "vi" else "Warning",
                "Đang xử lý, vui lòng chờ!" if self.main_view.current_lang == "vi" else "Processing, please wait!"
            )
            return
        file_path = event.data.strip('{}')
        if file_path and os.path.exists(file_path):
            self.load_file(file_path)

    def load_file(self, file_path=None):
        if self.is_processing:
            messagebox.showwarning(
                "Cảnh báo" if self.main_view.current_lang == "vi" else "Warning",
                "Đang xử lý, vui lòng chờ!" if self.main_view.current_lang == "vi" else "Processing, please wait!"
            )
            return
        if not file_path:
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(filetypes=[("Audio files", "*.mp3 *.wav *.ogg *.flac *.aac *.m4a *.wma")])
        if file_path:
            self.is_processing = True
            self.control_panel.start_progress()
            self.main_view.update_status("Đang tải file âm thanh..." if self.main_view.current_lang == "vi" else "Loading audio file...")
            threading.Thread(target=self._load_file_thread, args=(file_path,), daemon=True).start()

    def _load_file_thread(self, file_path):
        try:
            start_time = time.time()
            self.audio, self.audio_array, self.sample_rate, self.channels, self.duration, self.bitrate, self.metadata = self.loader.load_audio(file_path)
            self.original_audio = self.audio
            self.file_path = file_path
            self.save_state()
            self.main_view.root.after(0, lambda: self.waveform_view.update_waveform(self.audio_array, self.sample_rate))
            self.main_view.root.after(0, lambda: self.control_panel.set_cut_defaults(self.duration))
            self.main_view.root.after(0, lambda: self.waveform_view.update_timeline(self.duration))
            self.main_view.root.after(0, lambda: self.main_view.update_status(
                f"Đã tải: {os.path.basename(file_path)} (Thời lượng: {self.duration:.3f}s)"
                if self.main_view.current_lang == "vi" else
                f"Loaded: {os.path.basename(file_path)} (Duration: {self.duration:.3f}s)"
            ))
            self.main_view.root.after(0, lambda: self.control_panel.update_file_info(
                self.duration, self.channels, self.sample_rate, self.bitrate, self.metadata
            ))
            self.reset_effects()
            self.beat_times, self.tempo = self.processor.detect_beats(self.audio_array, self.sample_rate)
            self.main_view.root.after(0, lambda: self.waveform_view.update_waveform(self.audio_array, self.sample_rate, self.beat_times))
            logging.info(f"Loaded file {file_path} in {time.time() - start_time:.2f} seconds")
        except Exception as e:
            self.main_view.root.after(0, lambda e=e: messagebox.showerror(
                "Lỗi" if self.main_view.current_lang == "vi" else "Error", str(e)
            ))
        finally:
            self.is_processing = False
            self.main_view.root.after(0, self.control_panel.stop_progress)

    def save_state(self):
        state = {
            "audio": self.audio,
            "audio_array": self.audio_array.copy() if self.audio_array is not None else None,
            "sample_rate": self.sample_rate,
            "duration": self.duration,
            "volume_gain": self.volume_gain,
            "speed": self.speed,
            "pitch_steps": self.pitch_steps,
            "reverb_enabled": self.reverb_enabled,
            "echo_enabled": self.echo_enabled,
            "fade_enabled": self.fade_enabled,
            "bass_gain": self.bass_gain,
            "mid_gain": self.mid_gain,
            "treble_gain": self.treble_gain
        }
        self.undo_stack.append(state)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack or len(self.undo_stack) < 2:
            return
        current_state = self.undo_stack.pop()
        self.redo_stack.append(current_state)
        previous_state = self.undo_stack[-1]
        self.audio = previous_state["audio"]
        self.audio_array = previous_state["audio_array"]
        self.sample_rate = previous_state["sample_rate"]
        self.duration = previous_state["duration"]
        self.volume_gain = previous_state["volume_gain"]
        self.speed = previous_state["speed"]
        self.pitch_steps = previous_state["pitch_steps"]
        self.reverb_enabled = previous_state["reverb_enabled"]
        self.echo_enabled = previous_state["echo_enabled"]
        self.fade_enabled = previous_state["fade_enabled"]
        self.bass_gain = previous_state["bass_gain"]
        self.mid_gain = previous_state["mid_gain"]
        self.treble_gain = previous_state["treble_gain"]
        self.waveform_view.update_waveform(self.audio_array, self.sample_rate, self.beat_times)
        self.control_panel.volume_slider.set(self.volume_gain)
        self.control_panel.speed_slider.set(self.speed)
        self.control_panel.pitch_slider.set(self.pitch_steps)
        self.control_panel.bass_slider.set(self.bass_gain)
        self.control_panel.mid_slider.set(self.mid_gain)
        self.control_panel.treble_slider.set(self.treble_gain)
        self.control_panel.set_cut_defaults(self.duration)
        self.waveform_view.update_timeline(self.duration)

    def redo(self):
        if not self.redo_stack:
            return
        state = self.redo_stack.pop()
        self.undo_stack.append(state)
        self.audio = state["audio"]
        self.audio_array = state["audio_array"]
        self.sample_rate = state["sample_rate"]
        self.duration = state["duration"]
        self.volume_gain = state["volume_gain"]
        self.speed = state["speed"]
        self.pitch_steps = state["pitch_steps"]
        self.reverb_enabled = state["reverb_enabled"]
        self.echo_enabled = state["echo_enabled"]
        self.fade_enabled = state["fade_enabled"]
        self.bass_gain = state["bass_gain"]
        self.mid_gain = state["mid_gain"]
        self.treble_gain = state["treble_gain"]
        self.waveform_view.update_waveform(self.audio_array, self.sample_rate, self.beat_times)
        self.control_panel.volume_slider.set(self.volume_gain)
        self.control_panel.speed_slider.set(self.speed)
        self.control_panel.pitch_slider.set(self.pitch_steps)
        self.control_panel.bass_slider.set(self.bass_gain)
        self.control_panel.mid_slider.set(self.mid_gain)
        self.control_panel.treble_slider.set(self.treble_gain)
        self.control_panel.set_cut_defaults(self.duration)
        self.waveform_view.update_timeline(self.duration)

    def cut_audio(self):
        if self.is_processing:
            messagebox.showwarning(
                "Cảnh báo" if self.main_view.current_lang == "vi" else "Warning",
                "Đang xử lý, vui lòng chờ!" if self.main_view.current_lang == "vi" else "Processing, please wait!"
            )
            return
        if self.audio is None:
            messagebox.showwarning(
                "Cảnh báo" if self.main_view.current_lang == "vi" else "Warning",
                "Vui lòng tải file âm thanh trước" if self.main_view.current_lang == "vi" else "Please load an audio file first"
            )
            return
        try:
            start = self.control_panel.start_entry.get().strip()
            end = self.control_panel.end_entry.get().strip()
            if not start or not end:
                raise ValueError("Thời gian bắt đầu và kết thúc không được để trống")
            start = float(start)
            end = float(end)
            if start < 0 or end <= start or end > self.duration:
                raise ValueError(f"Thời gian không hợp lệ: Thời gian bắt đầu phải nhỏ hơn thời gian kết thúc và trong phạm vi {self.duration:.3f}s")
            self.is_processing = True
            self.control_panel.start_progress()
            self.main_view.update_status("Đang cắt âm thanh..." if self.main_view.current_lang == "vi" else "Cutting audio...")
            threading.Thread(target=self._cut_audio_thread, args=(start, end), daemon=True).start()
        except ValueError as e:
            messagebox.showerror(
                "Lỗi" if self.main_view.current_lang == "vi" else "Error",
                f"Thời gian không hợp lệ: {str(e)}" if self.main_view.current_lang == "vi" else f"Invalid time: {str(e)}"
            )

    def _cut_audio_thread(self, start, end):
        try:
            self.audio = self.processor.cut_audio(self.audio, start, end, self.duration)
            self.original_audio = self.audio
            self._update_audio_arrays(self.audio)
            self.save_state()
            self.main_view.root.after(0, lambda: self.waveform_view.update_waveform(self.audio_array, self.sample_rate, self.beat_times))
            self.main_view.root.after(0, lambda: self.control_panel.set_cut_defaults(self.duration))
            self.main_view.root.after(0, lambda: self.waveform_view.update_timeline(self.duration))
            self.main_view.root.after(0, lambda: self.main_view.update_status(
                "Đã cắt âm thanh" if self.main_view.current_lang == "vi" else "Audio cut completed"
            ))
        except Exception as e:
            self.main_view.root.after(0, lambda: messagebox.showerror(
                "Lỗi" if self.main_view.current_lang == "vi" else "Error", str(e)
            ))
        finally:
            self.is_processing = False
            self.main_view.root.after(0, self.control_panel.stop_progress)

    def apply_all(self):
        if self.is_processing:
            messagebox.showwarning(
                "Cảnh báo" if self.main_view.current_lang == "vi" else "Warning",
                "Đang xử lý, vui lòng chờ!" if self.main_view.current_lang == "vi" else "Processing, please wait!"
            )
            return
        if self.audio is None:
            messagebox.showwarning(
                "Cảnh báo" if self.main_view.current_lang == "vi" else "Warning",
                "Vui lòng tải file âm thanh trước" if self.main_view.current_lang == "vi" else "Please load an audio file first"
            )
            return
        with self._apply_lock:
            if self.is_processing:
                return
            self.is_processing = True
        self.control_panel.start_progress()
        self.main_view.update_status("Đang xử lý hiệu ứng..." if self.main_view.current_lang == "vi" else "Applying effects...")
        threading.Thread(target=self._apply_all_thread, daemon=True).start()

    def _apply_all_thread(self):
        try:
            with self._apply_lock:
                if self.original_audio is not None:
                    self._update_audio_arrays(self.original_audio)
                else:
                    raise ValueError("Không có âm thanh gốc để áp dụng hiệu ứng")

                self.volume_gain = float(self.control_panel.volume_slider.get())
                self.speed = float(self.control_panel.speed_slider.get())
                self.pitch_steps = float(self.control_panel.pitch_slider.get())
                self.bass_gain = float(self.control_panel.bass_slider.get())
                self.mid_gain = float(self.control_panel.mid_slider.get())
                self.treble_gain = float(self.control_panel.treble_slider.get())
                audio = self.original_audio

                if self.volume_gain != 0:
                    audio = self.processor.change_volume(self.volume_gain, audio)
                    self._update_audio_arrays(audio)

                if self.speed != 1.0:
                    audio_array, sr = self.processor.change_speed(self.speed, self.audio_array, self.sample_rate)
                    temp_wav = os.path.join(os.path.dirname(self.file_path or "."), "temp_speed.wav")
                    sf.write(temp_wav, audio_array.T if len(audio_array.shape) > 1 else audio_array, sr)
                    audio = AudioSegment.from_wav(temp_wav)
                    try:
                        os.remove(temp_wav)
                    except Exception as e:
                        print(f"Warning: Could not remove {temp_wav}: {str(e)}")
                    self._update_audio_arrays(audio)

                if self.pitch_steps != 0:
                    audio_array, sr = self.processor.change_pitch(self.pitch_steps, self.audio_array, self.sample_rate)
                    temp_wav = os.path.join(os.path.dirname(self.file_path or "."), "temp_pitch.wav")
                    sf.write(temp_wav, audio_array.T if len(audio_array.shape) > 1 else audio_array, sr)
                    audio = AudioSegment.from_wav(temp_wav)
                    try:
                        os.remove(temp_wav)
                    except Exception as e:
                        print(f"Warning: Could not remove {temp_wav}: {str(e)}")
                    self._update_audio_arrays(audio)

                if self.reverb_enabled:
                    audio_array = self.processor.add_reverb(audio, self.channels)
                    temp_wav = os.path.join(os.path.dirname(self.file_path or "."), "temp_reverb.wav")
                    if len(audio_array.shape) > 1:
                        sf.write(temp_wav, audio_array, self.sample_rate, subtype='PCM_16')
                    else:
                        sf.write(temp_wav, audio_array, self.sample_rate, subtype='PCM_16')
                    try:
                        audio = AudioSegment.from_wav(temp_wav)
                    except Exception as e:
                        raise Exception(f"Error reading temp_reverb.wav: {str(e)}")
                    try:
                        os.remove(temp_wav)
                    except Exception as e:
                        print(f"Warning: Could not remove {temp_wav}: {str(e)}")
                    self._update_audio_arrays(audio)

                if self.echo_enabled:
                    audio = self.processor.add_echo(audio)
                    self._update_audio_arrays(audio)

                if self.fade_enabled:
                    audio = self.processor.fade_in_out(audio)
                    self._update_audio_arrays(audio)

                if self.bass_gain != 0 or self.mid_gain != 0 or self.treble_gain != 0:
                    audio_array, sr = self.processor.apply_equalizer(self.audio_array, self.sample_rate, self.channels, self.bass_gain, self.mid_gain, self.treble_gain)
                    temp_wav = os.path.join(os.path.dirname(self.file_path or "."), "temp_eq.wav")
                    sf.write(temp_wav, audio_array.T if len(audio_array.shape) > 1 else audio_array, sr)
                    audio = AudioSegment.from_wav(temp_wav)
                    try:
                        os.remove(temp_wav)
                    except Exception as e:
                        print(f"Warning: Could not remove {temp_wav}: {str(e)}")
                    self._update_audio_arrays(audio)

                self.audio = audio
                self.save_state()
                self.main_view.root.after(0, lambda: self.waveform_view.update_waveform(self.audio_array, self.sample_rate, self.beat_times))
                self.main_view.root.after(0, lambda: self.control_panel.set_cut_defaults(self.duration))
                self.main_view.root.after(0, lambda: self.waveform_view.update_timeline(self.duration))
                self.main_view.root.after(0, lambda: self.main_view.update_status(
                    "Đã áp dụng hiệu ứng" if self.main_view.current_lang == "vi" else "Effects applied"
                ))
        except Exception as e:
            self.main_view.root.after(0, lambda: messagebox.showerror(
                "Lỗi" if self.main_view.current_lang == "vi" else "Error", str(e)
            ))
        finally:
            self.is_processing = False
            self.main_view.root.after(0, self.control_panel.stop_progress)

    def toggle_reverb(self):
        if self.is_processing:
            messagebox.showwarning(
                "Cảnh báo" if self.main_view.current_lang == "vi" else "Warning",
                "Đang xử lý, vui lòng chờ!" if self.main_view.current_lang == "vi" else "Processing, please wait!"
            )
            return
        self.reverb_enabled = not self.reverb_enabled
        self.apply_all()

    def toggle_echo(self):
        if self.is_processing:
            messagebox.showwarning(
                "Cảnh báo" if self.main_view.current_lang == "vi" else "Warning",
                "Đang xử lý, vui lòng chờ!" if self.main_view.current_lang == "vi" else "Processing, please wait!"
            )
            return
        self.echo_enabled = not self.echo_enabled
        self.apply_all()

    def toggle_fade(self):
        if self.is_processing:
            messagebox.showwarning(
                "Cảnh báo" if self.main_view.current_lang == "vi" else "Warning",
                "Đang xử lý, vui lòng chờ!" if self.main_view.current_lang == "vi" else "Processing, please wait!"
            )
            return
        self.fade_enabled = not self.fade_enabled
        self.apply_all()

    def separate_vocal(self):
        if self.is_processing:
            messagebox.showwarning(
                "Cảnh báo" if self.main_view.current_lang == "vi" else "Warning",
                "Đang xử lý, vui lòng chờ!" if self.main_view.current_lang == "vi" else "Processing, please wait!"
            )
            return
        if self.audio is None:
            messagebox.showwarning(
                "Cảnh báo" if self.main_view.current_lang == "vi" else "Warning",
                "Vui lòng tải file âm thanh trước" if self.main_view.current_lang == "vi" else "Please load an audio file first"
            )
            return
        if self._after_id is not None:
            self.main_view.root.after_cancel(self._after_id)
            self._after_id = None
        self.is_processing = True
        self.control_panel.start_progress()
        self.main_view.update_status("Đang tách giọng hát..." if self.main_view.current_lang == "vi" else "Separating vocals...")
        process = mp.Process(target=separate_vocal_worker, args=(self.audio_array.copy(), self.sample_rate, self.channels, self.queue))
        process.start()
        self._check_separate_vocal_result()

    def _check_separate_vocal_result(self):
        if not self.queue.empty():
            result = self.queue.get()
            if result[0] == "success":
                vocal, instrumental = result[1], result[2]
                output_dir = os.path.dirname(self.file_path or ".")
                
                # Chuyển vocal thành AudioSegment
                temp_vocal_wav = os.path.join(output_dir, "temp_vocal.wav")
                sf.write(temp_vocal_wav, vocal.T if len(vocal.shape) > 1 else vocal, self.sample_rate, subtype='PCM_16')
                vocal_segment = AudioSegment.from_wav(temp_vocal_wav)
                self.exporter.export_audio(vocal_segment, "wav", os.path.join(output_dir, "vocal.wav"), self.file_path, self.sample_rate, self.channels)
                os.remove(temp_vocal_wav)
                
                # Chuyển instrumental thành AudioSegment
                temp_instrumental_wav = os.path.join(output_dir, "temp_instrumental.wav")
                sf.write(temp_instrumental_wav, instrumental.T if len(instrumental.shape) > 1 else instrumental, self.sample_rate, subtype='PCM_16')
                instrumental_segment = AudioSegment.from_wav(temp_instrumental_wav)
                self.exporter.export_audio(instrumental_segment, "wav", os.path.join(output_dir, "instrumental.wav"), self.file_path, self.sample_rate, self.channels)
                os.remove(temp_instrumental_wav)
                
                self.main_view.root.after(0, lambda: self.main_view.update_status(
                    "Đã tách giọng hát và nhạc nền" if self.main_view.current_lang == "vi" else "Vocals and instrumental separated"
                ))
            else:
                error_msg = result[1]
                self.main_view.root.after(0, lambda: messagebox.showerror(
                    "Lỗi" if self.main_view.current_lang == "vi" else "Error", error_msg
                ))
            self.is_processing = False
            self.main_view.root.after(0, self.control_panel.stop_progress)
            self._after_id = None
        else:
            self._after_id = self.main_view.root.after(100, self._check_separate_vocal_result)

    def preview_audio(self):
        if self.is_processing:
            messagebox.showwarning(
                "Cảnh báo" if self.main_view.current_lang == "vi" else "Warning",
                "Đang xử lý, vui lòng chờ!" if self.main_view.current_lang == "vi" else "Processing, please wait!"
            )
            return
        if self.audio is None:
            messagebox.showwarning(
                "Cảnh báo" if self.main_view.current_lang == "vi" else "Warning",
                "Vui lòng tải file âm thanh trước" if self.main_view.current_lang == "vi" else "Please load an audio file first"
            )
            return
        try:
            start = self.control_panel.start_entry.get().strip()
            end = self.control_panel.end_entry.get().strip()
            if not start or not end:
                raise ValueError("Thời gian bắt đầu và kết thúc không được để trống")
            start = float(start)
            end = float(end)
            if start < 0 or end <= start or end > self.duration:
                raise ValueError(f"Thời gian không hợp lệ: Thời gian bắt đầu phải nhỏ hơn thời gian kết thúc và trong phạm vi {self.duration:.3f}s")
            self.is_processing = True
            self.control_panel.start_progress()
            self.main_view.update_status("Đang phát thử..." if self.main_view.current_lang == "vi" else "Previewing...")
            self.preview_start_offset = start
            self.last_timeline_position = start
            # Xuất file WAV tạm thời từ self.audio (chứa effect)
            self.temp_preview_file = os.path.join(os.path.dirname(self.file_path or "."), "audio_preview.wav")
            self.audio.export(self.temp_preview_file, format="wav")
            self.exporter.preview_audio(self.temp_preview_file, self.sample_rate, self.channels, start, end)
            self.control_panel.preview_button.config(state="disabled")
            self.control_panel.stop_button.config(state="normal")
            threading.Thread(target=self._preview_manager, daemon=True).start()
        except ValueError as e:
            messagebox.showerror(
                "Lỗi" if self.main_view.current_lang == "vi" else "Error",
                f"Thời gian không hợp lệ: {str(e)}" if self.main_view.current_lang == "vi" else f"Invalid time: {str(e)}"
            )
        except Exception as e:
            messagebox.showerror(
                "Lỗi" if self.main_view.current_lang == "vi" else "Error",
                f"Lỗi phát âm thanh: {str(e)}" if self.main_view.current_lang == "vi" else f"Playback error: {str(e)}"
            )
        finally:
            self.is_processing = False
            self.control_panel.stop_progress()

    def _preview_manager(self):
        preview_duration = float(self.control_panel.end_entry.get()) - self.preview_start_offset
        start_time = time.time()
        while self.exporter.is_previewing:
            elapsed = time.time() - start_time
            position = elapsed + self.preview_start_offset
            if not self.is_seeking and abs(position - self.last_timeline_position) >= 0.1 and position <= self.duration:
                self.last_timeline_position = position
                self.main_view.root.after(0, lambda: self.waveform_view.update_timeline_position(position, self.duration))
                self.main_view.root.after(0, lambda: self.waveform_view.timeline_slider.set(position))
            if elapsed >= preview_duration:
                self.exporter.stop_preview(self.temp_preview_file, None)
                break
            time.sleep(0.1)
        self.main_view.root.after(0, lambda: self.waveform_view.update_timeline_position(0, self.duration))
        self.main_view.root.after(0, lambda: self.waveform_view.timeline_slider.set(0))
        self.main_view.root.after(0, lambda: self.main_view.update_status(
            "Đã dừng phát" if self.main_view.current_lang == "vi" else "Playback stopped"
        ))
        self.main_view.root.after(0, lambda: self.control_panel.preview_button.config(state="normal"))
        self.main_view.root.after(0, lambda: self.control_panel.stop_button.config(state="disabled"))
        self.last_timeline_position = 0
        self.is_seeking = False
        # Xóa file WAV tạm thời
        if self.temp_preview_file and os.path.exists(self.temp_preview_file):
            try:
                os.remove(self.temp_preview_file)
            except Exception as e:
                logging.warning(f"Could not remove {self.temp_preview_file}: {str(e)}")
        self.temp_preview_file = None
        logging.info("Preview stopped")

    def start_seeking(self, event):
        self.is_seeking = True

    def seek_audio(self, event):
        if not self.temp_preview_file or not self.exporter.is_previewing:
            self.is_seeking = False
            return
        new_position = self.waveform_view.timeline_slider.get()
        if new_position < self.preview_start_offset or new_position > float(self.control_panel.end_entry.get()):
            self.is_seeking = False
            return
        self.exporter.stop_preview(self.temp_preview_file, None)
        self.preview_start_offset = new_position
        self.last_timeline_position = new_position
        self.exporter.preview_audio(self.temp_preview_file, self.sample_rate, self.channels, new_position, float(self.control_panel.end_entry.get()))
        self.is_seeking = False
        threading.Thread(target=self._preview_manager, daemon=True).start()

    def stop_preview(self):
        self.exporter.stop_preview(self.temp_preview_file, None)
        self.main_view.update_status("Đã dừng phát" if self.main_view.current_lang == "vi" else "Playback stopped")
        self.control_panel.preview_button.config(state="normal")
        self.control_panel.stop_button.config(state="disabled")
        self.last_timeline_position = 0
        self.is_seeking = False
        # Xóa file WAV tạm thời
        if self.temp_preview_file and os.path.exists(self.temp_preview_file):
            try:
                os.remove(self.temp_preview_file)
            except Exception as e:
                logging.warning(f"Could not remove {self.temp_preview_file}: {str(e)}")
        self.temp_preview_file = None

    def export_audio(self):
        if self.is_processing:
            messagebox.showwarning(
                "Cảnh báo" if self.main_view.current_lang == "vi" else "Warning",
                "Đang xử lý, vui lòng chờ!" if self.main_view.current_lang == "vi" else "Processing, please wait!"
            )
            return
        if self.audio is None:
            messagebox.showwarning(
                "Cảnh báo" if self.main_view.current_lang == "vi" else "Warning",
                "Vui lòng tải file âm thanh trước" if self.main_view.current_lang == "vi" else "Please load an audio file first"
            )
            return
        format = self.control_panel.get_export_format()
        output_path = tk.filedialog.asksaveasfilename(defaultextension=f".{format}", filetypes=[(f"{format.upper()} files", f"*.{format}")])
        if output_path:
            self.is_processing = True
            self.control_panel.start_progress()
            self.main_view.update_status("Đang xuất âm thanh..." if self.main_view.current_lang == "vi" else "Exporting audio...")
            threading.Thread(target=self._export_audio_thread, args=(output_path, format), daemon=True).start()

    def _export_audio_thread(self, output_path, format):
        try:
            self.exporter.export_audio(self.audio, format, output_path, self.file_path, self.sample_rate, self.channels)
            self.main_view.root.after(0, lambda: self.main_view.update_status(
                f"Đã xuất: {os.path.basename(output_path)}" if self.main_view.current_lang == "vi" else f"Exported: {os.path.basename(output_path)}"
            ))
        except Exception as e:
            self.main_view.root.after(0, lambda: messagebox.showerror(
                "Lỗi" if self.main_view.current_lang == "vi" else "Error", str(e)
            ))
        finally:
            self.is_processing = False
            self.main_view.root.after(0, self.control_panel.stop_progress)

    def reset_effects(self):
        if self.audio is None:
            self.main_view.update_status(
                "Không có âm thanh để đặt lại" if self.main_view.current_lang == "vi" else "No audio to reset"
            )
            return
        self.volume_gain = 0.0
        self.speed = 1.0
        self.pitch_steps = 0.0
        self.reverb_enabled = False
        self.echo_enabled = False
        self.fade_enabled = False
        self.bass_gain = 0.0
        self.mid_gain = 0.0
        self.treble_gain = 0.0
        self.control_panel.volume_slider.set(0)
        self.control_panel.speed_slider.set(1.0)
        self.control_panel.pitch_slider.set(0)
        self.control_panel.bass_slider.set(0)
        self.control_panel.mid_slider.set(0)
        self.control_panel.treble_slider.set(0)
        self.control_panel.set_cut_defaults(self.duration)
        self.main_view.update_status(
            "Đã đặt lại hiệu ứng và thời gian cắt" if self.main_view.current_lang == "vi" else "Effects and cut times reset"
        )

    def seek_timeline(self, position):
        position = float(position)
        self.waveform_view.update_timeline_position(position, self.duration)

    def change_language(self, event=None):
        lang = self.main_view.lang_combobox.get()
        self.main_view.current_lang = "vi" if lang == "Tiếng Việt" else "en"
        lang_dict = self.main_view.languages[self.main_view.current_lang]
        self.main_view.root.title(lang_dict["title"])
        self.main_view.status.config(text=lang_dict["status"])
        self.main_view.lang_label.config(text=lang_dict["language"])
        self.control_panel.control_frame.config(text=lang_dict["control_frame"])
        self.control_panel.file_info_label.config(text=lang_dict["file_info"])
        self.control_panel.load_button.config(text=lang_dict["load"])
        self.control_panel.format_label.config(text=lang_dict["format"])
        self.control_panel.export_button.config(text=lang_dict["export"])
        self.control_panel.save_project_button.config(text=lang_dict["save_project"])
        self.control_panel.load_project_button.config(text=lang_dict["load_project"])
        self.control_panel.undo_button.config(text=lang_dict["undo"])
        self.control_panel.redo_button.config(text=lang_dict["redo"])
        self.control_panel.reset_button.config(text=lang_dict["reset"])
        self.control_panel.cut_label.config(text=lang_dict["cut"])
        self.control_panel.apply_cut_button.config(text=lang_dict["apply_cut"])
        self.control_panel.volume_label.config(text=lang_dict["volume"])
        self.control_panel.speed_label.config(text=lang_dict["speed"])
        self.control_panel.pitch_label.config(text=lang_dict["pitch"])
        self.control_panel.apply_all_button.config(text=lang_dict["apply"])
        self.control_panel.eq_frame.config(text=lang_dict["eq"])
        self.control_panel.bass_label.config(text=lang_dict["bass"])
        self.control_panel.mid_label.config(text=lang_dict["mid"])
        self.control_panel.treble_label.config(text=lang_dict["treble"])
        self.control_panel.reverb_button.config(text=lang_dict["reverb"])
        self.control_panel.echo_button.config(text=lang_dict["echo"])
        self.control_panel.fade_button.config(text=lang_dict["fade"])
        self.control_panel.vocal_button.config(text=lang_dict["vocal"])
        self.control_panel.preview_button.config(text=lang_dict["preview"])
        self.control_panel.stop_button.config(text=lang_dict["stop"])
        self.waveform_view.timeline_label.config(text=lang_dict["timeline"])
        self.waveform_view.ax.set_title(lang_dict["waveform"], fontsize=14, color="black")
        self.waveform_view.canvas.draw()
        if self.audio_array is not None:
            self.waveform_view.update_timeline_position(0, self.duration)
            self.control_panel.update_file_info(self.duration, self.channels, self.sample_rate, self.bitrate, self.metadata)