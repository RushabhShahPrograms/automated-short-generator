# Automated Shorts Generator


## Tested And Build on Legion 5 15ACH6
- Nvidia RTX 3050 4GB VRAM GPU
- 16GB RAM
- AMD Ryzen 7 5800H CPU
- Windows 11

This is still under development and take time to build it properly.


Until then if you want to test it, then follow this steps:
```
conda create -n automated-short-generator python==3.11
conda activate automated-short-generator
pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 --index-url https://download.pytorch.org/whl/cu118
pip install -e .
pip install -r requirements.txt
python main.py
```

This will open PyQt6 UI where we can do our work.

From here generate your google gemini api key: [Google AI Studio](https://aistudio.google.com/welcome)


## Flow
- Used gemini model to create the short text of what we want to talk.
- Then used F5-TTS which will take those text and user has to just provide one 15 second reference audio (either english or chinese) then F5-TTS will convert the text into the human like audio based on the reference audio provided.
- And you will be able to download the audio
- Added option to merge this audio with the video and even provide hard subtitles for the video
- Using whisper large-v2 model for generating subtitles
- Using FFmpeg I am merging the generated audio and the subtitles.srt file created by whisper in one single video.
