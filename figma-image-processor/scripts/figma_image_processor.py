#!/usr/bin/env python3
"""
Figma image download + compress + CDN upload processor.

Supports two modes:
1) api mode (default): call /api/image-compressor + /api/bos/sts
2) standalone mode: local compression (Pillow) + direct BOS upload (AK/SK)
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import hmac
import http.client
import io
import json
import mimetypes
import os
import re
import sys
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse
from urllib.request import Request, urlopen


QUALITY_PRESETS = {
    "high": 92,
    "balanced": 80,
    "small": 60,
}

SUPPORTED_FORMATS = {"original", "jpeg", "png", "webp", "avif"}
SUPPORTED_MODES = {"api", "standalone"}
LOCAL_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".bmp", ".tif", ".tiff"}


@dataclass
class FigmaImageRef:
    node_id: str
    node_name: str
    node_type: str
    image_ref: str
    download_url: Optional[str]


@dataclass
class ProcessResult:
    success: bool
    node_id: str
    node_name: str
    image_ref: str
    original_size: int = 0
    compressed_size: int = 0
    compression_ratio: float = 0.0
    cdn_url: Optional[str] = None
    downloaded_path: Optional[str] = None
    compressed_path: Optional[str] = None
    error: Optional[str] = None


def parse_file_key(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"[A-Za-z0-9]{22}", value):
        return value

    parsed = urlparse(value)
    if "figma.com" not in parsed.netloc:
        raise ValueError("Input is neither a valid Figma URL nor a file key.")

    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2 and parts[0] in {"design", "file", "proto", "board"}:
        return parts[1]
    raise ValueError("Could not parse file key from URL.")


def fetch_figma_json(url: str, token: str, timeout: int = 120) -> dict:
    req = Request(url, headers={"X-Figma-Token": token})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def iter_image_refs(file_json: dict) -> Iterable[dict]:
    stack: List[dict] = [file_json.get("document", {})]
    path_stack: List[List[str]] = [[]]

    while stack:
        node = stack.pop()
        path = path_stack.pop()
        if not isinstance(node, dict):
            continue

        node_name = str(node.get("name", "")).strip() or "<unnamed>"
        node_id = str(node.get("id", ""))
        node_type = str(node.get("type", ""))
        current_path = path + [node_name]

        for paint_field in ("fills", "strokes", "background"):
            paints = node.get(paint_field, [])
            if not isinstance(paints, list):
                continue
            for paint in paints:
                if not isinstance(paint, dict):
                    continue
                if paint.get("type") == "IMAGE" and paint.get("imageRef"):
                    yield {
                        "node_id": node_id,
                        "node_name": node_name,
                        "node_type": node_type,
                        "node_path": " / ".join(current_path),
                        "image_ref": str(paint["imageRef"]),
                    }

        children = node.get("children", []) or []
        for child in reversed(children):
            if isinstance(child, dict):
                stack.append(child)
                path_stack.append(current_path)


def sanitize_filename(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return sanitized or "image"


def parse_ext_from_url(url: str) -> str:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower().lstrip(".")
    if suffix in {"jpg", "jpeg", "png", "webp", "avif", "gif", "bmp", "tif", "tiff"}:
        return "jpg" if suffix == "jpeg" else suffix
    return "jpg"


def parse_ext_from_path(path_value: str) -> str:
    suffix = Path(path_value).suffix.lower().lstrip(".")
    if suffix in {"jpg", "jpeg", "png", "webp", "avif", "gif", "bmp", "tif", "tiff"}:
        return "jpg" if suffix == "jpeg" else suffix
    return "jpg"


def format_size(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024:
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} TB"


def normalize_ext(ext: str) -> str:
    ext = ext.lower().lstrip(".")
    if ext == "jpeg":
        return "jpg"
    if ext == "tiff":
        return "tif"
    return ext


def guess_content_type(ext: str) -> str:
    ext = normalize_ext(ext)
    if ext == "jpg":
        return "image/jpeg"
    guessed = mimetypes.types_map.get(f".{ext}")
    return guessed or "application/octet-stream"


def build_bce_v1_authorization(ak: str, sk: str, timestamp: str, key: str, host: str) -> str:
    expiration_seconds = 1800
    sign_key_info = f"bce-auth-v1/{ak}/{timestamp}/{expiration_seconds}"
    signing_key = hmac.new(sk.encode("utf-8"), sign_key_info.encode("utf-8"), hashlib.sha256).hexdigest()
    canonical_headers = f"host:{host}"
    canonical_request = f"PUT\n{key}\n\n{canonical_headers}"
    signature = hmac.new(signing_key.encode("utf-8"), canonical_request.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{sign_key_info}/host/{signature}"


class BaseProcessorClient:
    def __init__(self, target_path: str, bucket: str, upload_endpoint: Optional[str] = None) -> None:
        self.target_path = target_path.strip()
        self.bucket = bucket
        self.upload_endpoint = (upload_endpoint or f"https://{bucket}.cdn.bcebos.com").strip()

        if not self.target_path:
            raise ValueError("target-path must not be empty")
        if self.target_path.startswith("/"):
            raise ValueError("target-path must not start with '/'")
        if "//" in self.target_path:
            raise ValueError("target-path must not contain '//'")

        endpoint = urlparse(self.upload_endpoint if "://" in self.upload_endpoint else f"https://{self.upload_endpoint}")
        if not endpoint.hostname:
            raise ValueError("invalid bos endpoint")

        self.endpoint_scheme = endpoint.scheme or "https"
        self.endpoint_host = endpoint.hostname
        self.endpoint_port = endpoint.port or (443 if self.endpoint_scheme == "https" else 80)
        self.endpoint_prefix = endpoint.path.rstrip("/")

    def fetch_image_source(self, image_ref: FigmaImageRef) -> Tuple[bytes, str]:
        if not image_ref.download_url:
            raise RuntimeError("missing download url")
        source = image_ref.download_url
        if source.startswith("/") or re.match(r"^[A-Za-z]:\\", source):
            local_path = Path(source)
            if not local_path.exists():
                raise RuntimeError(f"local file not found: {source}")
            return local_path.read_bytes(), parse_ext_from_path(str(local_path))

        if source.startswith("file://"):
            local_path = Path(source[7:])
            if not local_path.exists():
                raise RuntimeError(f"local file not found: {local_path}")
            return local_path.read_bytes(), parse_ext_from_path(str(local_path))

        req = Request(source, headers={"User-Agent": "figma-image-processor"})
        with urlopen(req, timeout=60) as resp:
            return resp.read(), parse_ext_from_url(source)

    def compress_image(self, image_data: bytes, source_filename: str, source_ext: str) -> Tuple[bytes, str, float]:
        raise NotImplementedError

    def upload_to_cdn(self, key: str, content: bytes, content_type: str) -> str:
        raise NotImplementedError

    def build_base_name(self, image_ref: FigmaImageRef) -> str:
        # Local files should keep business filename; Figma images append a short ref to avoid collisions.
        if image_ref.node_type == "LOCAL_FILE":
            return sanitize_filename(image_ref.node_name)
        return sanitize_filename(f"{image_ref.node_name}_{image_ref.image_ref[:8]}")

    def process_one(
        self,
        image_ref: FigmaImageRef,
        download_dir: Optional[Path],
        output_dir: Optional[Path],
        upload: bool,
    ) -> ProcessResult:
        try:
            original_bytes, source_ext = self.fetch_image_source(image_ref)
            original_size = len(original_bytes)
            source_ext = normalize_ext(source_ext)
            base_name = self.build_base_name(image_ref)
            source_filename = f"{base_name}.{source_ext}"

            downloaded_path = None
            if download_dir is not None:
                download_dir.mkdir(parents=True, exist_ok=True)
                source_path = download_dir / source_filename
                source_path.write_bytes(original_bytes)
                downloaded_path = str(source_path)

            compressed_bytes, output_ext, compression_ratio = self.compress_image(
                original_bytes,
                source_filename,
                source_ext,
            )
            output_ext = normalize_ext(output_ext)
            compressed_size = len(compressed_bytes)
            output_filename = f"{base_name}.{output_ext}"

            compressed_path = None
            if output_dir is not None:
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / output_filename
                output_path.write_bytes(compressed_bytes)
                compressed_path = str(output_path)

            cdn_url = None
            if upload:
                key = f"/{self.target_path}/{output_filename}"
                content_type = guess_content_type(output_ext)
                cdn_url = self.upload_to_cdn(key, compressed_bytes, content_type)

            return ProcessResult(
                success=True,
                node_id=image_ref.node_id,
                node_name=image_ref.node_name,
                image_ref=image_ref.image_ref,
                original_size=original_size,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio,
                cdn_url=cdn_url,
                downloaded_path=downloaded_path,
                compressed_path=compressed_path,
            )
        except Exception as exc:  # noqa: BLE001
            return ProcessResult(
                success=False,
                node_id=image_ref.node_id,
                node_name=image_ref.node_name,
                image_ref=image_ref.image_ref,
                error=str(exc),
            )


class ApiModeClient(BaseProcessorClient):
    def __init__(
        self,
        api_base: str,
        target_path: str,
        bucket: str,
        image_format: str,
        quality: int,
        upload_endpoint: Optional[str] = None,
    ) -> None:
        super().__init__(target_path=target_path, bucket=bucket, upload_endpoint=upload_endpoint)
        self.api_base = api_base.rstrip("/")
        self.image_format = image_format
        self.quality = quality

        if self.image_format not in SUPPORTED_FORMATS:
            raise ValueError(f"unsupported format: {self.image_format}")
        if not (1 <= self.quality <= 100):
            raise ValueError("quality must be between 1 and 100")

        parsed = urlparse(self.api_base)
        if not parsed.scheme or not parsed.hostname:
            raise ValueError("api-base must be a valid URL")
        self.api_scheme = parsed.scheme
        self.api_host = parsed.hostname
        self.api_port = parsed.port or (443 if parsed.scheme == "https" else 80)
        self._cached_sts: Optional[Dict[str, str]] = None

    def _open_api_conn(self) -> http.client.HTTPConnection:
        if self.api_scheme == "https":
            return http.client.HTTPSConnection(self.api_host, self.api_port, timeout=60)
        return http.client.HTTPConnection(self.api_host, self.api_port, timeout=60)

    def _compress_via_api(self, image_data: bytes, filename: str) -> Dict[str, Any]:
        options = {
            "format": self.image_format,
            "quality": self.quality,
            "resize": {
                "mode": "none",
                "width": None,
                "height": None,
                "fit": "inside",
                "percent": 100,
            },
            "keepMetadata": False,
        }
        boundary = "----CodexBoundary" + uuid.uuid4().hex
        payload_parts: List[bytes] = [
            f"--{boundary}".encode(),
            f'Content-Disposition: form-data; name="images"; filename="{filename}"'.encode(),
            b"Content-Type: application/octet-stream",
            b"",
            image_data,
            f"--{boundary}".encode(),
            b'Content-Disposition: form-data; name="options"',
            b"",
            json.dumps(options, ensure_ascii=False).encode("utf-8"),
            f"--{boundary}--".encode(),
            b"",
        ]
        body = b"\r\n".join(payload_parts)
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        }

        conn = self._open_api_conn()
        try:
            conn.request("POST", "/api/image-compressor/compress", body=body, headers=headers)
            response = conn.getresponse()
            text = response.read().decode("utf-8", errors="replace")
            if response.status >= 400:
                raise RuntimeError(f"compress API failed ({response.status}): {text}")
            payload = json.loads(text)
        finally:
            conn.close()

        if not payload.get("success"):
            err = (payload.get("error") or {}).get("message", "compress failed")
            raise RuntimeError(err)

        data = (payload.get("data") or [{}])[0]
        if not data.get("success"):
            err = (data.get("error") or {}).get("message", "compress failed")
            raise RuntimeError(err)
        return data

    def _download_compressed_via_api(self, image_id: str) -> bytes:
        conn = self._open_api_conn()
        try:
            conn.request("GET", f"/api/image-compressor/download/{image_id}")
            response = conn.getresponse()
            content = response.read()
            if response.status >= 400:
                raise RuntimeError(f"download compressed failed ({response.status})")
            return content
        finally:
            conn.close()

    def _fetch_sts(self) -> Dict[str, str]:
        if self._cached_sts:
            return self._cached_sts

        body = json.dumps({"resource": [f"{self.bucket}/*"]}).encode("utf-8")
        headers = {"Content-Type": "application/json", "Content-Length": str(len(body))}

        conn = self._open_api_conn()
        try:
            conn.request("POST", "/api/bos/sts", body=body, headers=headers)
            response = conn.getresponse()
            text = response.read().decode("utf-8", errors="replace")
            if response.status >= 400:
                raise RuntimeError(f"fetch sts failed ({response.status}): {text}")
            payload = json.loads(text)
        finally:
            conn.close()

        sts = payload.get("data") or {}
        required = ("AccessKeyId", "SecretAccessKey", "SessionToken")
        if not all(sts.get(key) for key in required):
            raise RuntimeError("invalid sts response")

        self._cached_sts = sts
        return sts

    def compress_image(self, image_data: bytes, source_filename: str, source_ext: str) -> Tuple[bytes, str, float]:
        _ = source_ext
        meta = self._compress_via_api(image_data, source_filename)
        image_id = str(meta["id"])
        content = self._download_compressed_via_api(image_id)
        output_ext = normalize_ext(str(meta.get("format") or "jpg"))
        if output_ext == "original":
            output_ext = normalize_ext(source_ext)
        ratio = float(meta.get("compressionRatio", 0.0))
        return content, output_ext, ratio

    def upload_to_cdn(self, key: str, content: bytes, content_type: str) -> str:
        sts = self._fetch_sts()
        ak = sts["AccessKeyId"]
        sk = sts["SecretAccessKey"]
        token = sts["SessionToken"]
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        auth = build_bce_v1_authorization(ak, sk, timestamp, key, self.endpoint_host)

        headers = {
            "Host": self.endpoint_host,
            "Content-Type": content_type,
            "Content-Length": str(len(content)),
            "x-bce-date": timestamp,
            "x-bce-security-token": token,
            "Authorization": auth,
        }

        if self.endpoint_scheme == "https":
            conn: http.client.HTTPConnection = http.client.HTTPSConnection(self.endpoint_host, self.endpoint_port, timeout=60)
        else:
            conn = http.client.HTTPConnection(self.endpoint_host, self.endpoint_port, timeout=60)

        try:
            conn.request("PUT", key, body=content, headers=headers)
            response = conn.getresponse()
            body = response.read()
            if response.status not in (200, 201):
                text = body.decode("utf-8", errors="replace")
                raise RuntimeError(f"cdn upload failed ({response.status}): {text}")
        finally:
            conn.close()

        return f"{self.endpoint_scheme}://{self.endpoint_host}{key}"


class StandaloneModeClient(BaseProcessorClient):
    def __init__(
        self,
        target_path: str,
        bucket: str,
        image_format: str,
        quality: int,
        bos_ak: Optional[str],
        bos_sk: Optional[str],
        bos_session_token: Optional[str],
        upload_endpoint: Optional[str] = None,
    ) -> None:
        super().__init__(target_path=target_path, bucket=bucket, upload_endpoint=upload_endpoint)
        self.image_format = image_format
        self.quality = quality
        self.bos_ak = (bos_ak or "").strip()
        self.bos_sk = (bos_sk or "").strip()
        self.bos_session_token = (bos_session_token or "").strip() or None

        if self.image_format not in SUPPORTED_FORMATS:
            raise ValueError(f"unsupported format: {self.image_format}")
        if not (1 <= self.quality <= 100):
            raise ValueError("quality must be between 1 and 100")

    def _require_pillow(self):
        try:
            from PIL import Image  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("standalone mode needs Pillow. Install with: pip install Pillow") from exc
        return Image

    def _resolve_output_ext(self, source_ext: str) -> str:
        if self.image_format == "original":
            preferred = normalize_ext(source_ext)
            if preferred in {"jpg", "png", "webp", "avif"}:
                return preferred
            return "png"
        return normalize_ext(self.image_format)

    def _encode_image(self, img, output_ext: str) -> bytes:
        Image = self._require_pillow()
        out = io.BytesIO()
        fmt = {
            "jpg": "JPEG",
            "png": "PNG",
            "webp": "WEBP",
            "avif": "AVIF",
        }.get(output_ext)
        if not fmt:
            raise RuntimeError(f"unsupported output format: {output_ext}")

        if fmt == "JPEG":
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            img.save(out, format=fmt, quality=self.quality, optimize=True)
        elif fmt == "PNG":
            img.save(out, format=fmt, optimize=True, compress_level=9)
        elif fmt == "WEBP":
            img.save(out, format=fmt, quality=self.quality, method=6)
        elif fmt == "AVIF":
            # AVIF support depends on local Pillow build.
            img.save(out, format=fmt, quality=self.quality)
        else:
            raise RuntimeError(f"unsupported output format: {output_ext}")

        return out.getvalue()

    def compress_image(self, image_data: bytes, source_filename: str, source_ext: str) -> Tuple[bytes, str, float]:
        _ = source_filename
        Image = self._require_pillow()
        output_ext = self._resolve_output_ext(source_ext)

        try:
            with Image.open(io.BytesIO(image_data)) as img:
                compressed = self._encode_image(img, output_ext)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"local compression failed: {exc}") from exc

        if len(image_data) == 0:
            ratio = 0.0
        else:
            ratio = max(0.0, (1 - (len(compressed) / len(image_data))) * 100)

        return compressed, output_ext, round(ratio, 2)

    def upload_to_cdn(self, key: str, content: bytes, content_type: str) -> str:
        if not self.bos_ak or not self.bos_sk:
            raise RuntimeError("standalone upload needs BOS credentials: --bos-ak and --bos-sk (or env BOS_AK/BOS_SK)")

        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        auth = build_bce_v1_authorization(self.bos_ak, self.bos_sk, timestamp, key, self.endpoint_host)

        headers = {
            "Host": self.endpoint_host,
            "Content-Type": content_type,
            "Content-Length": str(len(content)),
            "x-bce-date": timestamp,
            "Authorization": auth,
        }
        if self.bos_session_token:
            headers["x-bce-security-token"] = self.bos_session_token

        if self.endpoint_scheme == "https":
            conn: http.client.HTTPConnection = http.client.HTTPSConnection(self.endpoint_host, self.endpoint_port, timeout=60)
        else:
            conn = http.client.HTTPConnection(self.endpoint_host, self.endpoint_port, timeout=60)

        try:
            conn.request("PUT", key, body=content, headers=headers)
            response = conn.getresponse()
            body = response.read()
            if response.status not in (200, 201):
                text = body.decode("utf-8", errors="replace")
                raise RuntimeError(f"cdn upload failed ({response.status}): {text}")
        finally:
            conn.close()

        return f"{self.endpoint_scheme}://{self.endpoint_host}{key}"


def collect_figma_image_refs(figma_input: str, figma_token: str) -> Tuple[str, List[FigmaImageRef], int]:
    file_key = parse_file_key(figma_input)
    file_info = fetch_figma_json(f"https://api.figma.com/v1/files/{file_key}", figma_token, timeout=180)
    images_payload = fetch_figma_json(f"https://api.figma.com/v1/files/{file_key}/images", figma_token, timeout=180)
    image_url_map = (images_payload.get("meta") or {}).get("images", {})

    refs: List[FigmaImageRef] = []
    for rec in iter_image_refs(file_info):
        refs.append(
            FigmaImageRef(
                node_id=rec["node_id"],
                node_name=rec["node_name"],
                node_type=rec["node_type"],
                image_ref=rec["image_ref"],
                download_url=image_url_map.get(rec["image_ref"]),
            )
        )

    unique_by_ref: Dict[str, FigmaImageRef] = {}
    unresolved = 0
    for ref in refs:
        if not ref.download_url:
            unresolved += 1
            continue
        if ref.image_ref not in unique_by_ref:
            unique_by_ref[ref.image_ref] = ref

    return file_key, list(unique_by_ref.values()), unresolved


def collect_local_image_refs(local_dir: Optional[str], local_files: Optional[str]) -> Tuple[str, List[FigmaImageRef], int]:
    paths: List[Path] = []
    if local_dir:
        root = Path(local_dir).resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError(f"local-dir not found or not a directory: {local_dir}")
        paths.extend([p for p in sorted(root.iterdir()) if p.is_file() and p.suffix.lower() in LOCAL_IMAGE_EXTS])

    if local_files:
        for item in local_files.split(","):
            raw = item.strip()
            if not raw:
                continue
            p = Path(raw).resolve()
            if not p.exists() or not p.is_file():
                raise ValueError(f"local file not found: {raw}")
            if p.suffix.lower() not in LOCAL_IMAGE_EXTS:
                continue
            paths.append(p)

    unique: Dict[str, Path] = {}
    for p in paths:
        unique[str(p)] = p

    refs: List[FigmaImageRef] = []
    for idx, p in enumerate(unique.values(), start=1):
        refs.append(
            FigmaImageRef(
                node_id=f"local:{idx}",
                node_name=p.stem,
                node_type="LOCAL_FILE",
                image_ref=f"local-{idx}-{p.name}",
                download_url=str(p),
            )
        )
    return "local", refs, 0


def parse_node_ids(raw_node_ids: Optional[str]) -> Optional[set]:
    if not raw_node_ids:
        return None
    parsed = {item.strip() for item in raw_node_ids.split(",") if item.strip()}
    return parsed or None


def resolve_bos_credential(value: Optional[str], env_keys: List[str]) -> Optional[str]:
    if value:
        return value
    for key in env_keys:
        val = os.environ.get(key)
        if val:
            return val
    return None


def build_client(args, quality: int):
    mode = args.mode
    if mode not in SUPPORTED_MODES:
        raise ValueError(f"unsupported mode: {mode}")

    if mode == "api":
        return ApiModeClient(
            api_base=args.api_base,
            target_path=args.target_path,
            bucket=args.bucket,
            image_format=args.format,
            quality=quality,
            upload_endpoint=args.bos_endpoint,
        )

    bos_ak = resolve_bos_credential(args.bos_ak, ["BOS_AK", "BCE_ACCESS_KEY_ID"])
    bos_sk = resolve_bos_credential(args.bos_sk, ["BOS_SK", "BCE_SECRET_ACCESS_KEY"])
    bos_session_token = resolve_bos_credential(
        args.bos_session_token,
        ["BOS_SESSION_TOKEN", "BCE_SESSION_TOKEN"],
    )

    return StandaloneModeClient(
        target_path=args.target_path,
        bucket=args.bucket,
        image_format=args.format,
        quality=quality,
        bos_ak=bos_ak,
        bos_sk=bos_sk,
        bos_session_token=bos_session_token,
        upload_endpoint=args.bos_endpoint,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download Figma images, compress and upload to CDN",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--figma-input", help="Figma file URL or file key")
    parser.add_argument("--figma-token", default=os.environ.get("FIGMA_TOKEN"), help="Figma token")
    parser.add_argument("--local-dir", help="Process local image directory")
    parser.add_argument("--local-files", help="Process local image files, comma-separated absolute/relative paths")
    parser.add_argument("--mode", choices=sorted(SUPPORTED_MODES), default="api", help="api or standalone")
    parser.add_argument("--target-path", default="lego-data/test", help="CDN target path")
    parser.add_argument("--bucket", default="feed-activity", help="BOS bucket name")
    parser.add_argument("--bos-endpoint", help="BOS endpoint URL, default https://{bucket}.cdn.bcebos.com")

    parser.add_argument("--api-base", default="http://localhost:3000", help="API base URL (api mode)")
    parser.add_argument("--bos-ak", help="BOS AccessKeyId (standalone mode)")
    parser.add_argument("--bos-sk", help="BOS SecretAccessKey (standalone mode)")
    parser.add_argument("--bos-session-token", help="BOS session token (optional, standalone mode)")

    parser.add_argument("--format", choices=sorted(SUPPORTED_FORMATS), default="original", help="Output format")
    parser.add_argument("--quality", type=int, default=80, help="Compression quality 1-100")
    parser.add_argument("--preset", choices=["high", "balanced", "small"], help="Quality preset")
    parser.add_argument("--node-ids", help="Only process these node IDs, comma-separated")
    parser.add_argument("--limit", type=int, help="Max number of images to process")
    parser.add_argument("--no-upload", action="store_true", help="Compress only, skip CDN upload")
    parser.add_argument("--download-dir", help="Save downloaded source images")
    parser.add_argument("--output-dir", help="Save compressed images")
    parser.add_argument("--json-out", help="Write result JSON to this file")

    args = parser.parse_args()

    quality = QUALITY_PRESETS[args.preset] if args.preset else args.quality
    if not (1 <= quality <= 100):
        print("ERROR: quality must be between 1 and 100", file=sys.stderr)
        return 2

    try:
        has_local_source = bool(args.local_dir or args.local_files)
        has_figma_source = bool(args.figma_input)

        if has_local_source:
            file_key, image_refs, unresolved_count = collect_local_image_refs(args.local_dir, args.local_files)
        elif has_figma_source:
            if not args.figma_token:
                print("ERROR: missing figma token. Use --figma-token or FIGMA_TOKEN env.", file=sys.stderr)
                return 2
            file_key, image_refs, unresolved_count = collect_figma_image_refs(args.figma_input, args.figma_token)
        else:
            print("ERROR: provide one source: --figma-input or --local-dir/--local-files", file=sys.stderr)
            return 2
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: failed to collect input images: {exc}", file=sys.stderr)
        return 1

    node_id_filter = parse_node_ids(args.node_ids)
    if node_id_filter is not None:
        image_refs = [item for item in image_refs if item.node_id in node_id_filter]

    if args.limit is not None:
        image_refs = image_refs[: max(args.limit, 0)]

    if not image_refs:
        print("No image refs found after filtering.")
        return 0

    print(f"mode={args.mode}")
    print(f"file_key={file_key}")
    print(f"unique_image_refs={len(image_refs)}")
    print(f"missing_download_url={unresolved_count}")
    print(f"upload_enabled={not args.no_upload}")
    print(f"target_path={args.target_path}")

    try:
        client = build_client(args, quality)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: invalid params: {exc}", file=sys.stderr)
        return 2

    download_dir = Path(args.download_dir) if args.download_dir else None
    output_dir = Path(args.output_dir) if args.output_dir else None
    should_upload = not args.no_upload

    results: List[ProcessResult] = []
    for idx, image_ref in enumerate(image_refs, start=1):
        print(
            f"[{idx}/{len(image_refs)}] node={image_ref.node_id} "
            f"name={image_ref.node_name} ref={image_ref.image_ref}"
        )
        result = client.process_one(image_ref, download_dir, output_dir, should_upload)
        results.append(result)
        if result.success:
            print(
                f"  OK: {format_size(result.original_size)} -> "
                f"{format_size(result.compressed_size)} ({result.compression_ratio}%)"
            )
            if result.cdn_url:
                print(f"  CDN: {result.cdn_url}")
        else:
            print(f"  ERROR: {result.error}")

    success_count = sum(1 for item in results if item.success)
    fail_count = len(results) - success_count
    total_original_size = sum(item.original_size for item in results if item.success)
    total_compressed_size = sum(item.compressed_size for item in results if item.success)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"total={len(results)} success={success_count} failed={fail_count}")
    if success_count > 0:
        saved = total_original_size - total_compressed_size
        percent = (saved / total_original_size * 100.0) if total_original_size else 0.0
        print(f"original_size={format_size(total_original_size)}")
        print(f"compressed_size={format_size(total_compressed_size)}")
        print(f"saved={format_size(saved)} ({percent:.2f}%)")

    output_json = args.json_out or f"figma_image_processor_result_{file_key}.json"
    payload = {
        "mode": args.mode,
        "file_key": file_key,
        "success": success_count,
        "failed": fail_count,
        "results": [asdict(item) for item in results],
    }
    Path(output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"json_saved={output_json}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
