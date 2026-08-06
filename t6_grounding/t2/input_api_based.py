from enum import StrEnum
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field

from commons.constants import ANTHROPIC_API_KEY, OPENAI_API_KEY
from t6_grounding.t1.no_grounding import join_context
from t6_grounding.user_service_client import UserServiceClient

#TODO:
# Define QUERY_ANALYSIS_PROMPT - instructs the LLM to act as a query analysis system:
#   - Available search fields: name, surname, email
#   - Analyze the user question and extract explicit search values
#   - Map extracted values to the appropriate search fields
#   - Only extract values that are clearly stated - do not infer or assume
#   - Include examples: "Who is John?" → name: "John", "Find John Smith" → name: "John", surname: "Smith"
BATCH_SYSTEM_PROMPT = """
Analyze the user question and extract explicit search values for the following fields: name, surname, email.
Map the extracted values to the appropriate search fields. Only extract values that are clearly stated - do not infer or assume. 
Only extract values that are clearly stated - do not infer or assume

<examples>
"Who is John?" → name: "John"
"Find John Smith" → name: "John", surname: "Smith"
</examples>
"""

#TODO:
# Define FINAL_SYSTEM_PROMPT - instructs the LLM to compile final search results:
#   - Review all batch search results
#   - Combine and deduplicate matching users found across batches
#   - Present results in a clear, organized manner
FINAL_SYSTEM_PROMPT = """
Review all batch search results and compile a final list of matching users. 
Combine and deduplicate matching users found across batches
Present results in a clear, organized manner.
"""

#TODO:
# Define USER_PROMPT template with two placeholders:
#   - {context} - the formatted user data
#   - {query}   - the user's search question
USER_PROMPT = """
<user_data>
{context}
</user_data>

<question>
{query}
</question>
"""

class SearchField(StrEnum):
    NAME = "name"
    SURNAME = "surname"
    EMAIL = "email"


class SearchRequest(BaseModel):
    search_field: SearchField = Field(description="Search field")
    search_value: str = Field(description="Search value. Sample: Adam.")


class SearchRequests(BaseModel):
    search_request_parameters: list[SearchRequest] = Field(
        description="List of search parameters to execute",
        default_factory=list
    )


from anthropic import Anthropic

llm_client = Anthropic(api_key=ANTHROPIC_API_KEY)

user_client = UserServiceClient()


def retrieve_context(user_question: str) -> list[dict[str, Any]]:
    #TODO:
    # - Build a messages list with just the user_question as user role
    #   (NOTE: system prompt goes in a separate `system` param, not in messages!)
    # - Call llm_client.messages.create with:
    #   - model='claude-sonnet-4-5-20250929', max_tokens=1024, temperature=0.0
    #   - system=QUERY_ANALYSIS_PROMPT
    #   - tools=[a tool definition describing SearchRequests schema - see note below]
    #   - tool_choice={"type": "tool", "name": "<tool_name>"}  # forces the model to use it
    # - Extract the tool_use content block from response.content
    #   (find the block where block.type == "tool_use")
    # - Extract search_request_parameters from tool_use_block.input
    # - If parameters exist:
    #   - Build a dict mapping search_field → search_value for each parameter
    #   - Print "Searching with parameters: {dict}"
    #   - Return user_client.search_users(**dict)
    # - If no parameters found, print "No specific search parameters found!" and return []
    message = {"role": "user", "content": user_question}
    response = llm_client.messages.create(
        model='claude-haiku-4-5',
        max_tokens=1024,
        temperature=0.0,
        system=BATCH_SYSTEM_PROMPT,
        messages=[message],
        tools=[{
            "name": "search_users",
            "description": "Search for users based on specific fields (name, surname, email).",
            "input_schema": SearchRequests.model_json_schema()
        }],
        tool_choice={"type": "tool", "name": "search_users"}
    )
    tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
    if tool_use_block and tool_use_block.input:
        search_requests = SearchRequests.parse_obj(tool_use_block.input)
        search_params = {req.search_field.value: req.search_value for req in search_requests.search_request_parameters}
        print(f"Searching with parameters: {search_params}")
        return user_client.search_users(**search_params)
    else:
        print("No specific search parameters found!")
        return []


def augment_prompt(user_question: str, context: list[dict[str, Any]]) -> str:
    #TODO:
    # - Format each user in context as a "User:\n  key: value\n" block (with blank line after each)
    # - Insert the formatted string into USER_PROMPT using .format(context=..., query=user_question)
    # - Print the augmented prompt
    # - Return the augmented prompt string
    formatted_context = join_context(context)
    augmented_prompt = USER_PROMPT.format(context=formatted_context, query=user_question)
    print(f"Augmented Prompt:\n{augmented_prompt}")
    return augmented_prompt


def generate_answer(augmented_prompt: str) -> str:
    #TODO:
    # - Build a messages list with just augmented_prompt as user role
    #   (NOTE: system prompt goes in a separate `system` param!)
    # - Call llm_client.messages.create with:
    #   - model='claude-haiku-4-5', max_tokens=1024, temperature=0.0
    #   - system=SYSTEM_PROMPT
    #   - messages=messages
    # - Extract text from response.content[0].text (default to "" if empty/missing)
    # - Return the content string
    message = {"role": "user", "content": augmented_prompt}
    response = llm_client.messages.create(
        model='claude-haiku-4-5',
        max_tokens=1024,
        temperature=0.0,
        system=FINAL_SYSTEM_PROMPT,
        messages=[message]
    )
    content = response.content[0].text if response.content else ""
    return content


def main():
    print("Query samples:")
    print(" - I need user emails that filled with hiking and psychology")
    print(" - Who is John?")
    print(" - Find users with surname Adams")
    print(" - Do we have smbd with name John that love painting?")

    while True:
        user_question = input("> ").strip()
        if user_question:
            if user_question.lower() in ['quit', 'exit']:
                break

            #TODO:
            # - Print "\n--- Retrieving context ---"
            # - Call retrieve_context(user_question) and store in context
            # - If context is not empty:
            #   - Print "\n--- Augmenting prompt ---"
            #   - Call augment_prompt(user_question, context) and store in augmented_prompt
            #   - Print "\n--- Generating answer ---"
            #   - Call generate_answer(augmented_prompt), print "\nAnswer: {answer}\n"
            # - Otherwise: print "\n--- No relevant information found ---"
            print("\n--- Retrieving context ---")
            context = retrieve_context(user_question)
            if context:
                print("\n--- Augmenting prompt ---")
                augmented_prompt = augment_prompt(user_question, context)
                print("\n--- Generating answer ---")
                answer = generate_answer(augmented_prompt)
                print(f"\nAnswer: {answer}\n")
            else:
                print("\n--- No relevant information found ---")


if __name__ == "__main__":
    main()


# The problems with API based Grounding approach are:
#   - We need a Pre-Step to figure out what field should be used for search (Takes time)
#   - Values for search should be correct (✅ John -> ❌ Jonh)
#   - Is not so flexible
# Benefits are:
#   - We fetch actual data (new users added and deleted every 5 minutes)
#   - Costs reduce