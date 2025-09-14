import React from 'react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  const renderMarkdown = (text: string): React.ReactNode => {
    // Split by lines to handle different markdown elements
    const lines = text.split('\n');
    const elements: React.ReactNode[] = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Handle headers
      if (line.startsWith('### ')) {
        elements.push(
          <h3 key={i} className="text-lg font-semibold text-white mb-2 mt-3">
            {processInlineMarkdown(line.slice(4))}
          </h3>
        );
        continue;
      }
      if (line.startsWith('## ')) {
        elements.push(
          <h2 key={i} className="text-xl font-semibold text-white mb-2 mt-4">
            {processInlineMarkdown(line.slice(3))}
          </h2>
        );
        continue;
      }
      if (line.startsWith('# ')) {
        elements.push(
          <h1 key={i} className="text-2xl font-bold text-white mb-3 mt-4">
            {processInlineMarkdown(line.slice(2))}
          </h1>
        );
        continue;
      }
      
      // Handle unordered lists
      if (line.startsWith('- ') || line.startsWith('* ')) {
        const listItems = [];
        let j = i;
        while (j < lines.length && (lines[j].startsWith('- ') || lines[j].startsWith('* '))) {
          listItems.push(
            <li key={j} className="ml-4">
              {processInlineMarkdown(lines[j].slice(2))}
            </li>
          );
          j++;
        }
        elements.push(
          <ul key={i} className="list-disc list-inside text-gray-300 mb-2 space-y-1">
            {listItems}
          </ul>
        );
        i = j - 1; // Skip processed list items
        continue;
      }
      
      // Handle ordered lists
      if (/^\d+\.\s/.test(line)) {
        const listItems = [];
        let j = i;
        while (j < lines.length && /^\d+\.\s/.test(lines[j])) {
          listItems.push(
            <li key={j} className="ml-4">
              {processInlineMarkdown(lines[j].replace(/^\d+\.\s/, ''))}
            </li>
          );
          j++;
        }
        elements.push(
          <ol key={i} className="list-decimal list-inside text-gray-300 mb-2 space-y-1">
            {listItems}
          </ol>
        );
        i = j - 1; // Skip processed list items
        continue;
      }
      
      // Handle empty lines
      if (line.trim() === '') {
        elements.push(<br key={i} />);
        continue;
      }
      
      // Handle regular paragraphs
      elements.push(
        <p key={i} className="text-gray-300 mb-2">
          {processInlineMarkdown(line)}
        </p>
      );
    }
    
    return elements;
  };
  
  const processInlineMarkdown = (text: string): React.ReactNode => {
    const parts: React.ReactNode[] = [];
    let currentIndex = 0;
    
    // Process bold (**text**)
    text = text.replace(/\*\*(.*?)\*\*/g, (match, content, offset) => {
      const before = text.slice(currentIndex, offset);
      if (before) parts.push(before);
      parts.push(<strong key={offset} className="font-bold text-white">{content}</strong>);
      currentIndex = offset + match.length;
      return ''; // Will be handled by parts array
    });
    
    // Process italic (*text*)
    text = text.replace(/\*(.*?)\*/g, (match, content, offset) => {
      const before = text.slice(currentIndex, offset);
      if (before) parts.push(before);
      parts.push(<em key={offset} className="italic text-gray-200">{content}</em>);
      currentIndex = offset + match.length;
      return '';
    });
    
    // Process inline code (`code`)
    text = text.replace(/`([^`]+)`/g, (match, content, offset) => {
      const before = text.slice(currentIndex, offset);
      if (before) parts.push(before);
      parts.push(
        <code key={offset} className="bg-gray-800 text-green-400 px-1 rounded text-sm font-mono">
          {content}
        </code>
      );
      currentIndex = offset + match.length;
      return '';
    });
    
    // Process links [text](url)
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, linkText, url, offset) => {
      const before = text.slice(currentIndex, offset);
      if (before) parts.push(before);
      parts.push(
        <a 
          key={offset} 
          href={url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-blue-400 hover:text-blue-300 underline"
        >
          {linkText}
        </a>
      );
      currentIndex = offset + match.length;
      return '';
    });
    
    // If we processed any inline elements, return the parts array
    if (parts.length > 0) {
      // Add any remaining text
      if (currentIndex < text.length) {
        parts.push(text.slice(currentIndex));
      }
      return parts;
    }
    
    // Otherwise return the original text
    return text;
  };
  
  return (
    <div className={className}>
      {renderMarkdown(content)}
    </div>
  );
};
