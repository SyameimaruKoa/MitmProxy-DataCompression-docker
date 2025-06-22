#!/usr/bin/env python3
from PIL import Image
import io, time, gzip
import brotli

def response(flow):
  # 変数をあらかじめ初期化して、UnboundLocalErrorを防ぐ
  cl = 0
  try:
    # content-typeヘッダとcontent本体の両方がある場合のみ処理する
    if "content-type" in flow.response.headers and flow.response.content:
      ru = str(flow.request.url)
      ct = str(flow.response.headers["content-type"])
      cl = len(flow.response.content)

      # サイズが10KBより大きい画像のみを対象とする
      if cl > 10000:
        s = io.BytesIO(flow.response.content)
        s2 = io.BytesIO()
        start = time.time()
        
        is_processed = False
        # jpeg を quality 10/100 に変換する
        if ct.startswith("image/jpeg"):
          print(f"*** jpeg start {ru} ***")
          img = Image.open(s)
          img.save(s2, "jpeg", quality=10, optimize=True, progressive=True)
          flow.response.content = s2.getvalue()
          is_processed = True

        # png を compress_level=9, 8bitカラーに変換する
        elif ct.startswith("image/png"):
          print(f"*** png start {ru} ***")
          # Pillowのバージョンに依存しにくい古い書き方に戻す
          img = Image.open(s).convert(mode='P', palette=Image.ADAPTIVE)
          img.save(s2, "png", compress_level=9)
          flow.response.content = s2.getvalue()
          is_processed = True

        # webp を quality 10/100 に変換する
        elif ct.startswith("image/webp"):
          print(f"*** webp start {ru} ***")
          img = Image.open(s)
          img.save(s2, "webp", quality=10)
          flow.response.content = s2.getvalue()
          is_processed = True
        
        # 画像圧縮が実行された場合のみ、ログを出力する
        if is_processed:
          cl2  = len(flow.response.content)
          if cl > 0:
            i = int(cl2 / cl * 100)
            elapsed_time = time.time() - start
            print(f"*** compressed {i} percent, size = {cl2}/{cl} bytes, {ru} is processed, {elapsed_time:.4f} sec ***")

  except Exception as e:
    print(f"--- Error processing {flow.request.url}: {e} ---")