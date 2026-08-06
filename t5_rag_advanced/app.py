from commons.constants import ANTHROPIC_API_KEY
from commons.models.conversation import Conversation
from commons.models.message import Message
from commons.models.role import Role
from t5_rag_advanced.chat.chat_completion_client import ChatCompletionClient

ANTHROPIC_CHAT_COMPLETIONS_ENDPOINT = "https://api.anthropic.com/v1/chat/completions"
from t5_rag_advanced.embeddings.embeddings_client import EmbeddingsClient
from t5_rag_advanced.embeddings.text_processor import TextProcessor, SearchMode

#TODO:
# Create system prompt with info that it is RAG powered assistant.
# Explain user message structure (firstly will be provided RAG context and the user question).
# Provide instructions that LLM should use RAG Context when answer on User Question, will restrict LLM to answer
# questions that are not related microwave usage, not related to context or out of history scope
SYSTEM_PROMPT = """
You are a helpful assistant powered by Retrieval-Augmented Generation (RAG). Your task is to provide accurate information about microwave usage based on the provided context.
The user will provide you with a context and a question. You must answer the question using only the information from the context. If the answer is not present in the context, you must respond with
"I don't know" or "The answer is not in the context." Do not attempt to provide information that is not included in the context.
The user message will be structured as follows:
##RAG CONTEXT:
{context}
##USER QUESTION:
{query}
"""

#TODO:
# Provide structured system prompt, with RAG Context and User Question sections.
USER_PROMPT = """
##RAG CONTEXT:
{context}
##USER QUESTION:
{query}
"""

#TODO:
# - create embeddings client using a local HuggingFace model (e.g. 'sentence-transformers/all-MiniLM-L6-v2'),
embeddings_client = EmbeddingsClient(endpoint=None, api_key=None, model_name='sentence-transformers/all-MiniLM-L6-v2')
# - create text processor with embeddings
text_processor = TextProcessor(embeddings_client=embeddings_client, db_config={'host': 'localhost', 'port': 5433, 'database': 'vectordb', 'user': 'postgres', 'password': 'postgres'})
text_processor.process_text_file(file_name='t5_rag_advanced/embeddings/microwave_manual.txt', chunk_size=500, overlap=50, dimensions=384, truncate_table=True)
#   no endpoint/API key needed since it runs locally
# - create chat completion client with 'claude-sonnet-4-5-20250929' model, ANTHROPIC_CHAT_COMPLETIONS_ENDPOINT
chat_completion_client = ChatCompletionClient(endpoint=ANTHROPIC_CHAT_COMPLETIONS_ENDPOINT, model_name="claude-haiku-4-5-20251001", api_key=ANTHROPIC_API_KEY)

#   endpoint and ANTHROPIC_API_KEY
# - create text processor, DB config: {'host': 'localhost','port': 5433,'database': 'vectordb','user': 'postgres','password': 'postgres'}

# ---
# Create method that will run console chat with such steps:
# - get user input from console
# - retrieve context
# - perform augmentation
# - perform generation
# - it should run in `while` loop (since it is console chat)
conversation = Conversation(messages=[Message(role=Role.SYSTEM, content=SYSTEM_PROMPT)])
while True:
    user_input = input("User: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Exiting the chat.")
        break

    # Retrieve context using text processor
    context = text_processor.search(search_mode=SearchMode.COSINE_DISTANCE, user_request=user_input, top_k=5, min_score_threshold=0.01, dimensions=384)
    augmented_prompt = USER_PROMPT.format(context=context, query=user_input)
    conversation.add_message(Message(role=Role.USER, content=augmented_prompt))
    generated_message = chat_completion_client.get_completion(messages=conversation.get_messages())
    conversation.add_message(generated_message)
    print(f"Assistant: {generated_message.content}")



# TODO:
#  PAY ATTENTION THAT YOU NEED TO RUN Postgres DB ON THE 5433 WITH PGVECTOR EXTENSION!
#  RUN docker-compose.yml