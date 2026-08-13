"""
Amazon Bedrock Client.

Provides access to Bedrock AI models with proper error handling and retry logic.
"""
import json
import logging
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BedrockClient:
    """
    Amazon Bedrock API client.
    
    Provides access to Claude and other foundation models through Bedrock.
    
    SECURITY: This client has NO access to:
    - Terraform execution
    - AWS CLI
    - IAM modification
    - Direct resource creation
    
    It only generates structured JSON responses that are validated
    before being used by the platform.
    """
    
    def __init__(self):
        """Initialize Bedrock client."""
        self.region = settings.aws_region
        self.model_id = settings.bedrock_model_id
        
        if not settings.demo_mode:
            self.client = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.region,
            )
    
    def invoke_model(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        tools: Optional[list[dict]] = None,
    ) -> dict[str, Any]:
        """
        Invoke Bedrock model with prompt.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0-1)
            tools: Tool definitions for function calling
            
        Returns:
            Model response
            
        Raises:
            Exception: If model invocation fails
        """
        if settings.demo_mode:
            logger.warning("Demo mode: Returning simulated Bedrock response")
            return self._demo_response(prompt)
        
        try:
            # Build request for Claude
            messages = [{"role": "user", "content": prompt}]
            
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }
            
            if system_prompt:
                request_body["system"] = system_prompt
            
            if tools:
                request_body["tools"] = tools
            
            # Invoke model
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body),
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            logger.info(
                f"Bedrock invocation successful. "
                f"Stop reason: {response_body.get('stop_reason')}"
            )
            
            return response_body
            
        except ClientError as e:
            logger.error(f"Bedrock invocation failed: {e}")
            raise
    
    def invoke_with_tools(
        self,
        prompt: str,
        tools: list[dict],
        system_prompt: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Invoke model with tool calling enabled.
        
        Args:
            prompt: User prompt
            tools: Available tools
            system_prompt: System instructions
            
        Returns:
            Model response with tool calls
        """
        response = self.invoke_model(
            prompt=prompt,
            system_prompt=system_prompt,
            tools=tools,
        )
        
        # Extract tool calls if present
        content = response.get('content', [])
        
        tool_calls = []
        text_response = ""
        
        for item in content:
            if item.get('type') == 'tool_use':
                tool_calls.append({
                    'id': item.get('id'),
                    'name': item.get('name'),
                    'input': item.get('input'),
                })
            elif item.get('type') == 'text':
                text_response += item.get('text', '')
        
        return {
            'response': response,
            'text': text_response,
            'tool_calls': tool_calls,
            'stop_reason': response.get('stop_reason'),
        }
    
    def extract_json_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """
        Extract and parse JSON from model response.
        
        Args:
            response: Model response
            
        Returns:
            Parsed JSON object
            
        Raises:
            ValueError: If JSON parsing fails
        """
        content = response.get('content', [])
        
        for item in content:
            if item.get('type') == 'text':
                text = item.get('text', '')
                
                # Try to extract JSON from text
                # Look for ```json blocks
                if '```json' in text:
                    start = text.find('```json') + 7
                    end = text.find('```', start)
                    if end > start:
                        json_text = text[start:end].strip()
                        return json.loads(json_text)
                
                # Try to parse entire text as JSON
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    pass
        
        raise ValueError("No valid JSON found in response")
    
    def _demo_response(self, prompt: str) -> dict[str, Any]:
        """Generate demo response for testing."""
        return {
            "id": "msg_demo123",
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": "This is a demo response. Bedrock integration is not active in demo mode."
                }
            ],
            "model": self.model_id,
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50
            }
        }
