
# app/services/content_generator.py

def generate_dummy_content(topic: str, card_type: str) -> str:
    """
    Simple placeholder generator for different card types.
    Later we will replace this with a real OpenAI call.
    """
    if card_type == "flashcard":
        return f"Q: What is {topic}?\nA: This is a simple explanation of {topic}."
    elif card_type == "summary":
        return f"Summary for {topic}: this is a short high-level summary."
    elif card_type == "quiz":
        return f"Quiz question about {topic}: write one key concept related to it."
    elif card_type == "task":
        return f"Task for {topic}: perform a small exercise that uses this topic in practice."
    elif card_type == "usecase":
        return f"Use case for {topic}: describe when and why you would use {topic}."
    elif card_type == "mindmap":
        return f"Mindmap structure for {topic}: main idea -> subtopic A, subtopic B, subtopic C."
    else:
        return f"Generic content for {topic} (type: {card_type})."
