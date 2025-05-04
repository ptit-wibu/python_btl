import numpy as np
import librosa
from pydub import AudioSegment

class AudioProcessor:
    def cut_audio(self, audio, start_time, end_time, duration):
        start_ms = start_time * 1000
        end_ms = end_time * 1000
        if start_ms < 0 or end_ms > duration * 1000 or start_ms >= end_ms:
            raise ValueError(f"Cut times out of range (max: {duration:.3f}s)")
        return audio[start_ms:end_ms]

    def change_volume(self, gain, audio):
        return audio + gain

    def change_speed(self, speed, audio_array, sample_rate):
        if len(audio_array.shape) > 2:
            raise ValueError("Unsupported audio format")
        if len(audio_array.shape) > 1:
            audio_changed = np.array([librosa.effects.time_stretch(audio_array[i], rate=speed) for i in range(audio_array.shape[0])])
        else:
            audio_changed = librosa.effects.time_stretch(audio_array, rate=speed)
        return audio_changed, sample_rate

    def change_pitch(self, n_steps, audio_array, sample_rate):
        if len(audio_array.shape) > 2:
            raise ValueError("Unsupported audio format")
        if len(audio_array.shape) > 1:
            audio_changed = np.array([librosa.effects.pitch_shift(audio_array[i], sr=sample_rate, n_steps=n_steps) for i in range(audio_array.shape[0])])
        else:
            audio_changed = librosa.effects.pitch_shift(audio_array, sr=sample_rate, n_steps=n_steps)
        return audio_changed, sample_rate

    def add_reverb(self, audio, channels, wet_level=0.2):
        if isinstance(audio, AudioSegment):
            audio_array = np.array(audio.get_array_of_samples())
            if channels == 2:
                audio_array = audio_array.reshape(-1, 2)
        else:
            audio_array = audio * (2**15)
        if len(audio_array.shape) > 1:
            reverb = np.array([np.convolve(audio_array[:, i], np.ones(1000) * wet_level, mode='same') for i in range(audio_array.shape[1])]).T
        else:
            reverb = np.convolve(audio_array, np.ones(1000) * wet_level, mode='same')
        reverb = reverb / np.max(np.abs(reverb))
        reverb = (reverb * 32767).astype(np.int16)
        return reverb

    def add_echo(self, audio, delay_ms=500, decay=0.5):
        delay_samples = int(audio.frame_rate * (delay_ms / 1000))
        echo = AudioSegment.silent(duration=len(audio) + delay_ms)
        echo = echo.overlay(audio, position=0)
        echo = echo.overlay(audio - 10 * decay, position=delay_samples)
        return echo[:len(audio)]

    def fade_in_out(self, audio, fade_in_ms=1000, fade_out_ms=1000):
        return audio.fade_in(fade_in_ms).fade_out(fade_out_ms)

    def apply_equalizer(self, audio_array, sample_rate, channels, bass_gain=0, mid_gain=0, treble_gain=0):
        audio_array = librosa.to_mono(audio_array) if len(audio_array.shape) > 1 else audio_array
        stft = librosa.stft(audio_array)
        freqs = librosa.fft_frequencies(sr=sample_rate)
        bass_mask = (freqs < 200)
        mid_mask = (freqs >= 200) & (freqs <= 2000)
        treble_mask = (freqs > 2000)
        stft[bass_mask] *= 10 ** (bass_gain / 20)
        stft[mid_mask] *= 10 ** (mid_gain / 20)
        stft[treble_mask] *= 10 ** (treble_gain / 20)
        audio_changed = librosa.istft(stft)
        if channels == 2:
            audio_changed = np.array([audio_changed, audio_changed])
        return audio_changed, sample_rate

    def detect_beats(self, audio_array, sample_rate):
        audio_array = librosa.to_mono(audio_array) if len(audio_array.shape) > 1 else audio_array
        tempo, beat_frames = librosa.beat.beat_track(y=audio_array, sr=sample_rate)
        beat_times = librosa.frames_to_time(beat_frames, sr=sample_rate)
        return beat_times, tempo