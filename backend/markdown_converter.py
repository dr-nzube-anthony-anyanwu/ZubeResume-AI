"""
Markdown to Formatted Text Converter
Converts markdown-style text from multi-agent output to properly formatted content for PDF/DOCX generation
"""

import re
import logging
from typing import List, Tuple, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FormattedText:
    """Represents a piece of text with formatting information"""
    text: str
    is_bold: bool = False
    is_italic: bool = False
    is_header: bool = False
    header_level: int = 0
    is_bullet: bool = False
    indent_level: int = 0

class MarkdownConverter:
    """Converts markdown-style text to structured formatted content"""
    
    def __init__(self):
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.bold_pattern = re.compile(r'\*\*(.+?)\*\*')
        self.italic_pattern = re.compile(r'\*(?!\*)(.+?)\*(?!\*)')
        self.bullet_pattern = re.compile(r'^[\s]*[•\*\+\-]\s+(.+)$', re.MULTILINE)
        self.numbered_pattern = re.compile(r'^[\s]*\d+\.\s+(.+)$', re.MULTILINE)
        
    def convert_to_structured_content(self, markdown_text: str) -> List[FormattedText]:
        """
        Convert markdown text to structured content with formatting information
        
        Args:
            markdown_text (str): Text with markdown formatting
            
        Returns:
            List[FormattedText]: List of formatted text elements
        """
        try:
            content = []
            lines = markdown_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for headers (## or ###)
                header_match = self.header_pattern.match(line)
                if header_match:
                    header_level = len(header_match.group(1))
                    header_text = header_match.group(2).strip()
                    content.append(FormattedText(
                        text=header_text,
                        is_header=True,
                        header_level=header_level
                    ))
                    continue
                
                # Check for bullet points
                bullet_match = self.bullet_pattern.match(line)
                if bullet_match:
                    bullet_text = bullet_match.group(1).strip()
                    # Count leading spaces for indent level
                    indent_level = (len(line) - len(line.lstrip())) // 2
                    
                    # Process inline formatting in bullet text
                    formatted_bullet = self._process_inline_formatting(bullet_text)
                    for item in formatted_bullet:
                        item.is_bullet = True
                        item.indent_level = indent_level
                        content.append(item)
                    continue
                
                # Check for numbered lists
                numbered_match = self.numbered_pattern.match(line)
                if numbered_match:
                    numbered_text = numbered_match.group(1).strip()
                    indent_level = (len(line) - len(line.lstrip())) // 2
                    
                    formatted_numbered = self._process_inline_formatting(numbered_text)
                    for item in formatted_numbered:
                        item.is_bullet = True  # Treat as bullet for formatting
                        item.indent_level = indent_level
                        content.append(item)
                    continue
                
                # Regular paragraph text
                formatted_line = self._process_inline_formatting(line)
                content.extend(formatted_line)
            
            return content
            
        except Exception as e:
            logger.error(f"Error converting markdown to structured content: {e}")
            return [FormattedText(text=markdown_text)]
    
    def _process_inline_formatting(self, text: str) -> List[FormattedText]:
        """Process inline formatting like bold and italic within a line"""
        result = []
        
        # Split text by formatting patterns while preserving the formatting info
        parts = self._split_with_formatting(text)
        
        for part in parts:
            if part.strip():
                result.append(part)
        
        return result if result else [FormattedText(text=text)]
    
    def _split_with_formatting(self, text: str) -> List[FormattedText]:
        """Split text and identify formatting"""
        result = []
        current_pos = 0
        
        # Find all bold patterns first
        for match in self.bold_pattern.finditer(text):
            # Add text before bold
            if match.start() > current_pos:
                before_text = text[current_pos:match.start()]
                if before_text.strip():
                    result.append(FormattedText(text=before_text))
            
            # Add bold text
            bold_text = match.group(1)
            result.append(FormattedText(text=bold_text, is_bold=True))
            current_pos = match.end()
        
        # Add remaining text
        if current_pos < len(text):
            remaining_text = text[current_pos:]
            if remaining_text.strip():
                result.append(FormattedText(text=remaining_text))
        
        # If no formatting found, return original text
        if not result:
            result.append(FormattedText(text=text))
        
        return result
    
    def convert_to_plain_formatted_text(self, markdown_text: str) -> str:
        """
        Convert markdown to clean text with proper spacing and structure
        but without markup characters
        
        Args:
            markdown_text (str): Text with markdown formatting
            
        Returns:
            str: Clean formatted text
        """
        try:
            # Remove the "Here is the final..." prefix if present
            if "Here is the final, document-ready content" in markdown_text:
                parts = markdown_text.split("Here is the final, document-ready content that will generate perfect files:")
                if len(parts) > 1:
                    markdown_text = parts[1].strip()
            
            # Convert structured content to clean text
            structured_content = self.convert_to_structured_content(markdown_text)
            
            result_lines = []
            for item in structured_content:
                if item.is_header:
                    # Add proper spacing around headers
                    if result_lines:
                        result_lines.append("")  # Blank line before header
                    result_lines.append(item.text.upper())
                    result_lines.append("")  # Blank line after header
                elif item.is_bullet:
                    # Add bullet points with proper indentation
                    indent = "  " * item.indent_level
                    result_lines.append(f"{indent}• {item.text}")
                else:
                    # Regular text
                    if item.text.strip():
                        result_lines.append(item.text)
            
            return "\n".join(result_lines)
            
        except Exception as e:
            logger.error(f"Error converting markdown to plain text: {e}")
            return markdown_text