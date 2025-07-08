# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import shlex
from datetime import datetime
import random # ランダムな値を生成するために追加

def download_video(url, base_filename):
    """ニコニコ動画からダウンロード"""
    url = url.strip()
    if not url:
        sys.exit("No video URL provided")
    output_file = f"videos/input_{base_filename}.mp4"
    cmd = f"yt-dlp -o {output_file} {shlex.quote(url)}"
    print(f"Downloading video: {url}")
    subprocess.run(cmd, shell=True, check=True)
    return output_file

def process_video(input_file, output_path):
    """
    革新的な方法で、視認できないほど高威力なグリッチ効果を適用します。
    """
    # FFprobeを使って実際の解像度とフレームレートを取得する
    input_width = 320
    input_height = 240
    input_fps = 30 # デフォルト値
    try:
        probe_cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,avg_frame_rate", "-of", "csv=p=0:s=x",
            input_file
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        parts = result.stdout.strip().split(',')
        if len(parts) >= 2:
            width_height = parts[0].split('x')
            input_width = int(width_height[0])
            input_height = int(width_height[1])
        if len(parts) >= 3:
            try:
                num, den = map(int, parts[2].split('/'))
                input_fps = num / den
            except ValueError:
                pass 
        print(f"Detected input resolution: {input_width}x{input_height}, FPS: {input_fps:.2f}")
    except Exception as e:
        print(f"Could not detect video resolution/FPS, using default {input_width}x{input_height}, {input_fps:.2f}fps. Error: {e}")

    # ランダムなグリッチ値を生成
    random_rotate_angle = round(random.uniform(0.5, 10.0), 2)
    random_geq_factor = random.randint(150, 500)
    random_opacity = round(random.uniform(0.8, 1.0), 2)
    glitch_fps = random.choice([1, 2, 5, 60, 120])
    pixel_block_size = random.randint(8, 32)
    
    noise_freq = round(random.uniform(0.01, 0.5), 2)
    noise_amp = round(random.uniform(0.1, 0.5), 2)

    # filter_complex 文字列をリストで構築し、後で結合する
    filters = []

    # ====== 映像ストリーム1: オリジナルをベースにした破壊的なフィードバック ======
    filters.append("[0:v]split=2[original][feedback_raw];")
    
    filters.append(
        "[feedback_raw]"
        f"fps={glitch_fps},"
        f"scale={input_width}:{input_height},"
        "tpad=start=0.05:stop=2,"
        f"rotate={random_rotate_angle}:ow=rotw({random_rotate_angle}):oh=roth({random_rotate_angle}),"
        f"scale={input_width}:{input_height},"
        "colorchannelmixer="
            "1.8:0.2:0.2:0.2:0.2:1.8:0.2:0.2:0.2:0.2:0.2:1.8,"
        f"geq=random(1)*{random_geq_factor}:random(1)*{random_geq_factor}:random(1)*{random_geq_factor},"
        "gblur=sigma=7:steps=3,"
        f"scale=iw/{pixel_block_size}:ih/{pixel_block_size},"
        f"scale={input_width}:{input_height}:flags=neighbor,"
        "negate,"
        "loop=loop=20:size=1:start=0,"
        "curves=preset=strong_contrast,"
        "setpts=PTS+random(0)*1/TB[glitch_feedback];"
    )

    # ====== 映像ストリーム2: ノイズとカラーフォーマット破壊を組み合わせたレイヤー ======
    filters.append(
        f"color=c=black:s={input_width}x{input_height}:d=10,"
        f"format=yuv444p,"
        f"noise=all=15:alls=20,"
        f"format=rgb24,"
        f"format=yuv420p,"
        f"geq=r='(r(X,Y)+random(0)*100)':g='(g(X,Y)+random(0)*100)':b='(b(X,Y)+random(0)*100)',"
        "setpts=PTS+random(0)*0.8/TB[noise_layer];"
    )

    # ====== 映像ストリーム3: オーディオからの視覚グリッチフィードバック (実験的) ======
    filters.append(
        "[0:a]asplit=2[audio_out][audio_for_video];"
        "[audio_for_video]showvolume=f=0:s=0:o=v:c=0xFFAABBCC,"
        f"geq=g='st(1, gt(abs(st(0, (T*2*PI*{noise_freq})+sin(T*3*PI*{noise_amp}))) , 0.5)*255)',"
        f"scale={input_width}:{input_height},"
        f"setpts=PTS+random(0)*1.2/TB[audio_glitch];"
    )

    # ====== 最終ブレンド ======
    filters.append(
        "[original][glitch_feedback]blend=all_mode=difference:all_opacity=1.0[blend1];"
        "[blend1][noise_layer]blend=all_mode=addition:all_opacity=1.0[blend2];"
        "[blend2][audio_glitch]blend=all_mode=grainmerge:all_opacity=1.0[v];"
    )

    # オーディオはそのまま通過
    filters.append("[audio_out]acopy[a]")

    filter_complex = "".join(filters)

    # エンコード設定
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "35",
        "-profile:v", "baseline",
        "-level", "3.0",
        "-g", str(random.randint(int(input_fps * 5), int(input_fps * 20))),
        "-keyint_min", "1",
        "-sc_threshold", "0",
        "-b:v", "50k",
        "-slices", str(random.randint(8, 32)),
        "-x264-params", "me=dia:subme=0:trellis=0:no-fast-pskip=1:no-dct-decimate=1:nr=5000",
        "-c:a", "aac",
        "-b:a", "32k",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    print("Running ffmpeg command:")
    print(" ".join(cmd))
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Processing complete. Output video: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg command failed with exit code {e.returncode}. This might be an intended part of the extreme glitch process!")
        print(f"Command: {e.cmd}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print("Partial output file generated. It might still contain extreme glitches!")
        else:
            sys.exit("FFmpeg failed to produce any output file. The glitch settings might be too extreme for this input/FFmpeg version. Try slightly reducing random ranges or filter intensities.")

if __name__ == "__main__":
    main()
