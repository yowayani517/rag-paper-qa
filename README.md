# 研究論文 Q&A（ローカルRAG）

研究論文のPDFをアップロードし、日本語で質問できるチャットアプリです。
LLMをローカルで動作させるため、**APIキー不要・完全無料**で利用できます。

## デモ

> ※ ローカル動作のため、デモURLはありません。以下の手順でご自身の環境で動作確認できます。

## 技術スタック

| 役割 | 技術 |
|---|---|
| LLM（推論） | [Ollama](https://ollama.com/) + Llama 3.2 |
| Embedding | Ollama + nomic-embed-text |
| ベクトルDB | ChromaDB |
| RAGフレームワーク | LangChain |
| UI | Streamlit |
| PDF解析 | PyMuPDF |

## アーキテクチャ

```
PDF アップロード
     ↓
PyMuPDF でテキスト抽出
     ↓
RecursiveCharacterTextSplitter でチャンク分割（800文字・オーバーラップ100文字）
     ↓
nomic-embed-text でベクトル化 → ChromaDB に保存
     ↓
質問入力 → 類似チャンクを上位4件検索
     ↓
Llama 3.2 で回答生成（参照箇所付き）
```

## セットアップ

### 1. Ollama のインストール

```bash
# https://ollama.com/ からダウンロード、またはコマンドで
winget install Ollama.Ollama   # Windows
```

### 2. モデルのダウンロード

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

### 3. 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

### 4. 起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が開きます。

## 使い方

1. サイドバーから研究論文のPDFをアップロード
2. 「論文を読み込む」ボタンをクリック（初回はEmbedding処理に数十秒かかります）
3. チャット欄に質問を入力（日本語・英語どちらでも可）
4. 回答と参照箇所が表示されます

## 技術的な工夫

- **チャンクサイズの調整**：日本語論文に合わせ、句読点（`。`）を分割セパレータに追加
- **オーバーラップ設定**：チャンク間で100文字のオーバーラップを設けることで、文脈の断絶を防止
- **プロンプト設計**：「抜粋に答えがない場合は判断できないと答える」よう明示し、ハルシネーションを抑制
- **完全ローカル動作**：Ollamaを使用することでAPIコスト・プライバシーの懸念をゼロにした

## 今後の改善点

- [ ] 複数PDFをまたいだ横断検索の精度向上
- [ ] 英語論文→日本語回答の翻訳精度改善
- [ ] HyDE（仮説文書埋め込み）による検索精度向上
- [ ] ストリーミング出力対応
