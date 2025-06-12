#!/bin/bash

WEIGHTS_DIR="/apps/HeyGem/landmark2face_wy/checkpoints/anylang/"
WEIGHTS_FILE="$WEIGHTS_DIR/your_model_weights.pth"

# 检查模型权重是否存在
if [ ! -f "$WEIGHTS_FILE" ]; then
    echo "Weights not found. Downloading..."
    cd /apps/HeyGem/ && bash download.sh
else
    echo "Weights already exist. Skipping download."
fi

echo "Starting sleep infinity..."
#sleep infinity

#python run.py --audio_path example/audio.wav --video_path example/video.mp4

python /rp_handler.py
