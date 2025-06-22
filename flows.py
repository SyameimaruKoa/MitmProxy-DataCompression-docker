#!/usr/bin/env python3
from PIL import Image, ImageFile
import io, time, os, gzip
import brotli

# ==============================================================================
# --- 設定 (ここを編集してプロキシの動作をカスタマイズ) ---
# ==============================================================================

# --- 共通設定 ---
MIN_SIZE_TO_PROCESS_BYTES = 10240  # これ以下のサイズのファイルは処理しない (10KB)

# --- モダンモード設定 (safe, force_webp) ---
# JPEG/PNGからWebPへ変換する際の品質 (1-100, 数値が低いほど高圧縮・低画質)
MODERN_WEBP_QUALITY = 50
# JPEGを再圧縮する際の品質 (1-100)
MODERN_JPEG_QUALITY = 10
# PNGを再圧縮する際の圧縮レベル (0-9, 数値が高いほど高圧縮)
MODERN_PNG_COMPRESS_LEVEL = 9
# WebPを再圧縮する際の品質 (1-100)
MODERN_WEBP_RECOMPRESS_QUALITY = 50

# --- レガシーモード設定 (legacy) ---
# 縮小する画像の最大幅 (ピクセル)
LEGACY_MAX_WIDTH = 800
# 縮小する画像の最大高さ (ピクセル)
LEGACY_MAX_HEIGHT = 600
# WebPからJPEGに変換する際の品質 (1-100, 高いほど高品質)
LEGACY_JPEG_QUALITY = 80

# ==============================================================================
# --- これ以降のコードは通常、編集不要 ---
# ==============================================================================

ImageFile.LOAD_TRUNCATED_IMAGES = True

def handle_legacy_mode(flow):
    """ 旧デバイス向けの処理 (WebP->JPEG変換, リサイズ) """
    try:
        ct = flow.response.headers.get("content-type", "")
        if ct.startswith("image/webp") and flow.response.content:
            ru = str(flow.request.url)
            print(f"*** LEGACY MODE: webp to jpeg start {ru} ***")
            start = time.time()
            s = io.BytesIO(flow.response.content)
            s2 = io.BytesIO()

            img = Image.open(s)

            if img.width > LEGACY_MAX_WIDTH or img.height > LEGACY_MAX_HEIGHT:
                print(f"    Resizing from {img.width}x{img.height} to fit within {LEGACY_MAX_WIDTH}x{LEGACY_MAX_HEIGHT}")
                img.thumbnail((LEGACY_MAX_WIDTH, LEGACY_MAX_HEIGHT), Image.Resampling.LANCZOS)

            img.convert('RGB').save(s2, "jpeg", quality=LEGACY_JPEG_QUALITY, optimize=True)
            flow.response.content = s2.getvalue()
            flow.response.headers["Content-Type"] = "image/jpeg"
            elapsed_time_ms = (time.time() - start) * 1000
            print(f"    Converted to JPEG in {elapsed_time_ms:.0f}ms")
    except Exception as e:
        print(f"--- Error in legacy mode for {flow.request.url}: {e} ---")

def handle_modern_modes(flow, proxy_mode):
    """ 最新デバイス向けの処理 (データ削減) """
    try:
        if "content-type" in flow.response.headers and flow.response.content:
            ct = str(flow.response.headers["content-type"])

            # --- 画像処理 (SVGを除外) ---
            if ct.startswith("image/") and not ct.startswith("image/svg") and len(flow.response.content) > MIN_SIZE_TO_PROCESS_BYTES:
                if proxy_mode == 'force_webp':
                    supports_webp = True
                else:
                    supports_webp = "image/webp" in flow.request.headers.get("accept", "").lower()

                ru = str(flow.request.url)
                s = io.BytesIO(flow.response.content)
                s2 = io.BytesIO()
                start = time.time()
                is_processed = False
                new_ct = ct
                img = Image.open(s)

                if supports_webp and (ct.startswith("image/jpeg") or ct.startswith("image/png")):
                    print(f"*** {ct.split('/')[1]} to webp start ({proxy_mode} mode) {ru} ***")
                    img.save(s2, "webp", quality=MODERN_WEBP_QUALITY)
                    flow.response.content = s2.getvalue()
                    new_ct = "image/webp"
                    flow.response.headers["Content-Type"] = new_ct
                    is_processed = True
                elif ct.startswith("image/jpeg"):
                    img.save(s2, "jpeg", quality=MODERN_JPEG_QUALITY, optimize=True, progressive=True)
                    flow.response.content = s2.getvalue()
                    is_processed = True
                elif ct.startswith("image/png"):
                    img.convert(mode='P', palette=Image.ADAPTIVE).save(s2, "png", compress_level=MODERN_PNG_COMPRESS_LEVEL)
                    flow.response.content = s2.getvalue()
                    is_processed = True
                elif ct.startswith("image/webp"):
                    img.save(s2, "webp", quality=MODERN_WEBP_RECOMPRESS_QUALITY)
                    flow.response.content = s2.getvalue()
                    is_processed = True

                if is_processed:
                    cl = len(s.getvalue())
                    cl2 = len(flow.response.content)
                    if cl > 0:
                        ratio_after = int(cl2 / cl * 100)
                        saved_ratio = 100 - ratio_after
                        elapsed_time_ms = (time.time() - start) * 1000
                        original_kb = cl / 1024
                        compressed_kb = cl2 / 1024
                        print(f"*** {ct} -> {new_ct} | Size: {original_kb:.1f}KB -> {compressed_kb:.1f}KB ({ratio_after}%) | Saved: {saved_ratio}% | Time: {elapsed_time_ms:.0f}ms | URL: {ru} ***")
                return # 画像処理が終わったら、以降の処理はしない

            # --- テキスト圧縮処理 (SVGも対象に含める) ---
            TEXT_TYPES = ("text/", "application/javascript", "application/json", "application/xml", "image/svg+xml")
            if "content-encoding" not in flow.response.headers and any(ct.startswith(t) for t in TEXT_TYPES):
                ru = str(flow.request.url)
                original_size = len(flow.response.content)

                if original_size < 1024: # 1KB未満の小さなテキストは圧縮しない
                    return

                compressed_content = gzip.compress(flow.response.content)
                compressed_size = len(compressed_content)
                if compressed_size < original_size:
                    flow.response.content = compressed_content
                    flow.response.headers["Content-Encoding"] = "gzip"

                    # --- ここからがログ出力の変更箇所 ---
                    ratio_after = int(compressed_size / original_size * 100)
                    saved_ratio = 100 - ratio_after
                    original_kb = original_size / 1024
                    compressed_kb = compressed_size / 1024

                    print(
                        f"*** Gzip Compress {ct} | "
                        f"Size: {original_kb:.1f}KB -> {compressed_kb:.1f}KB ({ratio_after}%) | "
                        f"Saved: {saved_ratio}% | "
                        f"URL: {ru} ***"
                    )

    except Exception as e:
        print(f"--- Error in modern mode for {flow.request.url}: {e} ---")

# --- メインの処理 ---
def response(flow):
    proxy_mode = os.environ.get('PROXY_MODE', 'safe').lower()
    if proxy_mode not in ['safe', 'force_webp', 'legacy']:
        print(f"--- Invalid PROXY_MODE: {proxy_mode} ---")
        return
    if proxy_mode == 'legacy':
        handle_legacy_mode(flow)
    else:
        handle_modern_modes(flow, proxy_mode)