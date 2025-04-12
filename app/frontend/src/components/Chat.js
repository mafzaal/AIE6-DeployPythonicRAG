import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight, oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useTheme } from './ui/theme-provider';
import { Button } from './ui/button';
import { Input } from './ui/input';

const Chat = ({ sessionId, docDescription, suggestedQuestions, selectedQuestion, onQuestionSelected }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const { theme } = useTheme();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle when a suggested question is selected
  useEffect(() => {
    if (selectedQuestion) {
      setInput(selectedQuestion);
      onQuestionSelected(); // Clear the selected question after setting it
    }
  }, [selectedQuestion, onQuestionSelected]);

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    const userMessage = input;
    setInput('');
    
    // Add user message to chat
    setMessages(prevMessages => [
      ...prevMessages, 
      { text: userMessage, sender: 'user' }
    ]);
    
    setIsLoading(true);
    
    try {
      const response = await axios.post('/query', {
        session_id: sessionId,
        query: userMessage
      });
      
      // Add AI response to chat
      setMessages(prevMessages => [
        ...prevMessages, 
        { text: response.data.response, sender: 'ai' }
      ]);
    } catch (error) {
      console.error('Error getting response:', error);
      
      // Add error message to chat
      setMessages(prevMessages => [
        ...prevMessages, 
        { 
          text: 'Sorry, there was an error processing your request.', 
          sender: 'ai', 
          isError: true 
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Component for rendering markdown with custom styles
  const MarkdownContent = ({ content }) => (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ node, ...props }) => <p className="mb-2" {...props} />,
        h1: ({ node, ...props }) => <h1 className="text-lg font-bold mb-2 mt-3" {...props} />,
        h2: ({ node, ...props }) => <h2 className="text-md font-bold mb-2 mt-3" {...props} />,
        h3: ({ node, ...props }) => <h3 className="text-sm font-bold mb-1 mt-2" {...props} />,
        ul: ({ node, ...props }) => <ul className="list-disc pl-4 mb-2" {...props} />,
        ol: ({ node, ...props }) => <ol className="list-decimal pl-4 mb-2" {...props} />,
        li: ({ node, ...props }) => <li className="mb-1" {...props} />,
        a: ({ node, ...props }) => <a className="text-primary underline" target="_blank" rel="noopener noreferrer" {...props} />,
        code: ({ node, inline, className, children, ...props }) => {
          const match = /language-(\w+)/.exec(className || '');
          const language = match ? match[1] : '';
          
          return !inline ? (
            <div className="rounded-md overflow-hidden my-2">
              <div className="bg-secondary/70 px-3 py-1 text-xs flex justify-between items-center border-b border-border">
                <span>{language || 'code'}</span>
                <button 
                  onClick={() => {
                    navigator.clipboard.writeText(String(children).replace(/\n$/, ''));
                  }}
                  className="px-2 py-0.5 text-xs hover:bg-secondary rounded"
                  title="Copy code"
                >
                  📋 Copy
                </button>
              </div>
              <SyntaxHighlighter
                style={theme === 'dark' ? oneDark : oneLight}
                language={language || 'text'}
                PreTag="div"
                customStyle={{
                  margin: 0,
                  padding: '0.75rem',
                  fontSize: '0.8rem',
                  borderRadius: '0 0 0.375rem 0.375rem',
                }}
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            </div>
          ) : (
            <code className="px-1 py-0.5 bg-secondary rounded text-xs font-mono" {...props}>
              {children}
            </code>
          );
        },
        pre: ({ node, ...props }) => <div className="my-2" {...props} />,
        blockquote: ({ node, ...props }) => <blockquote className="border-l-2 border-primary/20 pl-2 italic my-2" {...props} />,
        table: ({ node, ...props }) => <div className="overflow-x-auto my-2"><table className="border-collapse w-full" {...props} /></div>,
        thead: ({ node, ...props }) => <thead className="bg-secondary/30" {...props} />,
        tbody: ({ node, ...props }) => <tbody {...props} />,
        tr: ({ node, ...props }) => <tr className="border-b border-border" {...props} />,
        th: ({ node, ...props }) => <th className="p-1.5 text-left text-xs font-medium" {...props} />,
        td: ({ node, ...props }) => <td className="p-1.5 text-xs" {...props} />,
        img: ({ node, ...props }) => <img className="max-w-full h-auto rounded my-2" {...props} />
      }}
    >
      {content}
    </ReactMarkdown>
  );

  return (
    <div className="flex flex-col rounded-lg border border-border bg-card/50 transition-colors duration-300 h-[600px]">
      <div className="flex-1 overflow-y-auto p-4 w-full">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="mb-4 rounded-full bg-primary/10 p-6 transition-all duration-300">
              <span role="img" aria-label="chat" className="text-4xl">💬</span>
            </div>
            <h3 className="mb-2 text-xl font-semibold">Welcome to the RAG Chat!</h3>
            <p className="text-sm text-muted-foreground max-w-md">
              Ask questions about your document or click one of the suggested questions above.
              I'm here to help you understand the content! ✨
            </p>
          </div>
        ) : (
          <div className="w-full">
            {messages.map((message, index) => (
              <div 
                key={index} 
                className={`mb-4 flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} w-full`}
              >
                <div 
                  className={`
                    flex items-start gap-2 max-w-[80%] rounded-lg px-4 py-3 shadow-sm
                    ${message.sender === 'user' 
                      ? 'bg-primary text-primary-foreground' 
                      : message.isError 
                        ? 'bg-destructive text-destructive-foreground' 
                        : 'bg-secondary text-secondary-foreground'
                    }
                    transition-all duration-200
                  `}
                >
                  <span className="mt-1 text-lg flex-shrink-0">
                    {message.sender === 'user' 
                      ? '👤' 
                      : message.isError 
                        ? '⚠️' 
                        : '🤖'}
                  </span>
                  <div className={`text-sm ${message.sender === 'ai' ? 'markdown-content' : ''} overflow-hidden`}>
                    {message.sender === 'user' ? (
                      message.text
                    ) : (
                      <MarkdownContent content={message.text} />
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        {isLoading && (
          <div className="mb-4 flex justify-start w-full">
            <div className="flex items-start gap-2 max-w-[80%] rounded-lg px-4 py-3 bg-secondary text-secondary-foreground shadow-sm">
              <span className="mt-1 text-lg flex-shrink-0">🤖</span>
              <div className="flex items-center space-x-2">
                <div className="h-2 w-2 animate-bounce rounded-full bg-primary"></div>
                <div className="h-2 w-2 animate-bounce rounded-full bg-primary" style={{ animationDelay: '0.2s' }}></div>
                <div className="h-2 w-2 animate-bounce rounded-full bg-primary" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSubmit} className="border-t border-border p-4 transition-colors duration-300 w-full">
        <div className="flex space-x-2 w-full">
          <Input
            id="chat-input"
            ref={inputRef}
            type="text"
            value={input}
            onChange={handleInputChange}
            placeholder="Ask a question about your document... 🔍"
            disabled={isLoading}
            className="flex-1 transition-colors duration-300"
          />
          <Button 
            type="submit" 
            disabled={isLoading || !input.trim()}
            className="transition-colors duration-300 flex items-center gap-2 flex-shrink-0"
          >
            <span>Send</span>
            <span role="img" aria-label="send" className="flex-shrink-0">📤</span>
          </Button>
        </div>
      </form>
    </div>
  );
};

export default Chat; 