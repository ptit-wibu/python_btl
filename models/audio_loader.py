import os
from pydub import AudioSegment
import librosa
from mutagen import File as MutagenFile

class AudioLoader:
    def load_audio(self, file_path):
        try:
            audio = AudioSegment.from_file(file_path)
            channels = audio.channels
            if channels not in [1, 2]:
                raise ValueError(f"Unsupported number of channels: {channels}. Only mono or stereo is supported.")
            audio_array, sample_rate = librosa.load(file_path, mono=False, sr=None)
            bitrate = audio.frame_width * audio.frame_rate * 8
            duration = len(audio) / 1000.0
            metadata = MutagenFile(file_path)
            metadata_dict = {
                "title": metadata.get("title", ["Unknown"])[0] if metadata else "Unknown",
                "artist": metadata.get("artist", ["Unknown"])[0] if metadata else "Unknown",
                "size": os.path.getsize(file_path) / (1024 * 1024)
            }
            return audio, audio_array, sample_rate, channels, duration, bitrate, metadata_dict
        except Exception as e:
            raise Exception(f"Error loading audio: {str(e)}")
        finally:
            import gc
            gc.collect()