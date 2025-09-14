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
    
    // Find all patterns and their positions
    const patterns = [
      { regex: /\[([^\]]+)\]\(([^)]+)\)/g, type: 'markdown-link' },
      { regex: /https?:\/\/[^\s<>"{}|\\^`[\]]+/g, type: 'url' },
      { regex: /\*\*(.*?)\*\*/g, type: 'bold' },
      { regex: /\*(.*?)\*/g, type: 'italic' },
      { regex: /`([^`]+)`/g, type: 'code' }
    ];
    
    const matches: Array<{
      start: number;
      end: number;
      match: RegExpMatchArray;
      type: string;
    }> = [];
    
    // Find all matches
    patterns.forEach(({ regex, type }) => {
      let match;
      const regexCopy = new RegExp(regex.source, regex.flags);
      while ((match = regexCopy.exec(text)) !== null) {
        matches.push({
          start: match.index!,
          end: match.index! + match[0].length,
          match,
          type
        });
      }
    });
    
    // Sort matches by start position
    matches.sort((a, b) => a.start - b.start);
    
    // Remove overlapping matches (keep the first one)
    const filteredMatches = [];
    let lastEnd = -1;
    for (const match of matches) {
      if (match.start >= lastEnd) {
        filteredMatches.push(match);
        lastEnd = match.end;
      }
    }
    
    // Build parts
    let currentIndex = 0;
    let keyCounter = 0;
    
    filteredMatches.forEach(({ start, end, match, type }) => {
      // Add text before this match
      if (start > currentIndex) {
        parts.push(text.slice(currentIndex, start));
      }
      
      // Add the formatted element
      switch (type) {
        case 'markdown-link':
          parts.push(
            <a 
              key={keyCounter++} 
              href={match[2]} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 underline"
            >
              {match[1]}
            </a>
          );
          break;
        case 'url':
          parts.push(
            <a 
              key={keyCounter++} 
              href={match[0]} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 underline"
            >
              {match[0]}
            </a>
          );
          break;
        case 'bold':
          parts.push(<strong key={keyCounter++} className="font-bold text-white">{match[1]}</strong>);
          break;
        case 'italic':
          parts.push(<em key={keyCounter++} className="italic text-gray-200">{match[1]}</em>);
          break;
        case 'code':
          parts.push(
            <code key={keyCounter++} className="bg-gray-800 text-green-400 px-1 rounded text-sm font-mono">
              {match[1]}
            </code>
          );
          break;
      }
      
      currentIndex = end;
    });
    
    // Add remaining text
    if (currentIndex < text.length) {
      parts.push(text.slice(currentIndex));
    }
    
    return parts.length > 0 ? parts : text;
  };
  
  return (
    <div className={className}>
      {renderMarkdown(content)}
    </div>
  );
};
