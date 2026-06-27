from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import Chroma

LLM_MODEL = "llama3.2"

PROMPT_TEMPLATE = """あなたは研究論文の内容を解説するアシスタントです。
以下の論文の抜粋を参考にして、質問に日本語で答えてください。
抜粋に答えが含まれていない場合は「この論文の抜粋からは判断できません」と答えてください。

【論文の抜粋】
{context}

【質問】
{question}

【回答】"""


def build_chain(vectorstore: Chroma):
    llm = ChatOllama(model=LLM_MODEL, temperature=0)
    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"],
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 8})
    answer_chain = prompt | llm | StrOutputParser()

    def invoke(inputs: dict) -> dict:
        query = inputs["query"]
        docs = retriever.invoke(query)
        context = "\n\n".join(doc.page_content for doc in docs)
        answer = answer_chain.invoke({"context": context, "question": query})
        return {"result": answer, "source_documents": docs}

    return invoke
