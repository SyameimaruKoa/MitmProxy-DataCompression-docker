#!/bin/sh
# もし途中でコマンドが失敗したら、即座に終了するおまじない
set -e

# --- 聖域の結界（証明書のインストール）---
# Mitmproxyの証明書を信頼させるための儀式じゃ。

echo "MitmproxyのCA証明書をインストールする..."

# /certs (ボリュームからマウントされた場所) から、OSの証明書ストアへコピーする
cp /certs/mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy-ca-cert.crt

echo "CA証明書ストアを更新する..."
# OSに、新しい証明書を認識させる
update-ca-certificates

echo "証明書のインストール、完了じゃ。"

# --- デーモンの召喚 ---
# 事前認証済みのため、ただ静かにデーモンを起動するだけ。
# ボリュームにある「身分証」を読み込んで、自動でネットワークに参加する。

echo "Tailscaleデーモンを起動する (事前認証済みモード)..."
exec tailscaled --tun=userspace-networking
# 司令官が号令をかけるまでの、慈悲の5秒
sleep 5

# Tailscale自身が我々に示した、完璧なる神託の呪文を詠唱！
echo "[TAILSCALE] Bringing tailscale up with auth key..."
tailscale up \
    --auth-key=${TS_AUTHKEY} \
    --hostname=mitm-proxy-node \
    --accept-dns=false \
    --accept-routes \
    --advertise-routes=0.0.0.0/0 \
    --advertise-exit-node=true
echo "[TAILSCALE] Setup complete. Waiting..."

# デーモンが終了するのを待つ
wait $!
