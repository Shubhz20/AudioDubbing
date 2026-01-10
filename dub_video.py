import os
import subprocess
import logging
import wave

# Suppress the Coqui XTTS Terms of Service Interactive Prompt
os.environ["COQUI_TOS_AGREED"] = "1"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from faster_whisper import WhisperModel
except ImportError:
    logging.warning("faster_whisper not found. Install it using: pip install faster-whisper")

try:
    from deep_translator import GoogleTranslator
except ImportError:
    logging.warning("deep_translator not found. Install it using: pip install deep-translator")

try:
    from TTS.api import TTS
    import torch
except ImportError:
    logging.warning("TTS not found. Install it using: pip install TTS")


class AudioTranscription:
    def __init__(self, model_size="base", device="cuda"):
        compute_type = "float16" if device == "cuda" else "int8"
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str) -> list:
        logging.info(f"Transcribing {audio_path}...")
        segments, info = self.model.transcribe(audio_path, beam_size=5)
        
        result_segments = []
        for segment in segments:
            result_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
            logging.info(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        
        return result_segments


class TextTranslator:
    def __init__(self, source_lang="en", target_lang="hi"):
        """Initialize TextTranslator with specific language pair"""
        self.translator = GoogleTranslator(source=source_lang, target=target_lang)

    def translate(self, text: str) -> str:
        logging.info(f"Translating: {text}")
        translation = self.translator.translate(text)
        logging.info(f"Translation: {translation}")
        return translation


class VoiceCloner:
    def __init__(self, device="cuda"):
        self.device = device
        self.tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False, gpu=(device=="cuda"))

    def clone(self, text: str, reference_audio: str, output_path: str, language="hi"):
        logging.info(f"Cloning voice in '{language}'. Outputting to {output_path}")
        self.tts.tts_to_file(
            text=text,
            speaker_wav=reference_audio,
            language=language,
            file_path=output_path
        )


class LipSyncer:
    def __init__(self, method="wav2lip", work_dir="./output"):
        self.method = method.lower()
        self.work_dir = work_dir
        os.makedirs(self.work_dir, exist_ok=True)
    
    def sync(self, video_path: str, audio_path: str, output_path: str):
        logging.info(f"Starting Lip Sync using {self.method}...")
        
        if self.method == "videoretalking":
            self._run_videoretalking(video_path, audio_path, output_path)
        elif self.method == "wav2lip":
            self._run_wav2lip(video_path, audio_path, output_path)
        else:
            raise ValueError(f"Unsupported lip-sync method: {self.method}")

    def _run_videoretalking(self, video_path, audio_path, output_path):
        import shlex
        cmd = [
            "python", "VideoReTalking/inference.py",
            "--face", video_path,
            "--audio", audio_path,
            "--outfile", output_path
        ]
        logging.info(f"Executing: {shlex.join(cmd)}")
        subprocess.run(cmd, check=True)

    def _run_wav2lip(self, video_path, audio_path, output_path):
        import shlex
        cmd = [
            "python", "Wav2Lip/inference.py",
            "--checkpoint_path", "Wav2Lip/checkpoints/wav2lip_gan.pth",
            "--face", video_path,
            "--audio", audio_path,
            "--outfile", output_path
        ]
        logging.info(f"Executing: {shlex.join(cmd)}")
        subprocess.run(cmd, check=True)


class VideoDubberPipeline:
    def __init__(self, video_path: str, output_dir: str):
        self.video_path = video_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        try:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        except NameError:
            self.device = "cpu"
        
        logging.info(f"Initializing pipeline components on {self.device.upper()}...")
        self.transcriber = AudioTranscription(device=self.device)
        self.translator = TextTranslator()
        self.cloner = VoiceCloner(device=self.device)
        self.syncer = LipSyncer(method="wav2lip", work_dir=self.output_dir)

    def run(self, start_time: str = "00:00:15", duration_sec: int = 15):
        logging.info("--- Starting 'The Golden 15 Seconds' Pipeline ---")
        
        segment_video = os.path.join(self.output_dir, "segment.mp4")
        self._ffmpeg_extract(self.video_path, segment_video, start_time, str(duration_sec))
        
        segment_audio = os.path.join(self.output_dir, "reference_audio.wav")
        self._extract_audio(segment_video, segment_audio)
        
        segments = self.transcriber.transcribe(segment_audio)
        full_text = " ".join([seg['text'] for seg in segments])
        
        hindi_text = self.translator.translate(full_text)
        
        raw_hindi_audio = os.path.join(self.output_dir, "hindi_audio_raw.wav")
        self.cloner.clone(hindi_text, reference_audio=segment_audio, output_path=raw_hindi_audio, language="hi")
        
        adjusted_hindi_audio = os.path.join(self.output_dir, "hindi_audio_synced.wav")
        self._match_audio_duration(raw_hindi_audio, adjusted_hindi_audio, float(duration_sec))
        
        final_output = os.path.join(self.output_dir, "final_dubbed_segment.mp4")
        self.syncer.sync(segment_video, adjusted_hindi_audio, final_output)
        
        logging.info(f"Pipeline complete! ✨ High-fidelity output saved at: {final_output}")

    def _ffmpeg_extract(self, input_path, output_path, start_time, duration):
        cmd = [
            "ffmpeg", "-y", "-i", input_path, 
            "-ss", start_time, "-t", duration, 
            "-c:v", "libx264", "-c:a", "aac", output_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _extract_audio(self, video_path, audio_path):
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1", audio_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _match_audio_duration(self, input_audio, output_audio, target_seconds):
        with wave.open(input_audio, 'r') as w:
            frames = w.getnframes()
            rate = w.getframerate()
            duration = frames / float(rate)
        
        ratio = duration / target_seconds
        
        filters = []
        temp_ratio = ratio
        while temp_ratio > 2.0:
            filters.append("atempo=2.0")
            temp_ratio /= 2.0
        while temp_ratio < 0.5:
            filters.append("atempo=0.5")
            temp_ratio /= 0.5
        filters.append(f"atempo={temp_ratio}")
        filter_str = ",".join(filters)
        
        cmd = [
            "ffmpeg", "-y", "-i", input_audio,
            "-filter:a", filter_str, output_audio
        ]
        logging.info(f"Adjusting audio tempo by {ratio:.2f}x to match exact {target_seconds}s video duration.")
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI Video Dubbing Pipeline (Golden 15 Seconds)")
    parser.add_argument("--video", required=True, help="Path to the source generic video.")
    parser.add_argument("--outdir", default="./output", help="Directory where processed files are outputted.")
    parser.add_argument("--start", default="00:00:15", help="Start timestamp, e.g., '00:00:15'")
    parser.add_argument("--duration", type=int, default=15, help="Duration of the segment to process in seconds.")
    args = parser.parse_args()

    pipeline = VideoDubberPipeline(video_path=args.video, output_dir=args.outdir)
    try:
        pipeline.run(start_time=args.start, duration_sec=args.duration)
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
