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
    description: str = "View and transcribe handwritten text from images using GPT-4o's vision capabilities with 3-pass OCR processing. Returns complete transcription with processing statistics."
    
    def _run(self, image_path: str, sequential_thinking_session_id: Optional[str] = None) -> str:
        """View an image and transcribe all handwritten text using 3-pass OCR with GPT-4o.
        
        Implements exactly 3 OCR passes:
        1. Contextual pass - Overall page understanding and initial transcription
        2. Word-level pass - Focus on individual words and unclear sections
        3. Letter-level pass - Character-by-character analysis for final accuracy
        
        Args:
            image_path: Path to the image file to view and transcribe
            sequential_thinking_session_id: Optional session ID for complex handwriting analysis
            
        Returns:
            JSON string with transcription and detailed processing statistics
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
            
            # PASS 1: CONTEXTUAL ANALYSIS - Overall page understanding
            contextual_prompt = """You are performing PASS 1 of 3 for handwritten manuscript transcription.

CONTEXTUAL ANALYSIS INSTRUCTIONS:
1. CRITICAL: Examine the ENTIRE page from TOP to BOTTOM - capture EVERY line including the first 4-5 lines at the very top
2. Understand the overall context, layout, and writing style
3. Identify the language and general content theme
4. Perform initial transcription using contextual understanding
5. When text is unclear, use surrounding context to make educated guesses
6. Mark uncertain words with [CONTEXT?] and completely illegible as [ILLEGIBLE]

MANDATORY: Start transcription from the absolute TOP of the page - do not skip any lines.

Return ONLY this JSON format:
{{
  "transcription": "complete text with line breaks preserved",
  "pass_type": "contextual",
  "uncertain_words": ["word1[CONTEXT?]", "word2[CONTEXT?]"],
  "illegible_sections": ["section1", "section2"],
  "total_words_found": X,
  "confidence_level": "high/medium/low"
}}"""

            response1 = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": contextual_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2500,
                temperature=0.1
            )
            
            # Parse Pass 1 result
            try:
                pass1_result = json.loads(response1.choices[0].message.content)
            except:
                # Fallback if JSON parsing fails
                pass1_result = {
                    "transcription": response1.choices[0].message.content,
                    "pass_type": "contextual",
                    "uncertain_words": [],
                    "illegible_sections": [],
                    "total_words_found": len(response1.choices[0].message.content.split()),
                    "confidence_level": "medium"
                }
            
            # PASS 2: WORD-LEVEL ANALYSIS - Focus on individual words
            word_level_prompt = f"""You are performing PASS 2 of 3 for handwritten manuscript transcription.

WORD-LEVEL ANALYSIS INSTRUCTIONS:
Previous contextual transcription: {pass1_result.get('transcription', '')}
Uncertain words from Pass 1: {pass1_result.get('uncertain_words', [])}
Illegible sections from Pass 1: {pass1_result.get('illegible_sections', [])}

1. Examine each word individually, especially those marked as uncertain
2. Use word shape, letter patterns, and common word structures
3. Apply linguistic knowledge to identify probable words
4. Cross-reference with context from Pass 1 to validate word choices
5. Mark remaining uncertain words with [WORD?] and illegible as [ILLEGIBLE]
6. Ensure the TOP 4-5 lines are still completely captured

Return ONLY this JSON format:
{{
  "transcription": "improved complete text with line breaks preserved",
  "pass_type": "word_level",
  "improvements_made": ["list of specific improvements"],
  "remaining_uncertain": ["word1[WORD?]", "word2[WORD?]"],
  "remaining_illegible": ["section1", "section2"],
  "total_words_found": X,
  "confidence_level": "high/medium/low"
}}"""

            response2 = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": word_level_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2500,
                temperature=0.1
            )
            
            # Parse Pass 2 result
            try:
                pass2_result = json.loads(response2.choices[0].message.content)
            except:
                pass2_result = {
                    "transcription": response2.choices[0].message.content,
                    "pass_type": "word_level",
                    "improvements_made": [],
                    "remaining_uncertain": [],
                    "remaining_illegible": [],
                    "total_words_found": len(response2.choices[0].message.content.split()),
                    "confidence_level": "medium"
                }
            
            # PASS 3: LETTER-LEVEL ANALYSIS - Character-by-character final pass
            letter_level_prompt = f"""You are performing PASS 3 of 3 for handwritten manuscript transcription.

