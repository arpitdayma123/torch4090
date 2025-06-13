import os
import uuid
import subprocess
import requests
from urllib.parse import urlparse
import runpod
from r2 import R2Uploader
import config
from diffusers.utils import export_to_video


# 初始化 R2 上传器
try:
    r2_uploader = R2Uploader(
        access_key_id=config.R2_ACCESS_KEY_ID,
        secret_access_key=config.R2_SECRET_ACCESS_KEY,
        endpoint=f"https://{config.R2_ACCOUNT_ID}.r2.cloudflarestorage.com", 
        bucket_name=config.R2_BUCKET_NAME,
        public_url=config.R2_PUBLIC_URL,
    )
    print("R2 uploader initialized successfully")
except Exception as e:
    print(f"Failed to initialize R2 uploader: {e}")
    r2_uploader = None


def download_file(url, dest_folder):
    """
    下载远程文件到指定目录
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
        for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1MB per chunk
            if chunk:
                f.write(chunk)

    return local_path


def handler(event):
    """
    RunPod Serverless 主函数
    支持远程 URL 的 audio_path 和 video_path，并上传生成的视频到 R2
    """
    print("Worker Start")
    input_data = event.get("input", {})
    audio_url = input_data.get("audio_path")
    video_url = input_data.get("video_path")

    if not audio_url or not video_url:
        return {"error": "Missing audio_path or video_path"}

    try:
        # 创建唯一临时工作目录
        unique_dir = os.path.join("/tmp", str(uuid.uuid4()))
        audio_dir = os.path.join(unique_dir, "audio")
        video_dir = os.path.join(unique_dir, "video")
        output_dir = os.path.join(unique_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        # 下载音视频
        audio_path = download_file(audio_url, audio_dir)
        video_path = download_file(video_url, video_dir)

        # 执行你的 Python 脚本（不带 --output_path）
        result = subprocess.run(
            ["python", "run.py", "--audio_path", audio_path, "--video_path", video_path],
            capture_output=True,
            text=True,
            check=True
        )


        # 使用 export_to_video 导出为 MP4
        output_video_path = os.path.join(output_dir, "output.mp4")
        fps = 25  # 可从 input 中获取
        export_to_video(frames, output_video_path, fps=fps)

        # 如果未初始化 R2，直接返回成功但无视频链接
        if not r2_uploader:
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "message": "Processing completed but R2 upload failed (not configured)."
            }

        # 上传到 R2
        filename = f"{uuid.uuid4()}.mp4"
        r2_key = f"{config.R2_VIDEO_PREFIX}/{filename}"
        video_url = r2_uploader.upload_file(output_video_path, key=r2_key, content_type="video/mp4")

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "video_url": video_url,
            "message": "Processing and upload completed successfully."
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
        return {"error": str(e)}
    finally:
        # 清理临时目录
        if 'unique_dir' in locals() and os.path.exists(unique_dir):
            for root, dirs, files in os.walk(unique_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(unique_dir)


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
