from PyPDF2 import PdfReader
from sqlalchemy import null
import streamlit as st
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_community.chat_models import ChatOpenAI
# from langchain_openai import ChatOpenAI
from langchain_community.llms import HuggingFaceEndpoint
from Web_Scrape import scrape_data, search_google
from templates.chat import css, user_template, bot_template
from dotenv import load_dotenv
import os


def get_pdf_text(pdf_docs):
    text = ""

    for i, pdf in enumerate(pdf_docs):
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def get_web_text(query, option):
    web_text = ""
    url_list = search_google(query, stop=int(option))
    for url in url_list:
        if url:
            web_text += scrape_data(url)
    return web_text


def get_text_chunks(raw_text):
    text_splitter = CharacterTextSplitter(
        separator="\n", chunk_size=1200, chunk_overlap=300, length_function=len)

    chunks = text_splitter.split_text(raw_text)
    return chunks


def get_embeddings(chunks, api_Secret):
    embeddings = HuggingFaceInferenceAPIEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2", api_key=api_Secret)
    vectorstore = FAISS.from_texts(texts=chunks, embedding=embeddings)
    print(embeddings)
    return vectorstore


def get_conversation_chain(vectorstore, setup_option):
    #
    # llm = ChatOpenAI()

    if setup_option == "Local setup using LM Studio":
        llm = ChatOpenAI(
            temperature=0.0, base_url="http://localhost:1234/v1", api_key="not-needed")

    elif setup_option == "Hugging Face":
        llm = HuggingFaceEndpoint(
            repo_id="google/flan-t5-xxl", temperature=0.5, max_length=512)

    elif setup_option == "OpenAI":
        pass

    memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm, retriever=vectorstore.as_retriever(), memory=memory)
    return conversation_chain


def handle_user_input(user_query):
    response = st.session_state.conversation({"question": user_query})
    print(response)
    st.session_state.chat_history = response['chat_history']
    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="LLM PDF MINER")
    load_dotenv()

    st.write(css, unsafe_allow_html=True)
    st.write(os.getenv('HUGGINGFACEHUB_API_TOKEN'))

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

        query = ""
        option = None
        pdf_docs = st.file_uploader(
            "Upload your pdfs here", accept_multiple_files=True)
        setup_option = st.radio("Select Setup Option", [
                                "Local setup using LM Studio", "Hugging Face", "OpenAI"])
        api_key = None
        if setup_option == "Local setup using LM Studio":
            api_key = st.text_input(
                "Enter LM Studio localhost address", disabled=True)

        elif setup_option == "Hugging Face":
            api_key = st.text_input("Enter Hugging Face API Key")

        elif setup_option == "OpenAI":
            api_key = st.text_input("Enter OpenAI API Key", disabled=True)
        api_key = str(api_key).strip()
        query_option = st.checkbox("Query the Web to add it to the knowledge")

        if query_option:
            query = st.text_area("Enter the Query for the google search")
            user_input = st.text_input(
                'Select how many links you want to scrape data from (default=10 - max=15): ', value='10')

            # Convert input to integer, default to 10 if input is empty
            try:
                option = int(user_input) if user_input else 10
            except ValueError:
                st.error("Please enter a valid integer.")

        if st.button("Process"):
            try:
                with st.spinner("Processing"):
                    raw_text = ""

                    if pdf_docs:
                        # get pdf text
                        raw_text += get_pdf_text(pdf_docs)

                    if query and option:
                        web_text = get_web_text(query, option)
                        raw_text += web_text

                    # get the text chunks
                    text_chunks = get_text_chunks(raw_text)
                    print(str(text_chunks))
                    # Text embeddings
                    # Vector Store
                    vectorstore = get_embeddings(text_chunks, api_key)
                    # Create Conversation
                    st.session_state.conversation = get_conversation_chain(
                        vectorstore, setup_option)

            except Exception as e:
                st.write(f"An Error has Occurred: {str(e)}")
                st.write("Please upload a document or check your input.")


if __name__ == "__main__":
    main()
