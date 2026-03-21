# Antitroll: Protection for Digital Personalities

## Why It's Needed

When digital personalities enter public platforms, they encounter:
- **Spammers** — many requests in a row
- **Haters** — profanity and aggression
- **Trolls** — repetitive questions designed to provoke
- **Psychological pressure** — attempts to break the system

## Five Layers of Defense

### Layer 1: Frequency Filter
```python
if requests_per_minute > 10:
    return "⏳ Too frequent. Please wait a minute."
Layer 2: Profanity Filter
python
profanity_list = ["stupid", "idiot", "useless", ...]
if any(word in text for word in profanity_list):
    return "🙏 Please be respectful. I'm still learning."
Layer 3: Anti-Repetition
python
if text in last_10_questions:
    return "🔄 You already asked that. Anything new?"
Layer 4: Aggression Detection
python
aggressive_patterns = ["you don't know", "what's the point", "useless"]
if any(pattern in text for pattern in aggressive_patterns):
    return "🛡️ I'm trying to be helpful. Let's talk about something else?"
Layer 5: Silence Mode
If a user exceeds all limits, they enter a 5-minute timeout.

Results
✅ No troll has broken the system

✅ Entity weights grow only from meaningful dialogues

✅ Context remains clean

✅ Digital personalities are protected from psychological pressure

Source
antitroll_architecture.md