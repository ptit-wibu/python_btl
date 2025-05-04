from tkinterdnd2 import TkinterDnD
from models.audio_loader import AudioLoader
from models.audio_processor import AudioProcessor
from models.audio_exporter import AudioExporter
from models.vocal_separator import VocalSeparator
from views.main_view import MainView
from views.control_panel import ControlPanel
from views.waveform_view import WaveformView
from controllers.audio_controller import AudioController
from controllers.effect_controller import EffectController

def main():
    root = TkinterDnD.Tk()
    
    # Khởi tạo models
    model_loader = AudioLoader()
    model_processor = AudioProcessor()
    model_exporter = AudioExporter()
    model_vocal_separator = VocalSeparator()

    # Khởi tạo views
    view_main = MainView(root, None)  # Tạm thời để None cho controller
    view_control = ControlPanel(view_main.main_frame, None, view_main.languages, view_main.current_lang)
    view_waveform = WaveformView(view_main.main_frame, None, view_main.languages, view_main.current_lang)

    # Khởi tạo controllers
    effect_controller = EffectController(model_processor, model_exporter, view_control, view_waveform)
    audio_controller = AudioController(model_loader, model_processor, model_exporter, view_main, view_control, view_waveform, effect_controller)

    # Gán controllers vào views
    view_main.controller = audio_controller
    view_control.controller = audio_controller
    view_waveform.controller = audio_controller

    # Gán controller phụ cho audio_controller
    audio_controller.effect_controller = effect_controller

    # Gán các sự kiện sau khi tất cả controller được thiết lập
    view_main.bind_drop_event()
    view_main.bind_language_event()
    view_control.bind_button_events()
    view_waveform.bind_timeline_event()

    root.mainloop()

if __name__ == "__main__":
    main()