import base64
from datetime import datetime

from commons.constants import OPENAI_HOST
from t3_content_generation._openai_client import OpenAIClientT3


# https://developers.openai.com/api/reference/resources/images/methods/generate
# ---
# Request:
# curl -X POST "https://api.openai.com/v1/images/generations" \
#     -H "Authorization: Bearer $OPENAI_API_KEY" \
#     -H "Content-type: application/json" \
#     -d '{
#         "model": "gpt-image-2",
#         "prompt": "smiling catdog."
#     }'
# Response:
# {
#   "created": 1699900000,
#   "data": [
#     {
#       "b64_json": Qt0n6ArYAEABGOhEoYgVAJFdt8jM79uW2DO...,
#     }
#   ]
# }

#TODO:
# You need to create some images with `gpt-image-2` model:
#   - Generate an image with 'Smiling catdog'
#   - Decode and save it locally
# ---
# Hints:
#   - Use OpenAIClientT3 to connect to OpenAI API
#   - Use /v1/images/generations endpoint
#   - The image will be returned in base64 format
client = OpenAIClientT3(OPENAI_HOST + "/v1/images/generations")
response = client.call(
    model="gpt-image-2",
    prompt="Smiling catdog",
    size="1024x1024",
    n=1
)
image_base64 = response["data"][0]["b64_json"]
# Decode the base64 image and save it locally
image_data = base64.b64decode(image_base64)
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
image_filename = f"smiling_catdog_{timestamp}.png"
with open(image_filename, "wb") as f:
    f.write(image_data)
print(f"Image saved as {image_filename}") 