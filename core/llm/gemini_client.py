"""
Gemini API client for ObsidianTools.

This module provides a client for communicating with the
Google Gemini API.
"""

import json
import re
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from secure_logging import ZeroSensitiveLogger, SafeLogContext


class GeminiClient:
    """Client for communicating with Google Gemini API."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self.logger = ZeroSensitiveLogger("gemini_client")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model_instance = genai.GenerativeModel(self.model)
    
    def process_content(self, content: str, prompt: str, max_tokens: int = 4000) -> str:
        """Process content using Gemini API."""
        try:
            # Combine prompt and content
            full_prompt = f"{prompt}\n\nContent:\n{content}"
            
            # Generate response
            response = self.model_instance.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7
                )
            )
            
            result = response.text
            
            self.logger.info("Content processed successfully with Gemini", SafeLogContext(
                operation="content_processing",
                status="success",
                metadata={
                    "model": self.model,
                    "content_length": len(content),
                    "prompt_length": len(prompt),
                    "response_length": len(result)
                }
            ))
            
            return result
            
        except Exception as e:
            self.logger.error("Failed to process content with Gemini", SafeLogContext(
                operation="content_processing",
                status="failed",
                metadata={
                    "error_type": type(e).__name__,
                    "model": self.model,
                    "content_length": len(content)
                }
            ))
            raise
    
    def generate_queries(self, content: str, max_queries: int = 5) -> List[str]:
        """Generate search queries from content."""
        try:
            prompt = f"""
            Based on the following content, generate {max_queries} search queries that would help find related information.
            Focus on key concepts, topics, and entities mentioned.
            Return only the queries, one per line, without numbering or additional text.
            
            Content:
            {content}
            """
            
            response = self.model_instance.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.5
                )
            )
            
            # Parse response into individual queries
            queries = [q.strip() for q in response.text.strip().split('\n') if q.strip()]
            
            self.logger.info("Search queries generated successfully", SafeLogContext(
                operation="query_generation",
                status="success",
                metadata={
                    "model": self.model,
                    "content_length": len(content),
                    "query_count": len(queries)
                }
            ))
            
            return queries[:max_queries]
            
        except Exception as e:
            self.logger.error("Failed to generate search queries", SafeLogContext(
                operation="query_generation",
                status="failed",
                metadata={
                    "error_type": type(e).__name__,
                    "model": self.model,
                    "content_length": len(content)
                }
            ))
            return []
    
    def analyze_document(self, content: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze document content and provide insights."""
        try:
            if analysis_type == "general":
                prompt = """
                Analyze the following document and provide:
                1. A brief summary (2-3 sentences)
                2. Key topics/themes
                3. Main entities (people, places, organizations)
                4. Suggested tags
                5. Potential connections to other topics
                
                Return the analysis in JSON format with these keys: summary, topics, entities, tags, connections
                """
            elif analysis_type == "academic":
                prompt = """
                Analyze the following academic document and provide:
                1. Research question/hypothesis
                2. Methodology
                3. Key findings
                4. Conclusions
                5. Suggested further research
                
                Return the analysis in JSON format with these keys: research_question, methodology, findings, conclusions, further_research
                """
            else:
                prompt = """
                Analyze the following document and provide insights based on the content.
                Return the analysis in JSON format.
                """
            
            full_prompt = f"{prompt}\n\nDocument:\n{content}"
            
            response = self.model_instance.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=2000,
                    temperature=0.3
                )
            )
            
            # Try to parse JSON response
            try:
                analysis = json.loads(response.text)
            except json.JSONDecodeError:
                # If JSON parsing fails, create a structured response
                analysis = {
                    "raw_response": response.text,
                    "analysis_type": analysis_type,
                    "status": "parsing_failed"
                }
            
            self.logger.info("Document analysis completed successfully", SafeLogContext(
                operation="document_analysis",
                status="success",
                metadata={
                    "model": self.model,
                    "analysis_type": analysis_type,
                    "content_length": len(content)
                }
            ))
            
            return analysis
            
        except Exception as e:
            self.logger.error("Failed to analyze document", SafeLogContext(
                operation="document_analysis",
                status="failed",
                metadata={
                    "error_type": type(e).__name__,
                    "model": self.model,
                    "analysis_type": analysis_type,
                    "content_length": len(content)
                }
            ))
            return {"error": str(e), "status": "failed"}
    
    def generate_note_content(self, content: str, note_type: str = "summary") -> str:
        """Generate Obsidian note content from document."""
        try:
            if note_type == "summary":
                prompt = """
                Create a well-structured Obsidian note from the following content.
                Include:
                - A clear title
                - Key points and insights
                - Relevant tags
                - Potential links to other notes
                
                Format it as a proper Markdown document suitable for Obsidian.
                """
            elif note_type == "detailed":
                prompt = """
                Create a comprehensive Obsidian note from the following content.
                Include:
                - Detailed analysis
                - Key concepts and definitions
                - Examples and evidence
                - Related topics and connections
                - Bibliography/references if applicable
                
                Format it as a proper Markdown document suitable for Obsidian.
                """
            else:
                prompt = """
                Create an Obsidian note from the following content.
                Format it as proper Markdown suitable for Obsidian.
                """
            
            full_prompt = f"{prompt}\n\nContent:\n{content}"
            
            response = self.model_instance.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=4000,
                    temperature=0.4
                )
            )
            
            result = response.text
            
            self.logger.info("Note content generated successfully", SafeLogContext(
                operation="note_generation",
                status="success",
                metadata={
                    "model": self.model,
                    "note_type": note_type,
                    "content_length": len(content),
                    "note_length": len(result)
                }
            ))
            
            return result
            
        except Exception as e:
            self.logger.error("Failed to generate note content", SafeLogContext(
                operation="note_generation",
                status="failed",
                metadata={
                    "error_type": type(e).__name__,
                    "model": self.model,
                    "note_type": note_type,
                    "content_length": len(content)
                }
            ))
            raise
    
    def clean_and_enhance_content(self, content: str) -> str:
        """Clean and enhance content for better processing."""
        try:
            prompt = """
            Clean and enhance the following content:
            1. Fix any obvious typos or formatting issues
            2. Improve clarity and readability
            3. Ensure proper paragraph structure
            4. Add appropriate line breaks
            5. Maintain the original meaning and tone
            
            Return the cleaned content without additional commentary.
            """
            
            full_prompt = f"{prompt}\n\nContent:\n{content}"
            
            response = self.model_instance.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=len(content) + 1000,
                    temperature=0.2
                )
            )
            
            result = response.text
            
            self.logger.info("Content cleaned and enhanced successfully", SafeLogContext(
                operation="content_enhancement",
                status="success",
                metadata={
                    "model": self.model,
                    "original_length": len(content),
                    "enhanced_length": len(result)
                }
            ))
            
            return result
            
        except Exception as e:
            self.logger.error("Failed to clean and enhance content", SafeLogContext(
                operation="content_enhancement",
                status="failed",
                metadata={
                    "error_type": type(e).__name__,
                    "model": self.model,
                    "content_length": len(content)
                }
            ))
            # Return original content if enhancement fails
            return content
    
    def extract_key_insights(self, content: str) -> List[str]:
        """Extract key insights from content."""
        try:
            prompt = """
            Extract the 5-10 most important insights from the following content.
            Focus on:
            - Key findings or conclusions
            - Important facts or data
            - Novel ideas or perspectives
            - Actionable recommendations
            
            Return each insight on a separate line, starting with a dash (-).
            """
            
            full_prompt = f"{prompt}\n\nContent:\n{content}"
            
            response = self.model_instance.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1000,
                    temperature=0.3
                )
            )
            
            # Parse insights from response
            insights = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    insights.append(line[1:].strip())
                elif line and not line.startswith('#'):
                    insights.append(line)
            
            self.logger.info("Key insights extracted successfully", SafeLogContext(
                operation="insight_extraction",
                status="success",
                metadata={
                    "model": self.model,
                    "content_length": len(content),
                    "insight_count": len(insights)
                }
            ))
            
            return insights
            
        except Exception as e:
            self.logger.error("Failed to extract key insights", SafeLogContext(
                operation="insight_extraction",
                status="failed",
                metadata={
                    "error_type": type(e).__name__,
                    "model": self.model,
                    "content_length": len(content)
                }
            ))
            return []
    
    def generate_content(self, prompt: str, max_tokens: int = 4000) -> Any:
        """
        Generate content using Gemini API with a given prompt.
        This method is designed to be compatible with the ingest engine.
        
        Args:
            prompt: The prompt to send to Gemini
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Response object with text attribute containing the generated content
        """
        try:
            response = self.model_instance.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7
                )
            )
            
            self.logger.info("Content generated successfully with Gemini", SafeLogContext(
                operation="content_generation",
                status="success",
                metadata={
                    "model": self.model,
                    "prompt_length": len(prompt),
                    "response_length": len(response.text) if response.text else 0
                }
            ))
            
            return response
            
        except Exception as e:
            self.logger.error("Failed to generate content with Gemini", SafeLogContext(
                operation="content_generation",
                status="failed",
                metadata={
                    "error_type": type(e).__name__,
                    "model": self.model,
                    "prompt_length": len(prompt)
                }
            ))
            raise
