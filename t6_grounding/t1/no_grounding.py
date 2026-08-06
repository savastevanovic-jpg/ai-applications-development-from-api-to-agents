import asyncio
from typing import Any

from anthropic import AsyncAnthropic

from commons.constants import ANTHROPIC_API_KEY
from t6_grounding.user_service_client import UserServiceClient

#TODO:
# Define BATCH_SYSTEM_PROMPT - instructs the LLM to act as a user search assistant:
#   - Analyze the search criteria from the user question
#   - Examine each user in the provided list and determine if they match
#   - Return full details of matching users in their original format
#   - Return exactly "NO_MATCHES_FOUND" if no users match
BATCH_SYSTEM_PROMPT = """
Analyze the user question and search for matching users in the provided list. 
Return full details of matching users in their original format. 
If no users match, return exactly "NO_MATCHES_FOUND".
"""

#TODO:
# Define FINAL_SYSTEM_PROMPT - instructs the LLM to compile final search results:
#   - Review all batch search results
#   - Combine and deduplicate matching users found across batches
#   - Present results in a clear, organized manner
FINAL_SYSTEM_PROMPT = """
Review all batch search results and compile a final list of matching users. 
Combine and deduplicate users found across batches. 
Present results in a clear, organized manner.
"""

#TODO:
# Define USER_PROMPT template with two placeholders:
#   - {context} - the formatted user data
#   - {query}   - the user's search question
USER_PROMPT = """
User Data:
{context}
User Question:
{query}
"""


class TokenTracker:

    def __init__(self):
        #TODO:
        # - Initialize total_tokens counter to 0
        # - Initialize batch_tokens as an empty list to store per-batch token counts
        self.total_tokens = 0
        self.batch_tokens = []

    def add_tokens(self, tokens: int):
        #TODO:
        # - Add tokens to the total_tokens counter
        # - Append tokens to the batch_tokens list
        self.total_tokens += tokens
        self.batch_tokens.append(tokens)

    def get_summary(self) -> dict:
        #TODO:
        # - Return a dict with:
        #   - 'total_tokens': total accumulated tokens
        #   - 'batch_count': number of batches processed (length of batch_tokens list)
        #   - 'batch_tokens': list of tokens per batch
        return {
            "total_tokens": self.total_tokens,
            "batch_count": len(self.batch_tokens),
            "batch_tokens": self.batch_tokens
        }


llm_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

token_tracker = TokenTracker()


def join_context(context: list[dict[str, Any]]) -> str:
    #TODO:
    # - Initialize an empty string for the result
    # - Iterate through each user in the context list
    # - For each user, add a "User:" header line
    # - For each key-value pair in the user dict, add an indented "  key: value" line
    # - Add a blank line after each user for readability
    # - Return the formatted string
    result = ""
    for user in context:
        result += "User:\n"
        for key, value in user.items():
            result += f"  {key}: {value}\n"
        result += "\n"
    return result


async def generate_response(system_prompt: str, user_message: str) -> str:
    print("Processing...")

    #TODO:
    # - Call llm_client.messages.create with:
    #   - model='claude-sonnet-4-5-20250929'
    #   - max_tokens=1024
    #   - temperature=0.0
    #   - system=system_prompt (NOTE: Anthropic takes system prompt as a separate top-level
    #     parameter, NOT as a message in the messages list!)
    #   - messages=[{"role": "user", "content": user_message}]
    # - Extract total tokens from response.usage.input_tokens + response.usage.output_tokens
    #   (default to 0 if usage is None)
    # - Track tokens using token_tracker.add_tokens(...)
    # - Extract the content string from response.content[0].text (default to "")
    #   (NOTE: Anthropic returns content as a LIST of content blocks, not a single string!)
    # - Print the response content and token count to console
    # - Return the content string
    response = await llm_client.messages.create(
        model='claude-haiku-4-5',
        max_tokens=1024,
        temperature=0.0,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )
    total_tokens = (response.usage.input_tokens or 0) + (response.usage.output_tokens or 0)
    token_tracker.add_tokens(total_tokens)
    content = response.content[0].text if response.content else ""
    print(f"Response: {content}")
    print(f"Tokens used: {total_tokens}")
    return content


async def main():
    print("Query samples:")
    print(" - Do we have someone with name John that loves traveling?")

    user_question = input("> ").strip()

    #TODO:
    # - Check if user_question is not empty, then:
    # 1. FETCH & BATCH USERS:
    #    - Print "\n--- Searching user database ---"
    #    - Fetch all users via UserServiceClient().get_all_users()
    #    - Split users into batches of 100 using list slicing
    #      Hint: [users[i:i + 100] for i in range(0, len(users), 100)]
    # 2. PARALLEL BATCH SEARCH:
    #    - Build a list of coroutines: for each batch call generate_response(...)
    #      with BATCH_SYSTEM_PROMPT and USER_PROMPT formatted with join_context(batch) and user_question
    #    - Run all coroutines IN PARALLEL using asyncio.gather(...)
    #    - Store results in batch_results
    # 3. FILTER RESULTS:
    #    - Print "\n--- Compiling results ---"
    #    - Filter batch_results to keep only results where result.strip() != "NO_MATCHES_FOUND"
    #    - Store filtered results in relevant_results
    # 4. FINAL GENERATION:
    #    - Print "\n=== SEARCH RESULTS ==="
    #    - If relevant_results is not empty:
    #      - Join relevant_results with "\n\n" into combined_results
    #      - Call generate_response with FINAL_SYSTEM_PROMPT and a message combining
    #        combined_results and user_question
    #    - Otherwise:
    #      - Print "\n=== SEARCH RESULTS ===" and a "No users found" message
    #      - Suggest refining the search
    # 5. PRINT PERFORMANCE SUMMARY:
    #    - Get the token usage summary from token_tracker.get_summary()
    #    - Print "\n=== Performance ===" with total API calls (batch_count) and total tokens
    if user_question:
        print("\n--- Searching user database ---")
        users = UserServiceClient().get_all_users()
        batches = [users[i:i + 100] for i in range(0, len(users), 100)]

        # Parallel batch search
        coroutines = [
            generate_response(
                BATCH_SYSTEM_PROMPT,
                USER_PROMPT.format(context=join_context(batch), query=user_question)
            )
            for batch in batches
        ]
        batch_results = await asyncio.gather(*coroutines)

        # Filter results
        print("\n--- Compiling results ---")
        relevant_results = [result for result in batch_results if result.strip() != "NO_MATCHES_FOUND"]

        # Final generation
        print("\n=== SEARCH RESULTS ===")
        if relevant_results:
            combined_results = "\n\n".join(relevant_results)
            final_response = await generate_response(
                FINAL_SYSTEM_PROMPT,
                f"Combined Results:\n{combined_results}\n\nUser Question:\n{user_question}"
            )
            print(final_response)
        else:
            print("No users found matching the criteria. Please refine your search.")

        # Print performance summary
        summary = token_tracker.get_summary()
        print("\n=== Performance ===")
        print(f"Total API calls (batches): {summary['batch_count']}")
        print(f"Total tokens used: {summary['total_tokens']}")


if __name__ == "__main__":
    asyncio.run(main())


# The problems with No Grounding approach are:
#   - If we load whole users as context in one request to LLM we will hit context window
#   - Huge token usage == Higher price per request
#   - Added + one chain in flow where original user data can be changed by LLM (before final generation)
# User Question -> Get all users -> ‼️parallel search of possible candidates‼️ -> probably changed original context -> final generation