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

st.set_page_config(page_title="研究論文Q&A", page_icon="📄", layout="wide")
st.title("📄 研究論文 Q&A")
st.caption("PDFをアップロードして、論文の内容を日本語で質問できます（完全ローカル・無料）")

# --- サイドバー：PDF管理 ---
with st.sidebar:
    st.header("論文をアップロード")
    uploaded_files = st.file_uploader(
        "PDFファイルを選択",
        type="pdf",
        accept_multiple_files=True,
    )

    if uploaded_files:
        if st.button("📥 論文を読み込む", use_container_width=True):
            with st.spinner("PDFを解析してベクトルDBに保存中..."):
                clear_vectorstore()
                all_chunks = []
                for f in uploaded_files:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(f.read())
                        tmp_path = tmp.name
                    docs = load_pdf(tmp_path)
                    chunks = split_documents(docs)
                    for chunk in chunks:
                        chunk.metadata["filename"] = f.name
                    all_chunks.extend(chunks)
                    os.unlink(tmp_path)

                build_vectorstore(all_chunks)
                st.session_state["db_ready"] = True
                st.session_state["chat_history"] = []
            st.success(f"{len(uploaded_files)}件のPDFを読み込みました（{len(all_chunks)}チャンク）")

    if st.button("🗑️ DBをリセット", use_container_width=True):
        clear_vectorstore()
        st.session_state["db_ready"] = False
        st.session_state["chat_history"] = []
        st.info("リセットしました")

    st.divider()
    st.markdown("**使い方**")
    st.markdown("1. PDFをアップロード\n2. 「論文を読み込む」をクリック\n3. 右の入力欄で質問")

# --- メイン：チャット ---
if "db_ready" not in st.session_state:
    st.session_state["db_ready"] = collection_exists()
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

if not st.session_state["db_ready"]:
    st.info("左のサイドバーからPDFをアップロードしてください。")
else:
    # チャット履歴の表示
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "sources" in msg:
                with st.expander("参照箇所"):
                    for src in msg["sources"]:
                        fname = src.metadata.get("filename", src.metadata.get("source", "不明"))
                        page = src.metadata.get("page", "?")
                        st.markdown(f"**{fname}** — p.{page}")
                        st.text(src.page_content[:300] + "...")

    # 質問入力
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
                with st.expander("参照箇所"):
                    for src in sources:
                        fname = src.metadata.get("filename", src.metadata.get("source", "不明"))
                        page = src.metadata.get("page", "?")
                        st.markdown(f"**{fname}** — p.{page}")
                        st.text(src.page_content[:300] + "...")

        st.session_state["chat_history"].append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
        })
