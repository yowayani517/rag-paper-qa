import tempfile
import os
import streamlit as st

from rag.loader import load_pdf, split_documents
from rag.vectorstore import (
    build_vectorstore,
    load_vectorstore,
    collection_exists,
    clear_vectorstore,
)
from rag.chain import build_chain

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="研究論文 Q&A",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (dark GitHub-inspired theme) ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ── App background ── */
.stApp {
    background-color: #0d1117;
}

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 960px !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #161b22 !important;
    border-right: 1px solid #21262d !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem !important;
}

/* ── Page title ── */
h1 {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
    background: linear-gradient(135deg, #58a6ff 0%, #bc8cff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.15rem !important;
}

h2, h3 {
    color: #e6edf3 !important;
    font-weight: 600 !important;
}

p, .stMarkdown p {
    color: #c9d1d9;
}

/* ── Caption / subtitle ── */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #8b949e !important;
    font-size: 0.85rem !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #1f6feb 0%, #388bfd 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.01em !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3) !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #388bfd 0%, #58a6ff 100%) !important;
    box-shadow: 0 4px 16px rgba(56,139,253,0.4) !important;
    transform: translateY(-1px) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3) !important;
}

/* Last button in sidebar = reset (secondary style) */
section[data-testid="stSidebar"] .stButton:last-of-type > button {
    background: #21262d !important;
    color: #8b949e !important;
    border: 1px solid #30363d !important;
    box-shadow: none !important;
}

section[data-testid="stSidebar"] .stButton:last-of-type > button:hover {
    background: #292e36 !important;
    color: #e6edf3 !important;
    box-shadow: none !important;
    transform: none !important;
}

/* ── File uploader ── */
[data-testid="stFileUploaderDropzone"] {
    background-color: #0d1117 !important;
    border: 2px dashed #30363d !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
}

[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #58a6ff !important;
    background-color: rgba(88,166,255,0.04) !important;
}

[data-testid="stFileUploaderDropzone"] > div {
    color: #8b949e !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background-color: #161b22 !important;
    border: 1px solid #21262d !important;
    border-radius: 12px !important;
    margin-bottom: 0.75rem !important;
    padding: 1rem 1.25rem !important;
    transition: border-color 0.15s ease !important;
}

[data-testid="stChatMessage"]:hover {
    border-color: #30363d !important;
}

/* User message: slightly different bg */
[data-testid="stChatMessage"][aria-label*="user"],
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background-color: #1c2128 !important;
    border-color: #30363d !important;
}

/* ── Chat input ── */
[data-testid="stChatInputContainer"] {
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 12px !important;
    padding: 0 !important;
}

[data-testid="stChatInputContainer"]:focus-within {
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 3px rgba(88,166,255,0.12) !important;
}

[data-testid="stChatInput"] textarea {
    color: #e6edf3 !important;
    background-color: transparent !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #484f58 !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background-color: #0d1117 !important;
    border: 1px solid #21262d !important;
    border-radius: 8px !important;
    margin-top: 0.5rem !important;
}

[data-testid="stExpander"] summary {
    color: #8b949e !important;
    font-size: 0.825rem !important;
}

/* ── Alert boxes ── */
div[data-testid="stAlert"][data-baseweb="notification"] {
    border-radius: 8px !important;
}

.stSuccess {
    background-color: rgba(63,185,80,0.1) !important;
    border-left: 3px solid #3fb950 !important;
    border-radius: 0 8px 8px 0 !important;
    color: #3fb950 !important;
}

.stInfo {
    background-color: rgba(88,166,255,0.08) !important;
    border-left: 3px solid #58a6ff !important;
    border-radius: 0 8px 8px 0 !important;
}

.stWarning {
    background-color: rgba(210,153,34,0.1) !important;
    border-left: 3px solid #d2991f !important;
    border-radius: 0 8px 8px 0 !important;
}

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div {
    background-color: #21262d !important;
    border-radius: 4px !important;
}

[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #1f6feb, #58a6ff) !important;
    border-radius: 4px !important;
}

/* ── Divider ── */
[data-testid="stDivider"] hr,
hr {
    border-color: #21262d !important;
    margin: 0.75rem 0 !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] div {
    border-top-color: #58a6ff !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #484f58; }

/* ── Sidebar markdown ── */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] li,
section[data-testid="stSidebar"] .stMarkdown {
    color: #8b949e !important;
    font-size: 0.82rem !important;
}

