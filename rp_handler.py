import os
import uuid
import subprocess
import requests
from urllib.parse import urlparse
import runpod
from r2 import R2Uploader
import config
from diffusers.utils import export_to_video
from PIL import Image
import numpy as np
import shutil


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

    # 设置 matplotlib 缓存目录
    mpl_cache_dir = "/tmp/matplotlib_cache"
    os.makedirs(mpl_cache_dir, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = mpl_cache_dir

    input_data = event.get("input", {})
    audio_url = input_data.get("audio_path")
    video_url = input_data.get("video_path")

    if not audio_url or not video_url:
        return {"error": "Missing audio_path or video_path"}

    unique_dir = None
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

        # 执行你的 Python 脚本
        result = subprocess.run(
            ["python", "run.py", "--audio_path", audio_path, "--video_path", video_path],
            capture_output=True,
            text=True,
            check=True
        )

        # 自动探测当前目录下的 PNG/JPG 图像帧
        image_files = [f for f in os.listdir(".") if f.endswith(".png") or f.endswith(".jpg")]
        if not image_files:
            raise FileNotFoundError("No image files found for video export")

        # 加载图像帧为 NumPy 数组
        frames = np.array([np.array(Image.open(img)) for img in sorted(image_files)])

        # 导出为 MP4
        output_video_path = os.path.join(output_dir, "output.mp4")
        fps = input_data.get("fps", 25)
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
        if unique_dir and os.path.exists(unique_dir):
            try:
                shutil.rmtree(unique_dir)
            except Exception as e:
                print(f"Failed to remove tmp dir: {str(e)}")

        # 清理图像帧
        image_files = [f for f in os.listdir(".") if f.endswith((".png", ".jpg"))]
        for f in image_files:
            try:
                os.remove(f)
            except Exception as e:
                print(f"Failed to remove file {f}: {str(e)}")


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
