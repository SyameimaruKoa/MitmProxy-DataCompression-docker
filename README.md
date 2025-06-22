# Real-time Image Compression Proxy with mitmproxy

## 概要 (Overview)

このプロジェクトは、`mitmproxy`と`Pillow-SIMD`を使用して、通信経路上でリアルタイムに画像を圧縮するプロキシサーバーを Docker で構築します。Web ブラウジング時のデータ通信量を削減することを目的としています。

Tailscale やローカルネットワークなど、プライベートな環境での利用を想定しています。

## 特徴 (Features)

- **Docker Compose 対応**: `docker compose up`だけで簡単に起動できます。
- **Web UI**: `mitmweb`により、ブラウザからリアルタイムで通信フローを監視できます。
- **高速な画像圧縮**: SIMD 命令で高速化された`Pillow-SIMD`を使用し、JPEG,PNG,WebP 形式の画像を圧縮します。
- **簡単な証明書インストール**: ブラウザから`http://mitm.it`にアクセスするだけで CA 証明書を導入できます。

## 必要なもの (Prerequisites)

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/) (Docker Desktop には同梱されています)

## 🚀 セットアップと実行 (Setup and Run)

1. このリポジトリをクローンします。

   ```bash
   git clone git@github.com:SyameimaruKoa/MitmProxy-DataCompression-docker.git
   cd MitmProxy-DataCompression-docker
   ```

2. コンテナをビルドして、バックグラウンドで起動します。

   ```bash
   docker compose up -d
   ```

3. ログを確認するには:

   ```bash
   docker compose logs -f
   ```

4. 停止するには:

   ```bash
   docker compose down
   ```

## 🛠️ 使い方 (Usage)

プロキシを利用するには、まずクライアントデバイス（PC やスマートフォン）でプロキシを設定し、次に専用ページから CA 証明書をインストールします。

### 1. プロキシの設定

クライアントデバイスのネットワーク設定で、HTTP/HTTPS プロキシを以下のように設定します。

- **サーバー (ホスト)**: Docker を動かしているマシンの IP アドレス
  - (例: `192.168.1.10`, Tailscale IP `tailxxxxx.ts.net`)
- **ポート**: `3126`

### 2. CA 証明書のインストール (ブラウザ経由)

このプロキシが HTTPS 通信を復号化するために、`mitmproxy`が生成する CA 証明書をクライアントにインストールする必要があります。

1. 上記**プロキシ設定を有効にした状態**で、デバイスの Web ブラウザを起動します。
2. アドレスバーに`http://mitm.it`と入力し、アクセスします。
3. `mitmproxy`の証明書ダウンロードページが表示されます。お使いのデバイス（Apple,Android,Windows など）に対応するアイコンをクリックして、証明書をダウンロードしてください。
4. ダウンロードした証明書を、各 OS の指示に従ってインストールします。

### 3. Web UI へのアクセス

ブラウザで以下の URL にアクセスすると、通信をリアルタイムで監視できる Web インターフェースが表示されます。（この URL にアクセスする際は、クライアントのプロキシ設定は不要です）

- `http://<Dockerを動かしているマシンのIPアドレス>:8081`

## 構成ファイル (File Structure)

- `docker-compose.yml`: Docker コンテナの構成（ポート、ボリュームなど）を定義します。
- `Dockerfile`: `mitmproxy`と依存ライブラリをインストールし、コンテナイメージをビルドします。
- `flows.py`: 画像を検知して圧縮処理を行う Python スクリプトです。

## 開発経緯 (Development Story)

このプロジェクトは、元々 CentOS 上で構築されていた[こちらの記事](https://qiita.com/tongari0/items/ffa3297630547c3bb712)の画像圧縮プロキシのアイデアが元になっています。

その素晴らしいコンセプトを、より現代的で、誰でも簡単に利用・管理できる Docker コンテナ環境へ移行させるため、Google の生成 AI「Gemini」に命令して作成しました。

Docker 化、最新対応化、そして開発過程で発生した数々のエラー解決に至るまで 100％ Gemini で作成されました。
