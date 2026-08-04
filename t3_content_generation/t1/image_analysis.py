import base64

from commons.constants import OPENAI_HOST
from t3_content_generation._openai_client import OpenAIClientT3


# https://developers.openai.com/api/docs/guides/images-vision?format=url&lang=curl
# https://developers.openai.com/api/docs/guides/images-vision?format=base64-encoded

#TODO:
# You need to analyse these 2 images:
#   - https://a-z-animals.com/media/2019/11/Elephant-male-1024x535.jpg
#   - in this folder we have 'logo.png', load it as encoded data (see documentation)
# ---
# Hints:
#   - Use OpenAIClientT3 to connect to OpenAI API
#   - Use /v1/chat/completions endpoint
#   - Function to encode image to base64 you can find in documentation
# ---
# In the end load both images (url and base64 encoded 'logo.png'), ask "Generate poem based on images" and se what will happen?
host = OpenAIClientT3(OPENAI_HOST+"/v1/chat/completions")
response = host.call(
    model="gpt-5.4-mini",
    messages=[
        {
            "role": "system",
            "content": "You are an assistant who answers concisely and informatively."
        },
        {
            "role": "user",
            "content": "Generate poem based on images"
        },
        {
            "role": "user",
            "content": "https://a-z-animals.com/media/2019/11/Elephant-male-1024x535.jpg"
        },
        {
            "role": "user",
            "content": "data:image/png;base64," + base64.b64encode(open("t3_content_generation/t1/logo.png", "rb").read()).decode("utf-8")
        }
    ],
    max_completion_tokens=1024,
    temperature=0.7,
    n=1,
    stop=None
)
response_text = response["choices"][0]["message"]["content"]

print(response_text)