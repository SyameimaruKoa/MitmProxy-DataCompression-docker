# ベースイメージの指定
FROM ubuntu:latest

# 環境変数の設定
ENV DEBIAN_FRONTEND=noninteractive

# パッケージのインストール
RUN apt-get update && \
    apt-get install -y \
        python3 \
        python3-pip \
        python3-dev \
        build-essential \
        libjpeg-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Pythonライブラリのインストール
RUN pip3 install --break-system-packages mitmproxy brotli pillow-simd

# 作業ディレクトリの作成と設定
WORKDIR /app

# コンテナ起動時に自動実行するコマンド
# --web-host 0.0.0.0 を付けることで、コンテナの外からWeb UIにアクセスできるようになる
CMD ["mitmweb", "--web-host", "0.0.0.0"]
