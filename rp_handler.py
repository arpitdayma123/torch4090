import os
import subprocess
import requests
from urllib.parse import urlparse
import runpod
from r2 import R2Uploader


def download_file(url, dest_folder):
    """
    下载文件到指定目录
    """
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)

    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    local_path = os.path.join(dest_folder, filename)

    print(f"Downloading {url} to {local_path}")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

    return local_path


def handler(event):
    """
    RunPod Serverless 处理函数
    支持本地路径或 URL 的 audio_path 和 video_path
    """
    # 获取输入参数
    input_data = event.get("input", {})
    audio_url = input_data.get("audio_path")
    video_url = input_data.get("video_path")

    if not audio_url or not video_url:
        return {"error": "Missing audio_path or video_path"}

    try:
        # 下载音视频文件到 /tmp/
        audio_path = download_file(audio_url, "/tmp/audio")
        video_path = download_file(video_url, "/tmp/video")

        # 执行你的 Python 脚本
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

    except requests.RequestException as e:
        return {"error": f"Download failed: {str(e)}"}
    except subprocess.CalledProcessError as e:
        return {
            "error": "Script execution failed",
            "stdout": e.stdout,
            "stderr": e.stderr
        }
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


#
# Start the Serverless function when the script is run
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