section[data-testid="stSidebar"] strong {
    color: #e6edf3 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────
def _status_badge(ready: bool) -> str:
    if ready:
        return (
            '<div style="display:inline-flex;align-items:center;gap:6px;'
            'padding:5px 12px;background:rgba(63,185,80,0.1);'
            'border:1px solid rgba(63,185,80,0.25);border-radius:20px;'
            'margin:8px 0 12px;">'
            '<span style="width:7px;height:7px;border-radius:50%;'
            'background:#3fb950;display:inline-block;'
            'box-shadow:0 0 6px #3fb950;"></span>'
            '<span style="color:#3fb950;font-size:0.75rem;font-weight:500;">'
            'DB 読み込み済み</span></div>'
        )
    else:
        return (
            '<div style="display:inline-flex;align-items:center;gap:6px;'
            'padding:5px 12px;background:rgba(139,148,158,0.08);'
            'border:1px solid #30363d;border-radius:20px;margin:8px 0 12px;">'
            '<span style="width:7px;height:7px;border-radius:50%;'
            'background:#484f58;display:inline-block;"></span>'
            '<span style="color:#6e7681;font-size:0.75rem;font-weight:500;">'
            'DB 未ロード</span></div>'
        )


def _source_card(fname: str, page: str | int, content: str) -> str:
    return (
        f'<div style="padding:10px 14px;background:#0d1117;border-radius:8px;'
        f'border:1px solid #21262d;border-left:3px solid #30363d;margin-bottom:8px;">'
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
        f'<span style="color:#58a6ff;font-size:0.8rem;font-weight:500;">{fname}</span>'
        f'<span style="color:#484f58;font-size:0.75rem;">p.{page}</span>'
        f'</div>'
        f'<p style="color:#8b949e;font-size:0.8rem;margin:0;line-height:1.6;">'
        f'{content[:300]}…</p></div>'
    )


# ── Header ─────────────────────────────────────────────────────────────────────
st.title("📄 研究論文 Q&A")
st.caption("PDFをアップロードして、論文の内容を日本語で質問できます — 完全ローカル・APIキー不要・無料")

# ── Session state ──────────────────────────────────────────────────────────────
if "db_ready" not in st.session_state:
    st.session_state["db_ready"] = collection_exists()
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("**論文をアップロード**")

    uploaded_files = st.file_uploader(
        "PDFファイルを選択",
        type="pdf",
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        for f in uploaded_files:
            st.markdown(
                f'<p style="color:#e6edf3;font-size:0.8rem;margin:2px 0;">📄 {f.name}</p>',
                unsafe_allow_html=True,
            )
        st.markdown("")

        if st.button("📥 論文を読み込む", use_container_width=True):
            bar = st.progress(0, text="初期化中...")
            with st.spinner("解析・ベクトル化中..."):
                clear_vectorstore()
                all_chunks = []
                for i, f in enumerate(uploaded_files):
                    pct = int((i / len(uploaded_files)) * 80)
                    bar.progress(pct, text=f"{f.name} を処理中...")
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(f.read())
                        tmp_path = tmp.name
                    docs = load_pdf(tmp_path)
                    chunks = split_documents(docs)
                    for chunk in chunks:
                        chunk.metadata["filename"] = f.name
                    all_chunks.extend(chunks)
                    os.unlink(tmp_path)

                bar.progress(90, text="ChromaDBに保存中...")
                build_vectorstore(all_chunks)
                bar.progress(100, text="完了！")
                st.session_state["db_ready"] = True
                st.session_state["chat_history"] = []
            bar.empty()
            st.success(
                f"✓ {len(uploaded_files)}件のPDF（{len(all_chunks)}チャンク）を読み込みました"
            )
    else:
        st.markdown(
            '<p style="color:#6e7681;font-size:0.78rem;margin-top:4px;">'
            'PDFをドラッグ＆ドロップ<br>またはクリックして選択</p>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown(_status_badge(st.session_state["db_ready"]), unsafe_allow_html=True)

    if st.button("🗑️ DBをリセット", use_container_width=True):
        clear_vectorstore()
        st.session_state["db_ready"] = False
        st.session_state["chat_history"] = []
        st.rerun()

    st.divider()
    st.markdown(
        '<p style="color:#6e7681;font-size:0.78rem;font-weight:600;'
        'letter-spacing:0.04em;text-transform:uppercase;margin-bottom:6px;">使い方</p>'
        '<ol style="color:#6e7681;font-size:0.78rem;padding-left:1.1rem;'
        'line-height:2;margin:0;">'
        "<li>PDFをアップロード</li>"
        "<li>「論文を読み込む」をクリック</li>"
        "<li>下の入力欄で質問</li>"
        "</ol>",
        unsafe_allow_html=True,
    )

# ── Main: Chat ─────────────────────────────────────────────────────────────────
if not st.session_state["db_ready"]:
    st.markdown(
        '<div style="margin-top:5rem;text-align:center;">'
        '<div style="font-size:3.5rem;margin-bottom:1.25rem;'
        'filter:drop-shadow(0 0 20px rgba(88,166,255,0.2));">📚</div>'
        '<p style="color:#6e7681;font-size:1rem;margin-bottom:0.5rem;">'
        "左のサイドバーからPDFをアップロードしてください</p>"
        '<p style="color:#484f58;font-size:0.8rem;">'
        "Ollama (Llama 3.2) &nbsp;·&nbsp; ChromaDB &nbsp;·&nbsp; LangChain</p>"
        "</div>",
        unsafe_allow_html=True,
    )
else:
    # Chat history
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                with st.expander(f"📎 参照箇所（{len(msg['sources'])}件）"):
                    for src in msg["sources"]:
                        fname = src.metadata.get("filename", src.metadata.get("source", "不明"))
                        page = src.metadata.get("page", "?")
                        st.markdown(_source_card(fname, page, src.page_content), unsafe_allow_html=True)

    # Input
    question = st.chat_input("論文について質問してください（例：この研究の目的は何ですか？）")
    if question:
        st.session_state["chat_history"].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("回答を生成中..."):
                db = load_vectorstore()
                chain = build_chain(db)
                result = chain({"query": question})
                answer = result["result"]
                sources = result.get("source_documents", [])
            st.markdown(answer)
            if sources:
                with st.expander(f"📎 参照箇所（{len(sources)}件）"):
                    for src in sources:
                        fname = src.metadata.get("filename", src.metadata.get("source", "不明"))
                        page = src.metadata.get("page", "?")
                        st.markdown(_source_card(fname, page, src.page_content), unsafe_allow_html=True)

        st.session_state["chat_history"].append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
        })
