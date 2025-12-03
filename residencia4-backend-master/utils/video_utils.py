import cv2
import os
import subprocess
import imageio_ffmpeg as ffmpeg


def save_video_snippet(frames, fps, output_path):
    """
    Salva um pequeno trecho do vídeo.
    """
    if not frames:
        print("[VideoUtils] Nenhum frame recebido, vídeo não será salvo.")
        return None

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    height, width, _ = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for frame in frames:
        out.write(frame)

    out.release()
    print(f"[VideoUtils] Trecho de vídeo salvo em: {output_path}")
    return output_path


def generate_thumbnail(video_path: str, output_dir: str) -> str:
    """
    Gera uma thumbnail de um vídeo.

    """
    try:
        os.makedirs(output_dir, exist_ok=True)

        if not os.path.isfile(video_path):
            print(f"[Thumbnail] Arquivo não encontrado: {video_path}")
            return None

        filename = os.path.splitext(os.path.basename(video_path))[0]
        thumbnail_path = os.path.join(output_dir, f"{filename}.jpg")

        ffmpeg_exe = ffmpeg.get_ffmpeg_exe()

        result = subprocess.run([
            ffmpeg_exe, "-y",
            "-i", video_path,
            "-ss", "00:00:00.500",
            "-vframes", "1",
            "-vf", "scale=320:-1",
            "-qscale:v", "4",
            thumbnail_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if result.returncode == 0 and os.path.exists(thumbnail_path):
            print(f"[Thumbnail] Criada via FFmpeg embutido: {thumbnail_path}")
            return thumbnail_path

        print(f"[Thumbnail] FFmpeg embutido falhou. Tentando OpenCV fallback...")

        cap = cv2.VideoCapture(video_path)

        frame = None
        for _ in range(8):
            success, frame = cap.read()
            if not success:
                break

        cap.release()

        if frame is not None:
            height, width = frame.shape[:2]
            new_width = 320
            new_height = int((new_width / width) * height)
            resized = cv2.resize(frame, (new_width, new_height))

            cv2.imwrite(thumbnail_path, resized)
            if os.path.exists(thumbnail_path):
                print(f"[Thumbnail] Criada via OpenCV fallback: {thumbnail_path}")
                return thumbnail_path

        print(f"[Thumbnail] Falha total ao gerar thumbnail.")
        return None

    except Exception as e:
        print(f"[Thumbnail] Erro ao gerar thumbnail: {e}")
        return None
