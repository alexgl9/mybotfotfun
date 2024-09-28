import os
import requests

HF_API_TOKEN = os.getenv('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')  # Змінна середовища з токеном
model_url = "https://api-inference.huggingface.co/models/gpt-neo-125M"

def test_hugging_face_token():
    headers = {"Authorization": f"Bearer {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}"}
    response = requests.post(model_url, headers=headers, json={"inputs": "Hello, how are you?"})
    if response.status_code == 200:
        print("Token is valid and the model is accessible.")
        print("Response:", response.json())
    else:
        print("Failed to access the model.")
        print("Status Code:", response.status_code)
        print("Response:", response.json())

test_hugging_face_token()
