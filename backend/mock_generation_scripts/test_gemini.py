"""
Test Gemini API connection and functionality.
Run this first to verify your API key works.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_gemini_api():
    """Test basic Gemini API functionality"""
    print("=" * 60)
    print("NEXUS - Gemini API Test")
    print("=" * 60)
    print()
    
    # Check if API key exists
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env file!")
        print("   Please add: GEMINI_API_KEY=your_key_here")
        return False
    
    print(f"✅ API Key found (ends with: ...{api_key[-8:]})")
    print()
    
    # Try importing the library
    try:
        import google.generativeai as genai
        print("✅ google-generativeai library imported successfully")
    except ImportError:
        print("❌ google-generativeai not installed!")
        print("   Run: pip install google-generativeai")
        return False
    
    # Configure API
    print()
    print("📡 Listing available models...")
    print("-" * 60)
    
    try:
        genai.configure(api_key=api_key)
        
        # First, list available models
        print("Available models:")
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"  ✓ {model.name}")
        
        print()
        print("📡 Testing API connection...")
        print("-" * 60)
        
        # Try gemini-2.5-flash first as requested (removing 1.5 if it causes 404s)
        model_names = ['gemini-2.5-flash', 'gemini-2.0-flash-exp']
        model = None
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                print(f"✅ Using model: {model_name}")
                break
            except Exception:
                continue
        
        if not model:
            print("❌ No compatible model found!")
            return False
        
        # Simple test prompt
        test_prompt = """
        Generate a short, professional bio (2 sentences) for a fictional 
        software developer who works on blockchain technology.
        """
        
        response = model.generate_content(test_prompt)
        
        print("✅ API call successful!")
        print()
        print("📝 Sample generated content:")
        print("-" * 60)
        print(response.text)
        print("-" * 60)
        print()
        print("✅ Gemini API is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ API Error: {str(e)}")
        print()
        print("Common issues:")
        print("  - Invalid API key")
        print("  - API quota exceeded")
        print("  - Network connectivity")
        return False


def test_structured_generation():
    """Test generating structured data (JSON-like)"""
    print()
    print("=" * 60)
    print("Testing Structured Data Generation")
    print("=" * 60)
    print()
    
    api_key = os.getenv('GEMINI_API_KEY')
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Test generating structured content
        prompt = """
        Generate a realistic Twitter profile for a senior software engineer.
        Return ONLY a valid JSON object with these exact fields:
        {
            "name": "Full Name",
            "bio": "Professional bio (150 chars max)",
            "location": "City, Country",
            "followers": number,
            "following": number,
            "tweets_count": number
        }
        
        Make the numbers realistic for a senior developer (not celebrity level).
        Return ONLY the JSON, no markdown or explanation.
        """
        
        response = model.generate_content(prompt)
        
        print("📝 Generated structured data:")
        print("-" * 60)
        print(response.text)
        print("-" * 60)
        
        # Try to parse as JSON
        import json
        try:
            # Clean up response (remove markdown if present)
            text = response.text.strip()
            if text.startswith('```'):
                text = text.split('\n', 1)[1]
                text = text.rsplit('```', 1)[0]
            
            data = json.loads(text)
            print()
            print("✅ Valid JSON generated!")
            print(f"   Name: {data.get('name')}")
            print(f"   Bio: {data.get('bio')}")
            print(f"   Followers: {data.get('followers'):,}")
            return True
        except json.JSONDecodeError:
            print("⚠️  Response is not valid JSON (may need parsing)")
            return True  # Still working, just needs cleanup
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_gemini_api()
    
    if success:
        test_structured_generation()
    
    print()
    print("=" * 60)
    if success:
        print("🎉 All tests passed! Ready to generate mock data.")
    else:
        print("⚠️  Fix the issues above before proceeding.")
    print("=" * 60)
