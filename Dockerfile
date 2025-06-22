# ベースイメージとして最新のAlmaLinux 9を指定
FROM almalinux:9

# 作業ディレクトリを作成・指定
WORKDIR /app

# 必要なパッケージのインストール
RUN dnf -y update && \
    dnf -y install dnf-plugins-core && \
    dnf config-manager --set-enabled crb && \
    dnf -y groupinstall "Development Tools" && \
    dnf -y install zlib-devel libjpeg-turbo-devel python3-devel python3-pip libwebp-devel && \
    dnf clean all

# pipをアップグレードし、共通のパッケージをインストール
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install mitmproxy brotli

# CPUがAVX2に対応しているか確認し、Pillow-SIMDのインストール方法を分岐
RUN if grep -q 'avx2' /proc/cpuinfo; then \
    echo "AVX2 supported. Compiling Pillow-SIMD with AVX2 optimizations."; \
    CC="cc -mavx2" python3 -m pip install -U --force-reinstall pillow-simd --global-option="build_ext" --global-option="--enable-webp"; \
    else \
    echo "AVX2 not supported. Compiling Pillow-SIMD without AVX2 optimizations."; \
    python3 -m pip install -U --force-reinstall pillow-simd --global-option="build_ext" --global-option="--enable-webp"; \
    fi

# flows.py スクリプトをコンテナにコピー
COPY flows.py .

# mitmproxyが使用するポートを公開 (プロキシ用とWeb UI用)
EXPOSE 3126 8081

# コンテナ起動時にmitmwebを実行するようデフォルトコマンドを変更
CMD ["mitmweb", \
    "--web-host", "0.0.0.0", \
    "--listen-port", "3126", \
    "--ssl-insecure", \
    "-s", "flows.py", \
    "--set", "stream_large_bodies=10m", \
    "--ignore-hosts", "(mzstatic|apple|icloud|mobilesuica|crashlytic|google-analytics|merpay|paypay|rakuten-bank|fate|colopl|rakuten-sec|line|kyash|plexure)", \
    "--set", "block_global=true", \
    "--set", "flow_detail=1", \
    "--set", "http2=false", \
    "--showhost"]