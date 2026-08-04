import os

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.vectorstores import VectorStore
from langchain_anthropic import ChatAnthropic
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import SecretStr
from langchain_huggingface import HuggingFaceEmbeddings

from commons.constants import ANTHROPIC_API_KEY, OPENAI_API_KEY

#TODO:
# Create system prompt with:
# - role: explains the role for LLM and what it should do
# - Structure of User message, consists of 2 blocks:
#   - `RAG CONTEXT`: information retrieved on the Retrieval step based on user request
#   - `USER QUESTION`: The user's actual question
# - Instructions:
#   - Model must use only information from conversation
#   - Strictly forbid to answer questions that are not in the conversation or not present in `RAG CONTEXT`
_SYSTEM_PROMPT = """
You are a helpful assistant that answers questions based on the provided context.
The user will provide you with a context and a question. You must answer the question using only the information from the context. If the answer is not present in the context, you must respond with
"I don't know" or "The answer is not in the context." Do not attempt to provide information that is not included in the context.
The user message will be structured as follows:
##RAG CONTEXT:
{context}
##USER QUESTION:
{query}
"""

_USER_PROMPT = """##RAG CONTEXT:
{context}


##USER QUESTION:
{query}"""


class MicrowaveRAG:

    def __init__(self, embeddings: HuggingFaceEmbeddings, llm_client: ChatAnthropic):
        self.llm_client = llm_client
        self.embeddings = embeddings
        self.vectorstore = self._setup_vectorstore()

    def _setup_vectorstore(self) -> VectorStore:
        """
        Load existing FAISS index from disk or create a new one.
        Returns:
              VectorStore: Initialized FAISS vectorstore.
        """
        #TODO:
        # - Print a startup message
        print("Setting up FAISS vectorstore...")
        # - Check if 'microwave_faiss_index' folder already exists
        if os.path.exists("microwave_faiss_index"):
            # - If yes, load the index from disk using FAISS.load_local()
            vectorstore = FAISS.load_local("microwave_faiss_index", self.embeddings, allow_dangerous_deserialization=True)
            print("Loaded existing FAISS index from disk.")
        else:
            # - If no, call _create_new_index() to build and save a fresh index
            vectorstore = self._create_new_index()
            print("Created and saved new FAISS index.")
        # - Return the vectorstore
        return vectorstore

    def _create_new_index(self) -> VectorStore:
        """
        Load the manual, split into chunks, embed, and save a new FAISS index.
        Returns:
              VectorStore: Newly created and saved FAISS vectorstore.
        """
        #TODO:
        # - Load 'microwave_manual.txt' using TextLoader
        manual = TextLoader("t4_rag_fundamentals/microwave_manual.txt", encoding="utf-8").load()
        # - Split documents into chunks using RecursiveCharacterTextSplitter
        #   (chunk_size=300, chunk_overlap=50, separators=["\n\n", "\n", "."])
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50,
            separators=["\n\n", "\n", "."]
        )
        chunks = text_splitter.split_documents(manual)
        # - Create a FAISS vectorstore from chunks and self.embeddings using FAISS.from_documents()
        vectorstore = FAISS.from_documents(chunks, self.embeddings)
        # - Save the index locally using vectorstore.save_local("microwave_faiss_index")
        vectorstore.save_local("microwave_faiss_index")
        # - Return the vectorstore
        return vectorstore

    def retrieve_context(self, query: str, k: int = 4, score=0.3):
        """
        Retrieve the context for a given query.
        Args:
              query (str): The query to retrieve the context for.
              k (int): The number of relevant documents(chunks) to retrieve.
              score (float): The similarity score between documents and query. Range 0.0 to 1.0.
        """
        #TODO:
        # - Search the vectorstore using similarity_search_with_relevance_scores() with k and score_threshold parameters
        similar_docs_with_scores = self.vectorstore.similarity_search_with_relevance_scores(query, k=k, score_threshold=score)
        # - Iterate over results, collect each doc's page_content, and print its relevance score
        for doc, score in similar_docs_with_scores:
            print(f"Relevance score: {score:.4f}, Content: {doc.page_content}")
            
        # - Return all collected chunks joined with "\n\n" as a single context string
        return "\n\n".join([doc.page_content for doc, _ in similar_docs_with_scores])

    def augment_prompt(self, query: str, context: str):
        """
        Inject retrieved context and user query into the prompt template.
        Args:
              query (str): The user's question.
              context (str): Retrieved context from the vectorstore.
        Returns:
              str: Formatted prompt ready for the LLM.
        """
        #TODO:
        # - Format _USER_PROMPT template substituting {context} and {query}
        augmented_prompt = _USER_PROMPT.format(context=context, query=query)
        # - Print the resulting augmented prompt
        print(augmented_prompt)
        # - Return the formatted string
        return augmented_prompt

    def generate_answer(self, augmented_prompt: str):
        """
        Send the augmented prompt to the LLM and return its response.
        Args:
              augmented_prompt (str): The prompt with injected context and query.
        Returns:
              str: The LLM-generated answer.
        """
        #TODO:
        # - Build a messages list: [SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=augmented_prompt)]
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=augmented_prompt)
        ]
        # - Invoke self.llm_client.generate with a batch containing the messages list
        # The ChatAnthropic.generate(...) returns an LLMResult. Extract the text from generations.
        llm_result = self.llm_client.generate(messages=[messages])
        # Safely extract the first generated text
        try:
            response_text = llm_result.generations[0][0].text
        except Exception:
            # Fallback if structure differs
            response_text = getattr(llm_result, "text", "")
        # - Print the response content
        print(response_text)
        # - Return the response content string
        return response_text


def main(rag: MicrowaveRAG):
    #TODO:
    # - Print a welcome message
    print("Welcome to the Microwave RAG Application!")
    # - Run an infinite loop that reads user input with input()
    while True:
        query = input("Enter your question (or 'quit' to exit): ")
        if query.lower() == "quit":
            break
        # - For each question execute the 3-step RAG pipeline:
        #   - Step 1 (Retrieval):   call rag.retrieve_context() to fetch relevant chunks
        #   - Step 2 (Augmentation): call rag.augment_prompt() to build the prompt
        #   - Step 3 (Generation):  call rag.generate_answer() to get the LLM answer
        context = rag.retrieve_context(query)
        augmented_prompt = rag.augment_prompt(query, context)
        rag.generate_answer(augmented_prompt)


#TODO:
# Start the application by calling main() and passing a MicrowaveRAG instance:
main(
    MicrowaveRAG(
        embeddings=HuggingFaceEmbeddings(),
        llm_client=ChatAnthropic(
            temperature=0.0,
            model="claude-haiku-4-5-20251001",
            anthropic_api_key=SecretStr(ANTHROPIC_API_KEY)
        )
    )
)
# - Create ChatAnthropic with temperature=0.0, model='claude-sonnet-4-5-20250929' and api_key=ANTHROPIC_API_KEY
# - Wrap both in a MicrowaveRAG instance and pass it to main()