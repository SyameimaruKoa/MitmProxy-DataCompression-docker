# Real-time Image and Text Optimization Proxy with mitmproxy

## 概要 (Overview)

このプロジェクトは、`mitmproxy` と `Pillow-SIMD` を使用して、通信経路上でリアルタイムに画像を最適化するプロキシサーバーを Docker で構築します。

データ通信量を削減する「モダンモード」と、古いデバイスでの表示を補助する「レガシーモード」を備えており、目的に応じて動作を切り替えられます。

Tailscale やローカルネットワークなど、プライベートな環境での利用を想定しています。

## 特徴 (Features)

- **Docker Compose 対応**: `docker compose up` だけで簡単に起動・更新できます。
- **高度なカスタマイズ性**: `flows.py`の先頭で、画質やリサイズ上限などのパラメータを簡単に調整できます。
- **動作モード切替**: 用途に応じて 3 つのモード（`safe`, `force_webp`, `legacy`）を選択可能です。
- **確実なテキスト圧縮**: モダンモードでは、サーバーが圧縮し忘れたテキストコンテンツ（HTML, CSS, JS 等）もプロキシが確実に gzip 圧縮します。
- **Web UI**: `mitmweb` により、ブラウザからリアルタイムで通信フローを監視できます。
- **WebP 自動変換**: モダンモードでは、クライアント**明確**が対応している場合に JPEG/PNG を WebP 形式に自動変換し、データを削減します。<br>※大体のブラウザではすべてのファイルに対応と指示を出し、webp を明確に指定しないので変換されないことが多いです
- **旧デバイス互換性**: レガシーモードでは、WebP 画像を JPEG に変換し、巨大な画像をリサイズすることで、古いブラウザでの閲覧を補助します。
- **高速な画像処理**: SIMD 命令で高速化された `Pillow-SIMD` を使用します。
- **幅広い CPU 互換性**: ビルド環境の CPU を自動判別し、AVX2 対応 CPU では高速に、非対応 CPU でも互換モードで動作します。
- **簡単な証明書インストール**: ブラウザから `http://mitm.it` にアクセスするだけで CA 証明書を導入できます。

## 必要なもの (Prerequisites)

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/) (Docker Desktop には同梱されています)

## 🚀 セットアップと実行 (Setup and Run)

1. このリポジトリをクローンします。

   ```bash
   git clone https://github.com/SyameimaruKoa/mitmproxy-DataCompression-docker.git
   cd mitmproxy-DataCompression-docker
   ```

2. コンテナをバックグラウンドで起動します。

   ```bash
   docker compose up -d
   ```

   **Note:** `docker-compose.yml` に `build` が指定されているため、初回実行時や、`Dockerfile`・`flows.py` などのソースファイルに変更があった場合は、このコマンドが自動でイメージの再ビルドを行います。常にビルドを強制したい場合のみ、`--build` オプションを追加してください。

3. 停止時は

   ```bash
   docker compose down
   ```

### 以下は確認用です

ログを確認するには

```bash
docker compose logs -f
```

## ⚙️ 動作モードとカスタマイズ

### 動作モードの切り替え

`docker-compose.yml` ファイル内の環境変数 `PROXY_MODE` の値を変更することで、プロキシの動作モードを切り替えられます。

```yaml
# docker-compose.yml
services:
  mitmproxy:
    --中略--
    environment:
      # 'safe', 'force_webp', 'legacy' から選択
      - PROXY_MODE=safe
```

- **`safe` モード (デフォルト・推奨)** : **バランス重視版** 。クライアントのブラウザが送信する `Accept`ヘッダを尊重し、互換性とデータ削減を両立します。
- **`force_webp` モード** : **データ削減特化版** 。JPEG/PNG を常に WebP へ強制変換し、データ削減を最大化します（WebP 非対応ブラウザでは画像が映りません）。
- **`legacy` モード** : **旧デバイス互換モード** 。WebP 画像を JPEG に変換し、巨大な画像を縮小することで、古いブラウザでの表示を補助します。

モードを変更した後は、`docker compose up -d` を実行すれば設定が反映されます。

### 詳細なカスタマイズ

`flows.py`ファイルの先頭にある「設定」セクションで、各モードの画質やリサイズの上限値などを細かく調整できます。

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
- `flows.py`: 画像を検知して最適化処理を行う Python スクリプトです。

## 開発経緯 (Development Story)

このプロジェクトは、元々 CentOS 上で構築されていた[こちらの記事](https://qiita.com/tongari0/items/ffa3297630547c3bb712)の画像圧縮プロキシのアイデアが元になっています。

その素晴らしいコンセプトを、より現代的で、誰でも簡単に利用・管理できる Docker コンテナ環境へ移行させるため、Google の生成 AI「Gemini」に命令して作成しました。

Docker 化、最新対応化、そして開発過程で発生した数々のエラー解決に至るまで 100％ Gemini で作成されました。
