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
    <div className="flex h-[600px] flex-col rounded-lg">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="mb-4 rounded-full bg-primary/10 p-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
            </div>
            <h3 className="mb-1 text-lg font-semibold">Welcome to the RAG Chat!</h3>
            <p className="text-sm text-muted-foreground">
              Ask questions about the document you uploaded or click one of the suggested questions above.
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
                  max-w-[80%] rounded-lg px-4 py-2 
                  ${message.sender === 'user' 
                    ? 'bg-primary text-primary-foreground' 
                    : message.isError 
                      ? 'bg-destructive text-destructive-foreground' 
                      : 'bg-secondary text-secondary-foreground'
                  }
                `}
              >
                <div className="text-sm">{message.text}</div>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="mb-4 flex justify-start">
            <div className="max-w-[80%] rounded-lg bg-secondary px-4 py-2 text-secondary-foreground">
              <div className="flex space-x-2">
                <div className="h-2 w-2 animate-bounce rounded-full bg-primary"></div>
                <div className="h-2 w-2 animate-bounce rounded-full bg-primary" style={{ animationDelay: '0.2s' }}></div>
                <div className="h-2 w-2 animate-bounce rounded-full bg-primary" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSubmit} className="border-t border-border p-4">
        <div className="flex space-x-2">
          <Input
            id="chat-input"
            ref={inputRef}
            type="text"
            value={input}
            onChange={handleInputChange}
            placeholder="Ask a question about your document..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button 
            type="submit" 
            disabled={isLoading || !input.trim()}
          >
            Send
          </Button>
        </div>
      </form>
    </div>
  );
};

export default Chat; 