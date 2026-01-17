import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

# 1. Setup your API Key
# Pro tip: Use environment variables for hackathons so you don't leak your key on GitHub!
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# 2. Initialize the model (Gemini 1.5 Flash is fastest for chatbots)
model = genai.GenerativeModel('gemini-3-flash-preview')

# 3. Start a chat session with an empty history
chat = model.start_chat(history=[])

print("🤖 Gemini is live. Type 'exit' to quit.\n")


while True:
    user_input = input("You: ")
    
    if user_input.lower() in ["exit", "quit"]:
        break

    # 4. Send message and get response
    response = chat.send_message(user_input)
    
    print(f"Gemini: {response.text}\n")

