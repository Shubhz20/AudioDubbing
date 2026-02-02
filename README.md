# Supernan AI Automation Intern: The Golden 15 Seconds

## Overview

This repository contains the solution for "The Golden 15 Seconds" dubbing pipeline. The goal is to take an english training video, segment out the exact 15-30s timeframe, transcribe and translate the contents into contextually aware Hindi, clone the speaker's voice, and re-lip-sync the dubbed video maintaining incredibly high standards for visual and audio sync.

**Budget constraints adhered to:** ₹0. Completely open-sourced stack built to run perfectly on Colab's Free Tier GPUs.

## 🚀 Setup Instructions (Google Colab Recommended)

Because of the high VRAM requirements for processing audio transcription, voice cloning (XTTS), and video re-talking natively concurrently, **the free tier of Google Colab (T4 GPU) is the recommended and verified environment.**

1. Clone this repository directly onto your Google Colab workspace:

```bash
!git clone https://github.com/<YOUR_GITHUB_REPO_LINK>
%cd <YOUR_GITHUB_REPO_NAME>
```

2. Install dependencies:

```bash
!pip install -r requirements.txt
!apt-get update && apt-get install -y ffmpeg
```

3. Prepare the underlying Lip-Sync submodules. If using `Wav2Lip` (fastest for Colab Free T4 testing):

```bash
!git clone https://github.com/Rudrabha/Wav2Lip.git
# Note: You must manually download the wav2lip_gan.pth checkpoint
# and move it to Wav2Lip/checkpoints/wav2lip_gan.pth
```

4. Run the pipeline passing your video link:

```bash
!python dub_video.py --video "downloaded_train_video.mp4" --start "00:00:15" --duration 15
```

5. Check `./output/final_dubbed_segment.mp4` for your visually unblurred, fully Hindi translated golden 15 seconds.

## 📦 All Dependencies

See `requirements.txt`. Main components include:

- `faster-whisper`: Optimized Whisper implementation for extremely fast and accurate VRAM-friendly transcription.
- `TTS` (Coqui): Best-in-class multi-lingual open source zero-shot voice cloning engine (XTTS v2).
- `deep-translator`: Zero-budget Google translation wrapper used to quickly test context without setting up IndicTrans2 directly in a notebook.
- `ffmpeg-python & ffmpeg`: For precise audio extraction, segment processing, and strict timescale filtering.
- `Wav2Lip / VideoReTalking`: Face and Lip-Sync engines.

## 💸 Cost per Minute of Video at Scale

We can operate near **$0.01 per minute** or drastically less if managed via self-hosted cloud GPUs rather than API wrappers (e.g. ElevenLabs = ~$0.30 per min, OpenAI Whisper API = $0.006 per min, Video APIs extremely overpriced).

- **Self-Hosted Setup (RunPod/Lambda A6000 Or RTX 4090 @ $0.30/hr - $0.70/hr):**
  - **1 Minute of Whisper Transcribe:** < 3 seconds
  - **1 Minute of Translate:** < 1 second using cached/batched inference.
  - **1 Minute of XTTS v2 Inference:** ~20-30 seconds
  - **1 Minute of VideoReTalking/GFPGAN Lip-Sync:** ~1.5 - 2 minutes on powerful nodes.
- **Estimated total self-hosted hardware cost per minute of video**: **~$0.005 — $0.015** assuming optimal node utilization queueing. Extremely sustainable for a startup.

## 🚀 The Scale Question (500 Hours Overnight)

**"How would you modify this script to process 500 hours of video overnight if we gave you a budget?"**

If we need to process `30,000` minutes (500 hours) in roughly `12` hours overnight, we must process ~42 hours of video concurrently per hour (or ~0.7 hours processed per minute).

**My Scalable Microservices Architecture:**

1.  **Stop Monolithic Pipelines:** I would decouple `dub_video.py` into 4 standalone microservices Docker containers (Transcription API, Translation API, AudioTTS API, SyncVideo API).
2.  **Message Queueing (RabbitMQ/Celery):** We deploy RabbitMQ. The 500-hour video pool is indexed and split into strict `2-minute max` audio overlapping chunks before entering the message queue. This dramatically prevents long-form memory leaks, timeline drifting, and Out-of-Memory (OOM) errors.
3.  **Compute Orchestration (Kubernetes/KEDA):**
    - **Whisper / Translate Worker Pods:** Whisper models and LLaMA 8b for translations execute rapidly. We map these generic pods to cheap T4 / RTX 3060 Spot Nodes on Runpod/AWS.
    - **Coqui XTTS Worker Pods:** XTTS requires significant loading. The scripts keep the `tts_models` hot-loaded continuously across a pool of A10s/A5000s, pulling from the queue sequentially allowing completely voided "cold boot" initializations.
    - **Lip Sync Video Worker Pods:** VideoReTalking with GFPGAN is extremely GPU intensive. We rent multiple fleets of A100s exclusively listening to the final stage of the queue whose only task is rendering the frames and audio together.
4.  **Re-Assembly Engine:** A low-cost memory-heavy CPU node runs `ffmpeg concat demuxer` using Amazon S3 mapped object stores to rapidly concatenate the finalized 2-minute video snippets back into full videos cleanly.

## 🔧 Known Limitations

- **Duration Discrepancies:** Hindi naturally takes larger syllabic spans to speak than English. Because we rigidly fit the generated Hindi voice back into an exact 15-second structural window using `ffmpeg atempo` filters, there can be slight distortions if the translated length was heavily disproportional. Dynamic padding resolves this.
- **Resolution vs Computation:** Native Wav2Lip often degrades facial resolutions causing a blurring artifact around the mouth. Our script supports utilizing `method="videoretalking"` which natively invokes CodeFormer/GFPGAN integrations to keep the nanny's face exquisitely sharp while still maintaining perfect sync lock.

## 🌟 What I'd Improve with More Time

- **Silences & Voice Activity Detection (VAD):** Integrate `Pyannote` to segment out non-speaking/background noise segments dynamically so the XTTS voice isn't attempting to "hallucinate" lip-smacks.
- **LLM Context-Aware Prompts:** I'd rip out `deep_translator` and invoke a local LLM or fast generic API fed with system logic: _"Translate this instructional nanny dialogue into friendly, conversational, culturally empathetic Hindi without stiff phrasing."_
- **Pitch Tracing & Intonation:** Extract pitch curves from the original English audio snippet using Librosa, mapping them natively over the Hindi result, so the TTS engine replicates identical human emotional inflections instead of an entirely standard readout.


## License
This project is licensed under the MIT License.
