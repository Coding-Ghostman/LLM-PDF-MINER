from PyPDF2 import PdfReader
import dotenv
import streamlit as st
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from langchain.embeddings.huggingface import HuggingFaceInstructEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_community.chat_models import ChatOpenAI
# from langchain_openai import ChatOpenAI
from langchain_community.llms import HuggingFaceEndpoint
from templates.chat import css, user_template, bot_template
from dotenv import load_dotenv

def get_pdf_text(pdf_docs):
    text = ""

    for i, pdf in enumerate(pdf_docs):
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def get_text_chunks(raw_text):
    text_splitter = CharacterTextSplitter(
        separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len)

    chunks = text_splitter.split_text(raw_text)
    return chunks


def get_embeddings(chunks):
    embeddings = HuggingFaceInstructEmbeddings(
        query_instruction="Ingest the provided PDF documents and use their content as context for answering user queries. Extract relevant information from the PDFs to provide accurate responses. Prioritize information in headings, subheadings, and bullet points. If the user asks about specific sections or details, ensure the model references the corresponding parts of the uploaded PDFs. Consider context across multiple pages and maintain coherence in responses. Additionally, emphasize accurate and concise answers, and avoid generating information not present in the provided PDFs.", model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_texts(texts=chunks, embedding=embeddings)
    return vectorstore


def get_conversation_chain(vectorstore, setup_option, api_key=None):
    #
    # llm = ChatOpenAI()

    if setup_option == "Local setup using LM Studio":
        llm = ChatOpenAI(
            temperature=0.0, base_url="http://localhost:1234/v1", api_key="not-needed")

    elif setup_option == "Hugging Face":
        llm = HuggingFaceEndpoint(
            repo_id="google/flan-t5-xxl", temperature=0.5, api_key=api_key)

    elif setup_option == "OpenAI":
        pass

    memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm, retriever=vectorstore.as_retriever(), memory=memory)
    return conversation_chain


def handle_user_input(user_query):
    response = st.session_state.conversation({"question": user_query})
    st.session_state.chat_history = response['chat_history']
    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)


def main():
    load_dotenv()
    st.set_page_config(page_title="LLM PDF MINER")
    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("Chat with pdfs :books:")
    user_query = st.text_input("Ask a question...")

    try:
        if user_query:
            handle_user_input(user_query)
            user_query = ""
            st.text_input("Ask a question...")
    except:
        st.write("""An Error has Occurred: Please Upload A document first then chat.
                 Ignore If pdf is already uploaded""")

    with st.sidebar:
        st.subheader("Your Documents")
        pdf_docs = st.file_uploader(
            "Upload your pdfs here", accept_multiple_files=True)
        setup_option = st.radio("Select Setup Option", [
                                "Local setup using LM Studio", "Hugging Face", "OpenAI"])

        api_key = None
        if setup_option == "Local setup using LM Studio":
            api_key = st.text_input("Enter LM Studio localhost address")

        elif setup_option == "Hugging Face":
            api_key = st.text_input("Enter Hugging Face API Key")

        elif setup_option == "OpenAI":
            api_key = st.text_input("Enter OpenAI API Key", disabled=True)

        if st.button("Process"):
            with st.spinner("Processing"):
                # get pdf text
                raw_text = get_pdf_text(pdf_docs)
                # st.write(raw_text)

                # get the text chunks
                text_chunks = get_text_chunks(raw_text)

                # Text embeddings
                # Vector Store
                vectorstore = get_embeddings(text_chunks)

                # Create Conversation
                st.session_state.conversation = get_conversation_chain(
                    vectorstore, setup_option, api_key)


if __name__ == "__main__":
    main()
