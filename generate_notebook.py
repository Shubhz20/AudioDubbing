import json

notebook = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {
    "id": "1A"
   },
   "source": [
    "# The Golden 15 Seconds - Automated Colab Testing Pipeline \u2728\n",
    "This notebook provides a 1-click execution setup for testing the `dub_video.py` code. **Make sure you have changed your runtime to a T4 GPU.**"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {
    "id": "2B"
   },
   "outputs": [],
   "source": [
    "# 1. Clone the repository and setup directories\n",
    "!git clone https://github.com/Shubhz20/AudioDubbing.git\n",
    "%cd AudioDubbing\n",
    "\n",
    "!apt-get update && apt-get install -y ffmpeg\n",
    "\n",
    "# 2. Install dependencies\n",
    "!pip install faster-whisper deep-translator TTS \n",
    "!pip install gdown\n",
    "\n",
    "# 3. Clone Wav2Lip and download checkpoints natively\n",
    "!git clone https://github.com/Rudrabha/Wav2Lip.git\n",
    "!mkdir -p Wav2Lip/checkpoints Wav2Lip/face_detection/detection/sfd\n",
    "!wget -c -O Wav2Lip/face_detection/detection/sfd/s3fd-619a316812.pth \"https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth\"\n",
    "!wget -c -O Wav2Lip/checkpoints/wav2lip_gan.pth \"https://huggingface.co/camenduru/Wav2Lip/resolve/main/checkpoints/wav2lip_gan.pth\""
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {
    "id": "3C"
   },
   "outputs": [],
   "source": [
    "# 4. Download User's Original Reference Video using gdown\n",
    "!gdown \"1uDzLVEow_gAJsXnNjbSoskzVLZ4d7opW\" -O training_video.mp4"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {
    "id": "4D"
   },
   "outputs": [],
   "source": [
    "# 5. Run the End-to-End Deep Learning Pipeline!\n",
    "# Please wait 5-10 minutes. The script suppresses Coqui XTTS Interactive TOS prompts.\n",
    "!python dub_video.py --video \"training_video.mp4\" --start \"00:00:15\" --duration 12"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {
    "id": "5E"
   },
   "outputs": [],
   "source": [
    "# 6. Play the Final High-Fidelity Lip-Synced output!\n",
    "from IPython.display import HTML\n",
    "from base64 import b64encode\n",
    "\n",
    "try:\n",
    "    mp4 = open('output/final_dubbed_segment.mp4','rb').read()\n",
    "    data_url = \"data:video/mp4;base64,\" + b64encode(mp4).decode()\n",
    "    display(HTML(f\"\"\"\n",
    "    <video width=400 controls>\n",
    "        <source src=\"{data_url}\" type=\"video/mp4\">\n",
    "    </video>\n",
    "    \"\"\"))\n",
    "except FileNotFoundError:\n",
    "    print(\"Output video not found. Ensure the pipeline cell finished successfully above.\\nNote: You can also download it from the left 'Files' sidebar.\")"
   ]
  }
 ],
 "metadata": {
  "colab": {
   "provenance": []
  },
  "kernelspec": {
   "display_name": "Python 3",
   "name": "python3"
  },
  "language_info": {
   "name": "python"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 0
}

with open("Golden_15_Seconds_Colab.ipynb", "w") as f:
    json.dump(notebook, f, indent=1)
