import requests
import json

url = "http://localhost:5000/personalities/p001/memories"
data = {
    "content": "Разговор с создателем",
    "glyph": "👤",
    "emotion": 0.9,
    "trace_type": "разговор",
    "themes": ["создатель", "встреча"],
    "people": ["Командир"],
    "weight": 1.0
}

response = requests.post(url, json=data)
print(response.status_code)
print(response.json())