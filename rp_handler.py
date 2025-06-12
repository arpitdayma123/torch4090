import os
import subprocess
from runpod.serverless.module.rp_handler import rp_serve

def handler(event):
    """
    RunPod Serverless 处理函数
    接收 audio_path 和 video_path 参数，并运行 run.py
    """
    # 获取输入参数
    audio_path = event.get("input", {}).get("audio_path")
    video_path = event.get("input", {}).get("video_path")

    if not audio_path or not video_path:
        return {"error": "Missing audio_path or video_path"}

    if not os.path.exists(audio_path) or not os.path.exists(video_path):
        return {"error": "Audio or Video file does not exist"}

    # 执行你的 Python 脚本
    try:
        result = subprocess.run(
            ["python", "run.py", "--audio_path", audio_path, "--video_path", video_path],
            capture_output=True,
            text=True,
            check=True
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "message": "Processing completed successfully."
        }
    except subprocess.CalledProcessError as e:
        return {
            "error": "Script execution failed",
            "stdout": e.stdout,
            "stderr": e.stderr
        }

# 启动 Serverless 服务
rp_serve(handler)
