import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';

const Chat = ({ sessionId, docDescription, suggestedQuestions, selectedQuestion, onQuestionSelected }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

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

  return (
    <div className="flex h-[600px] flex-col rounded-lg border border-border bg-card/50 transition-colors duration-300">
      <div className="flex-1 overflow-y-auto p-4">
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
          messages.map((message, index) => (
            <div 
              key={index} 
              className={`mb-4 flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
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
                <span className="mt-1 text-lg">
                  {message.sender === 'user' 
                    ? '👤' 
                    : message.isError 
                      ? '⚠️' 
                      : '🤖'}
                </span>
                <div className="text-sm">{message.text}</div>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="mb-4 flex justify-start">
            <div className="flex items-start gap-2 max-w-[80%] rounded-lg px-4 py-3 bg-secondary text-secondary-foreground shadow-sm">
              <span className="mt-1 text-lg">🤖</span>
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
      
      <form onSubmit={handleSubmit} className="border-t border-border p-4 transition-colors duration-300">
        <div className="flex space-x-2">
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
            className="transition-colors duration-300 flex items-center gap-2"
          >
            <span>Send</span>
            <span role="img" aria-label="send">📤</span>
          </Button>
        </div>
      </form>
    </div>
  );
};

export default Chat; 