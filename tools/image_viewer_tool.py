"""Tool for viewing and transcribing images with GPT-4o multimodal capabilities."""

import base64
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import openai
from crewai.tools import BaseTool

class ImageViewerTool(BaseTool):
    name: str = "image_viewer"
    description: str = "View and transcribe handwritten text from images using GPT-4o's vision capabilities. Returns complete transcription with word statistics."
    
    def _run(self, image_path: str, sequential_thinking_session_id: Optional[str] = None) -> str:
        """View an image and transcribe all handwritten text using GPT-4o.
        
        Args:
            image_path: Path to the image file to view and transcribe
            sequential_thinking_session_id: Optional session ID for complex handwriting analysis
            
        Returns:
            JSON string with transcription and statistics
        """
        try:
            # Verify file exists
            path = Path(image_path)
            if not path.exists():
                return json.dumps({"error": f"Image file not found at {image_path}"})
            
            # Read and encode the image
            with open(path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
            
            # Create the transcription prompt
            prompt = """You are transcribing a handwritten Spanish manuscript page. Follow these steps:

1. CRITICAL: Start from the VERY TOP of the page - capture EVERY line including the first 4-5 lines
2. VIEW the entire image carefully and transcribe EXACTLY what you see written
3. Do NOT skip any lines at the beginning - start from the absolute top
4. When handwriting is unclear:
   - Use context clues, logic, and letter placement to make your best effort
   - Mark uncertain words with [?] after them
   - Mark completely illegible words as [illegible]
5. Preserve original line breaks where clear

After transcription, provide statistics in this format:
{
  "transcription": "full text here with line breaks preserved",
  "stats": {
    "total_words": X,
    "normal_transcription": X,
    "context_logic_transcription": X,
    "unable_to_transcribe": X
  },
  "unclear_sections": ["list of unclear parts"]
}

Transcribe everything you see, maintaining the original Spanish text exactly as written."""

            # PASS 1: Initial transcription
            response1 = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            # PASS 2: Review and improve unclear sections
            pass2_prompt = f"""Review this transcription and the image again. Focus on any [?] or [illegible] sections.
Previous transcription: {response1.choices[0].message.content}

Look at the image again and try to improve any unclear parts. Return the same JSON format with improvements."""
            
            response2 = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": pass2_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            # PASS 3: Final verification and quality check
            pass3_prompt = f"""Final pass - verify the transcription is complete and accurate.
Current transcription: {response2.choices[0].message.content}

CRITICAL: Ensure the FIRST 4-5 lines at the TOP of the page are included. If missing, add them now.
Return the final JSON format."""
            
            response3 = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": pass3_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            # Use the final pass result
            result = response3.choices[0].message.content
            
            # Try to parse as JSON, or wrap in JSON if not
            try:
                result_json = json.loads(result)
            except:
                # If not JSON, create proper structure
                lines = result.strip().split('\n')
                result_json = {
                    "transcription": result,
                    "stats": {
                        "total_words": len(result.split()),
                        "normal_transcription": "Unable to parse",
                        "context_logic_transcription": "Unable to parse",
                        "unable_to_transcribe": "Unable to parse"
                    },
                    "unclear_sections": []
                }
            
            return json.dumps(result_json, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Error transcribing image: {str(e)}"})