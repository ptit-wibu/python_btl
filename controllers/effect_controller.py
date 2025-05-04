import multiprocessing as mp

from models.vocal_separator import VocalSeparator

def separate_vocal_worker(audio_array, sample_rate, channels, queue):
    try:
        separator = VocalSeparator()
        vocal, instrumental = separator.separate_vocal(audio_array, sample_rate, channels)
        queue.put(("success", vocal, instrumental))
    except Exception as e:
        queue.put(("error", str(e)))

class EffectController:
    def __init__(self, processor, exporter, control_panel, waveform_view):
        self.processor = processor
        self.exporter = exporter
        self.control_panel = control_panel
        self.waveform_view = waveform_view

    def _separate_vocal_thread(self, audio_array, sample_rate, channels, queue):
        try:
            vocal, instrumental = self.processor.separate_vocal(audio_array, sample_rate, channels)
            queue.put(("success", vocal, instrumental))
        except Exception as e:
            queue.put(("error", str(e)))