LETTER-LEVEL ANALYSIS INSTRUCTIONS:
Previous word-level transcription: {pass2_result.get('transcription', '')}
Remaining uncertain words: {pass2_result.get('remaining_uncertain', [])}
Remaining illegible sections: {pass2_result.get('remaining_illegible', [])}

1. Examine each character individually, especially in uncertain sections
2. Use letter formation patterns, stroke analysis, and character recognition
3. Apply comprehensive logic guessing for unclear handwriting:
   - Analyze letter shapes and stroke patterns
   - Consider common letter combinations in the language
   - Use phonetic similarity for unclear characters
   - Apply statistical letter frequency analysis
4. Make final determinations on all uncertain sections
5. VERIFY the first 4-5 lines at the TOP are completely captured
6. Mark only truly illegible sections as [ILLEGIBLE]

Return ONLY this JSON format:
{{
  "transcription": "final complete transcription with line breaks preserved",
  "pass_type": "letter_level",
  "final_improvements": ["list of final character-level improvements"],
  "logic_guesses": ["word1: guessed based on letter shape", "word2: guessed based on context"],
  "final_illegible": ["only truly illegible sections"],
  "processing_stats": {{
    "total_words": X,
    "normal_transcription": X,
    "context_logic_transcription": X,
    "unable_to_transcribe": X
  }},
  "unclear_sections": ["final list of unclear parts"],
  "confidence_level": "high/medium/low"
}}"""

            response3 = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": letter_level_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2500,
                temperature=0.1
            )
            
            # Parse Pass 3 result and create final output
            try:
                pass3_result = json.loads(response3.choices[0].message.content)
                
                # Create comprehensive final result
                final_result = {
                    "status": "success",
                    "transcription": pass3_result.get("transcription", ""),
                    "processing_stats": pass3_result.get("processing_stats", {
                        "total_words": len(pass3_result.get("transcription", "").split()),
                        "normal_transcription": 0,
                        "context_logic_transcription": 0,
                        "unable_to_transcribe": 0
                    }),
                    "unclear_sections": pass3_result.get("unclear_sections", []),
                    "ocr_passes": 3,
                    "model_used": "gpt-4o",
                    "pass_details": {
                        "pass1_contextual": {
                            "confidence": pass1_result.get("confidence_level", "medium"),
                            "uncertain_words": len(pass1_result.get("uncertain_words", [])),
                            "illegible_sections": len(pass1_result.get("illegible_sections", []))
                        },
                        "pass2_word_level": {
                            "confidence": pass2_result.get("confidence_level", "medium"),
                            "improvements_made": len(pass2_result.get("improvements_made", [])),
                            "remaining_uncertain": len(pass2_result.get("remaining_uncertain", []))
                        },
                        "pass3_letter_level": {
                            "confidence": pass3_result.get("confidence_level", "high"),
                            "final_improvements": len(pass3_result.get("final_improvements", [])),
                            "logic_guesses": pass3_result.get("logic_guesses", [])
                        }
                    }
                }
                
            except:
                # Fallback if JSON parsing fails
                transcription_text = response3.choices[0].message.content
                word_count = len(transcription_text.split())
                
                final_result = {
                    "status": "success",
                    "transcription": transcription_text,
                    "processing_stats": {
                        "total_words": word_count,
                        "normal_transcription": word_count,
                        "context_logic_transcription": 0,
                        "unable_to_transcribe": 0
                    },
                    "unclear_sections": [],
                    "ocr_passes": 3,
                    "model_used": "gpt-4o",
                    "pass_details": {
                        "pass1_contextual": {"confidence": "medium", "uncertain_words": 0, "illegible_sections": 0},
                        "pass2_word_level": {"confidence": "medium", "improvements_made": 0, "remaining_uncertain": 0},
                        "pass3_letter_level": {"confidence": "high", "final_improvements": 0, "logic_guesses": []}
                    }
                }
            
            return json.dumps(final_result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"OCR ERROR: {error_detail}")  # Debug logging
            return json.dumps({
                "status": "error",
                "error": f"Error transcribing image: {e.__class__.__name__}: {str(e)}",
                "processing_stats": {
                    "total_words": 0,
                    "normal_transcription": 0,
                    "context_logic_transcription": 0,
                    "unable_to_transcribe": 0
                },
                "unclear_sections": [],
                "ocr_passes": 0,
                "model_used": "gpt-4o"
            })