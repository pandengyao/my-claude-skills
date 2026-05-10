#!/usr/bin/env python3
"""三引擎 ASR 转写脚本 — SenseVoice + Paraformer + Whisper 综合输出。

用法:
    python3 asr.py <audio_file> [--output-dir DIR] [--skip-whisper]

始终运行三引擎（SenseVoice-Small、Paraformer-large、Whisper large），
输出各引擎结果的 JSON 供后续交叉校正使用。

注意:
    - Whisper 在 Apple Silicon CPU 上无 GPU 加速，15分钟音频约需 30 分钟
    - 使用 --skip-whisper 可跳过 Whisper（仅 SenseVoice + Paraformer 双引擎）
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time


def run_sensevoice(audio_path):
    """SenseVoice-Small + VAD 转写。

    ⚠️ 关键: 必须配合 vad_model 使用，否则长音频(>30s)会输出乱码！
    """
    from funasr import AutoModel

    print("[SenseVoice] Loading model with VAD...", file=sys.stderr)
    t0 = time.time()

    model = AutoModel(
        model="iic/SenseVoiceSmall",
        trust_remote_code=True,
        disable_update=True,
        vad_model="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
        vad_kwargs={"max_single_segment_time": 30000},
    )

    print(f"[SenseVoice] Model loaded in {time.time() - t0:.1f}s", file=sys.stderr)
    print(f"[SenseVoice] Transcribing...", file=sys.stderr)
    t0 = time.time()

    result = model.generate(
        input=audio_path,
        language="zh",
        use_itn=True,
        batch_size_s=300,
    )

    elapsed = time.time() - t0
    print(f"[SenseVoice] Done in {elapsed:.1f}s", file=sys.stderr)

    text = result[0]["text"] if result else ""
    text = re.sub(r"<\|[^|]*\|>", "", text).strip()

    return {
        "engine": "sensevoice-small",
        "text": text,
        "elapsed_seconds": round(elapsed, 1),
    }


def run_paraformer(audio_path):
    """Paraformer-large + VAD + CT-Transformer 标点恢复。"""
    from funasr import AutoModel

    print("[Paraformer] Loading model with VAD + punctuation...", file=sys.stderr)
    t0 = time.time()

    model = AutoModel(
        model="iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        vad_model="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
        punc_model="iic/punc_ct-transformer_cn-en-common-vocab471067-large",
        disable_update=True,
    )

    print(f"[Paraformer] Model loaded in {time.time() - t0:.1f}s", file=sys.stderr)
    print(f"[Paraformer] Transcribing...", file=sys.stderr)
    t0 = time.time()

    result = model.generate(input=audio_path, batch_size_s=300)

    elapsed = time.time() - t0
    print(f"[Paraformer] Done in {elapsed:.1f}s", file=sys.stderr)

    text = result[0]["text"] if result else ""
    timestamps = result[0].get("timestamp") if result else None

    return {
        "engine": "paraformer-large",
        "text": text,
        "timestamps": timestamps,
        "elapsed_seconds": round(elapsed, 1),
    }


def run_whisper(audio_path, output_dir=None):
    """Whisper large-v3 转写（子进程调用）。

    注意: Apple Silicon CPU 上无 GPU 加速，15分钟音频约需 30 分钟。
    """
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(audio_path)) or "."

    print("[Whisper] Starting whisper large (CPU, may take 30+ min for 15min audio)...", file=sys.stderr)
    t0 = time.time()

    cmd = [
        "whisper", audio_path,
        "--language", "zh",
        "--model", "large",
        "--output_format", "json",
        "--output_dir", output_dir,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - t0

    if proc.returncode != 0:
        print(f"[Whisper] Error: {proc.stderr}", file=sys.stderr)
        return {
            "engine": "whisper-large",
            "text": "",
            "error": proc.stderr,
            "elapsed_seconds": round(elapsed, 1),
        }

    print(f"[Whisper] Done in {elapsed:.1f}s", file=sys.stderr)

    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    json_path = os.path.join(output_dir, f"{base_name}.json")

    text = ""
    segments = []
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            whisper_result = json.load(f)
            text = whisper_result.get("text", "")
            segments = whisper_result.get("segments", [])

    return {
        "engine": "whisper-large",
        "text": text,
        "segments": segments,
        "elapsed_seconds": round(elapsed, 1),
    }


def main():
    parser = argparse.ArgumentParser(
        description="三引擎 ASR 转写 (SenseVoice + Paraformer + Whisper)"
    )
    parser.add_argument("audio_file", help="音频文件路径")
    parser.add_argument("--output-dir", default=None, help="输出目录（默认与音频同目录）")
    parser.add_argument("--skip-whisper", action="store_true", help="跳过 Whisper（节省时间）")

    args = parser.parse_args()

    if not os.path.exists(args.audio_file):
        print(f"错误: 文件不存在: {args.audio_file}", file=sys.stderr)
        sys.exit(1)

    results = []

    # 1. SenseVoice（最快，~50s）
    results.append(run_sensevoice(args.audio_file))

    # 2. Paraformer（快，~2min，带标点）
    results.append(run_paraformer(args.audio_file))

    # 3. Whisper（慢，~30min，但质量高）
    if not args.skip_whisper:
        results.append(run_whisper(args.audio_file, args.output_dir))
    else:
        print("[Whisper] Skipped (--skip-whisper)", file=sys.stderr)

    output = {
        "audio_file": os.path.basename(args.audio_file),
        "engines_used": [r["engine"] for r in results],
        "results": results,
        "cross_correction_guide": (
            "交叉校正方法: "
            "1) 按时间段对齐三引擎输出; "
            "2) 多数投票——两个引擎一致时采用多数版本; "
            "3) 三引擎均不同时，结合上下文语义由 LLM 判断最合理版本; "
            "4) 专有名词/术语需结合视频主题确认。"
        ),
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
