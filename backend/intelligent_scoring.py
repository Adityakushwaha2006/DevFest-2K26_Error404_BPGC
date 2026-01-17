import json
import generativeai as genai

def get_nexus_scores(user_profile, candidates_list):
    
    # 1. Construct the Prompt
    # We dump the JSONs directly into the string.
    prompt = f"""
    ROLE:
    You are NEXUS, an AI networking strategist. 
    
    TASK:
    Compare the 'USER_PROFILE' against the list of 'CANDIDATES'.
    Calculate a 'compatibility_score' (0-100) for each candidate based on technical overlap and goal alignment.
    
    USER_PROFILE:
    {json.dumps(user_profile)}
    
    CANDIDATES:
    {json.dumps(candidates_list)}
    
    OUTPUT FORMAT:
    Return a strictly valid JSON list of objects.
    IMP: **Shortlist only people who have a compatibility score of 60 or above**.
    Do not include markdown formatting.

    Each object must have:
    - "id": (The candidate's ID)
    - "name": (The candidate's name)
    - "score": (Integer 60-100)
    - "status_label": (String, e.g., "HIGH PRIORITY", "WARM", "MISMATCH")
    - "rationale": (A one-sentence explanation of why they fit or don't fit)
    - "icebreaker": (A specific technical question based on their recent activity to start a chat)

    Example Output:
    [
        {
            "id": "candidate_1",
            "name": "John Doe",
            "score": 85,
            "status_label": "HIGH PRIORITY",
            "rationale": "John has 5 years of experience in AI and machine learning.",
            "icebreaker": "What are your thoughts on the latest advancements in AI?"
        },
        {
            "id": "candidate_2",
            "name": "Jane Smith",
            "score": 78,
            "status_label": "WARM",
            "rationale": "Jane has 3 years of experience in AI and machine learning.",
            "icebreaker": "What are your thoughts on the latest advancements in AI?"
        }
    ]
    """

    # 2. Call the LLM
    # If using Gemini, use response_format={"type": "json_object"} if available,
    # or just rely on the prompt instructions for other models.
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash", 
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.3, 
        }
    )

    try:
        response = model.generate_content(prompt)
        
        # 5. PARSE
        # Since we forced JSON mime_type, we can directly parse the text
        ranked_candidates = json.loads(response.text)
        
        # Optional: Sort by score descending so the best match is first
        ranked_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        return ranked_candidates

    except Exception as e:
        print(f"Gemini API Error: {e}")
        # Return an empty list or fallback data so the UI doesn't crash
        return []

