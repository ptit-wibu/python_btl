'''
import numpy as np
import librosa

class VocalSeparator:
    def separate_vocal(self, audio_array, sample_rate, channels):
        audio_array = librosa.to_mono(audio_array) if len(audio_array.shape) > 1 else audio_array
        S_full, phase = librosa.magphase(librosa.stft(audio_array))
        S_filter = librosa.decompose.nn_filter(S_full)
        S_foreground = np.minimum(S_full, S_filter)
        S_background = S_full - S_foreground
        vocal = librosa.istft(S_foreground * phase)
        instrumental = librosa.istft(S_background * phase)
        if channels == 2:
            vocal = np.array([vocal, vocal])
            instrumental = np.array([instrumental, instrumental])
        return vocal, instrumental
'''
'''
import numpy as np
import librosa

class VocalSeparator:
    def separate_vocal(self, audio_array, sample_rate, channels):
        # Chuyển sang mono nếu là stereo
        if len(audio_array.shape) > 1:
            audio_array = librosa.to_mono(audio_array)
        
        # Tính STFT
        S_full, phase = librosa.magphase(librosa.stft(audio_array))
        
        # Tính filter với tham số cụ thể
        width = int(librosa.time_to_frames(2, sr=sample_rate))
        S_filter = librosa.decompose.nn_filter(S_full, aggregate=np.median, metric='cosine', width=width)
        
        # Đặt margin cho soft-masking
        margin_i = 2
        margin_v = 10
        power = 2
        
        # Tính softmasks với đảm bảo không âm
        X_i = S_filter
        X_ref_i = np.maximum(0, margin_i * (S_full - S_filter))
        mask_i = librosa.util.softmask(X_i, X_ref_i, power=power)
        
        X_v = np.maximum(0, S_full - S_filter)
        X_ref_v = margin_v * S_filter
        mask_v = librosa.util.softmask(X_v, X_ref_v, power=power)
        
        # Tách thành phần
        S_foreground = mask_v * S_full  # Vocal
        S_background = mask_i * S_full  # Instrumental
        
        # Tái tạo âm thanh
        vocal = librosa.istft(S_foreground * phase)
        instrumental = librosa.istft(S_background * phase)
        
        # Nếu gốc là stereo, nhân đôi kênh
        if channels == 2:
            vocal = np.array([vocal, vocal])
            instrumental = np.array([instrumental, instrumental])
        
        return vocal, instrumental
'''
from spleeter.separator import Separator
import numpy as np
import librosa

class VocalSeparator:
    def __init__(self):
        self.separator = Separator('spleeter:2stems')
    
    def separate_vocal(self, audio_array, sample_rate, channels):
        # Đảm bảo audio ở định dạng float32
        if audio_array.dtype != np.float32:
            audio_array = audio_array.astype(np.float32)
        
        # Resample về 44100 Hz nếu cần
        if sample_rate != 44100:
            audio_array = librosa.resample(audio_array, orig_sr=sample_rate, target_sr=44100)
            sample_rate = 44100
        
        # Nếu là mono, chuyển sang stereo
        if len(audio_array.shape) == 1:
            audio_array = np.stack([audio_array, audio_array], axis=-1)
        elif audio_array.shape[0] == 2:
            audio_array = audio_array.T  # Spleeter mong đợi (samples, channels)
        
        # Tách bằng Spleeter
        separation = self.separator.separate(audio_array)
        
        # Lấy vocal và accompaniment
        vocal = separation['vocals'].T  # Chuyển lại về (channels, samples)
        instrumental = separation['accompaniment'].T
        
        # Nếu gốc là mono, lấy một kênh
        if channels == 1:
            vocal = vocal[0]
            instrumental = instrumental[0]
        
        return vocal, instrumental