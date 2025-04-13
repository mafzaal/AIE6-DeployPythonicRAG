import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight, oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useTheme } from './ui/theme-provider';
import { Button } from './ui/button';
import { Input } from './ui/input';
import Quiz from './Quiz';

// Helper function to parse thinking and answer sections
const parseThinkingAnswer = (text) => {
  // Try to match the think tag, even if it's incomplete
  const thinkingRegex = /<think>([\s\S]*?)(?:<\/think>|$)/i;
  const thinkingMatch = thinkingRegex.exec(text);
  
  // If thinking section is found (even partially)
  if (thinkingMatch) {
    // Get the text after the thinking section, including if </think> is not yet complete
    const thinkingEndIndex = thinkingMatch.index + thinkingMatch[0].length;
    const restOfText = text.substring(thinkingEndIndex).trim();
    
    // Check for explicit answer tag, even if incomplete
    const answerRegex = /<answer>([\s\S]*?)(?:<\/answer>|$)/i;
    const answerMatch = answerRegex.exec(restOfText);
    
    if (answerMatch) {
      // Both thinking and answer tags found
      return {
        thinking: thinkingMatch[1].trim(),
        answer: answerMatch[1].trim(),
        hasFormatting: true
      };
    } else {
      // Only thinking tag found, treat the rest as the answer
      return {
        thinking: thinkingMatch[1].trim(),
        answer: restOfText,
        hasFormatting: true
      };
    }
  }
  
  // Check if there's just an answer tag, even if incomplete
  const answerRegex = /<answer>([\s\S]*?)(?:<\/answer>|$)/i;
  const answerMatch = answerRegex.exec(text);
  if (answerMatch) {
    return {
      thinking: "",
      answer: answerMatch[1].trim(),
      hasFormatting: true
    };
  }
  
  // If no formatting is found, return the original text as the answer
  return {
    thinking: '',
    answer: text,
    hasFormatting: false
  };
};

const Chat = ({ sessionId, docDescription, suggestedQuestions, selectedQuestion, onQuestionSelected }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [userQuestionCount, setUserQuestionCount] = useState(0);
  const [showQuizPrompt, setShowQuizPrompt] = useState(false);
  const [showQuiz, setShowQuiz] = useState(false);
  const [quizQuestions, setQuizQuestions] = useState([]);
  const [quizLoading, setQuizLoading] = useState(false);
  const [quizResults, setQuizResults] = useState(null);
  const [expandedThinking, setExpandedThinking] = useState({});
  const [activeEventSource, setActiveEventSource] = useState(null);
  
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

  const toggleThinking = (messageId) => {
    setExpandedThinking(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    const userMessage = input;
    setInput('');
    
    // Add user message to chat - ensure unique ID
    const userMessageId = Date.now();
    console.log('Adding user message:', userMessageId, userMessage);
    
    setMessages(prevMessages => [
      ...prevMessages, 
      { text: userMessage, sender: 'user', id: userMessageId }
    ]);
    
    // Check if user is explicitly asking for a quiz
    const quizRequestPatterns = [
      /quiz me/i,
      /take (a|the) quiz/i,
      /start (a|the) quiz/i,
      /test (my )?knowledge/i,
      /give me (a|the) quiz/i,
      /create (a|the) quiz/i,
      /can (i|you) (do|have|take) (a|the) quiz/i
    ];
    
    const isQuizRequest = quizRequestPatterns.some(pattern => pattern.test(userMessage));
    
    if (isQuizRequest && !showQuiz && !quizLoading) {
      // Add user message acknowledging quiz request
      const messageId = Date.now() + 1;
      setMessages(prevMessages => [
        ...prevMessages, 
        { 
          text: "I'd be happy to create a quiz based on this document! Generating questions now...", 
          sender: 'ai',
          id: messageId,
          hasFormatting: false
        }
      ]);
      
      // Start quiz generation
      handleQuizGeneration();
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Create placeholder message for streaming content with a guaranteed unique ID
      const messageId = userMessageId + 100;
      console.log('Creating AI message placeholder:', messageId);
      
      setMessages(prevMessages => [
        ...prevMessages, 
        { 
          text: "", 
          sender: 'ai',
          id: messageId,
          thinking: "",
          answer: "",
          hasFormatting: false,
          isStreaming: true
        }
      ]);
      
      // Close any existing EventSource before creating a new one
      if (activeEventSource) {
        console.log('Closing existing EventSource');
        activeEventSource.close();
      }
      
      // Create EventSource for streaming connection
      const eventSource = new EventSource(`/stream?session_id=${sessionId}&query=${encodeURIComponent(userMessage)}`, { 
        withCredentials: true 
      });
      
      // Store the event source in state
      setActiveEventSource(eventSource);
      
      let streamedText = "";
      
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        streamedText += data.chunk;
        
        // Parse current content
        const parsedResponse = parseThinkingAnswer(streamedText);
        
        console.log('Updating message with chunk, ID:', messageId);
        
        // Update message with streamed content
        setMessages(prevMessages => prevMessages.map(msg => 
          msg.id === messageId
            ? { 
                ...msg, 
                text: streamedText,
                thinking: parsedResponse.thinking,
                answer: parsedResponse.answer,
                hasFormatting: parsedResponse.hasFormatting,
                isStreaming: true,
                sender: 'ai'
              }
            : msg
        ));
      };
      
      // Listen for stream completion event
      eventSource.addEventListener('complete', (event) => {
        console.log('Stream complete, closing EventSource');
        eventSource.close();
        setActiveEventSource(null);
        
        const parsedResponse = parseThinkingAnswer(streamedText);
        
        // Update message with final streamed content
        setMessages(prevMessages => 
          prevMessages.map(msg => 
            msg.id === messageId
              ? { 
                  ...msg, 
                  text: streamedText,
                  thinking: parsedResponse.thinking,
                  answer: parsedResponse.answer,
                  hasFormatting: parsedResponse.hasFormatting,
                  isStreaming: false,
                  sender: 'ai'
                }
              : msg
          )
        );
        
        // Increment question count after successful response
        const newCount = userQuestionCount + 1;
        setUserQuestionCount(newCount);
        
        // Check if we should show quiz prompt (after 3+ questions and not already shown)
        if (newCount >= 3 && !showQuizPrompt && !showQuiz && !quizResults) {
          setShowQuizPrompt(true);
        }
        
        setIsLoading(false);
      });
      
      eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        eventSource.close();
        setActiveEventSource(null);
        
        // If we got a partial response, keep it
        if (streamedText) {
          const parsedResponse = parseThinkingAnswer(streamedText);
          
          // Update message with final streamed content
          setMessages(prevMessages => 
            prevMessages.map(msg => 
              msg.id === messageId
                ? { 
                    ...msg, 
                    text: streamedText,
                    thinking: parsedResponse.thinking,
                    answer: parsedResponse.answer,
                    hasFormatting: parsedResponse.hasFormatting,
                    isStreaming: false,
                    sender: 'ai'
                  }
                : msg
            )
          );
        } else {
          // If we got no response, show error
          setMessages(prevMessages => [
            ...prevMessages.filter(msg => msg.id !== messageId), // Remove placeholder
            { 
              text: 'Sorry, there was an error processing your request.', 
              sender: 'ai', 
              isError: true,
              id: Date.now() 
            }
          ]);
        }
        
        setIsLoading(false);
      };
      
      eventSource.onopen = () => {
        console.log('EventSource connected');
      };
      
    } catch (error) {
      console.error('Error getting response:', error);
      
      // Add error message to chat
      setMessages(prevMessages => [
        ...prevMessages, 
        { 
          text: 'Sorry, there was an error processing your request.', 
          sender: 'ai', 
          isError: true,
          id: Date.now() 
        }
      ]);
      
      setIsLoading(false);
    }
  };

  const handleQuizGeneration = async () => {
    setQuizLoading(true);
    setShowQuizPrompt(false);
    
    try {
      const response = await axios.post('/generate-quiz', {
        session_id: sessionId,
        num_questions: 5
      });
      
      setQuizQuestions(response.data.questions);
      setShowQuiz(true);
    } catch (error) {
      console.error('Error generating quiz:', error);
      
      // Add error message to chat
      setMessages(prevMessages => [
        ...prevMessages, 
        { 
          text: 'Sorry, there was an error generating the quiz. Please try again later.', 
          sender: 'ai', 
          isError: true,
          id: Date.now(),
          hasFormatting: false
        }
      ]);
    } finally {
      setQuizLoading(false);
    }
  };

  const handleAcceptQuiz = async () => {
    setShowQuizPrompt(false);
    setQuizLoading(true);
    
    // Add message about starting quiz generation
    setMessages(prevMessages => [
      ...prevMessages,
      { 
        text: "I'll create a knowledge quiz based on this document. Please wait a moment...", 
        sender: 'ai',
        id: Date.now(),
        hasFormatting: false 
      }
    ]);
    
    handleQuizGeneration();
  };

  const handleDeclineQuiz = () => {
    setShowQuizPrompt(false);
    
    // Add message acknowledging user's choice
    setMessages(prevMessages => [
      ...prevMessages,
      { 
        text: "No problem! Feel free to continue asking questions about the document.", 
        sender: 'ai',
        id: Date.now(),
        hasFormatting: false
      }
    ]);
  };

  const handleQuizComplete = (results) => {
    setQuizResults(results);
    setShowQuiz(false);
    
    // Add quiz results to chat
    const resultMessage = `
## Quiz Results 📊

You answered **${results.correctAnswers}** out of **${results.totalQuestions}** questions correctly (**${Math.round(results.score)}%**).

${results.score >= 80 
  ? "Great job! You have a solid understanding of the material." 
  : results.score >= 60 
    ? "Good work! You're on the right track." 
    : "Keep learning! Review the document to improve your understanding."}
`;
    
    setMessages(prevMessages => [
      ...prevMessages,
      { 
        text: resultMessage, 
        sender: 'ai',
        id: Date.now(),
        hasFormatting: false
      }
    ]);
  };

  const handleCloseQuiz = () => {
    setShowQuiz(false);
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

  // If quiz is active, show the quiz component
  if (showQuiz) {
    return <Quiz questions={quizQuestions} onComplete={handleQuizComplete} onClose={handleCloseQuiz} />;
  }

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
                key={message.id || index} 
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
                    ) : message.isStreaming ? (
                      // Unified streaming display
                      <div>
                        {/* Show streaming content differently depending on whether formatting is detected */}
                        {message.hasFormatting ? (
                          <>
                            {message.thinking && (
                              <div className="mb-2">
                                <div 
                                  className="flex items-center gap-1 mb-1 cursor-pointer text-xs opacity-80"
                                  onClick={() => toggleThinking(message.id)}
                                >
                                  <span className="text-xs">
                                    {expandedThinking[message.id] ? '▼' : '►'}
                                  </span>
                                  <span className="font-medium">
                                    {expandedThinking[message.id] ? 'Hide Thinking Process' : 'Show Thinking Process'}
                                  </span>
                                </div>
                                
                                {expandedThinking[message.id] && (
                                  <div className="p-2 bg-muted/40 rounded-md border border-primary/10 text-xs leading-relaxed mb-2">
                                    <MarkdownContent content={message.thinking} />
                                  </div>
                                )}
                              </div>
                            )}
                            
                            <div>
                              <MarkdownContent content={message.answer} />
                              <span className="inline-block w-1.5 h-4 ml-1 bg-primary animate-pulse rounded-sm" />
                            </div>
                          </>
                        ) : (
                          <>
                            <MarkdownContent content={message.text} />
                            <span className="inline-block w-1.5 h-4 ml-1 bg-primary animate-pulse rounded-sm" />
                          </>
                        )}
                      </div>
                    ) : message.hasFormatting ? (
                      // Non-streaming formatted display
                      <div>
                        {message.thinking && (
                          <div className="mb-2">
                            <div 
                              className="flex items-center gap-1 mb-1 cursor-pointer text-xs opacity-80"
                              onClick={() => toggleThinking(message.id)}
                            >
                              <span className="text-xs">
                                {expandedThinking[message.id] ? '▼' : '►'}
                              </span>
                              <span className="font-medium">
                                {expandedThinking[message.id] ? 'Hide Thinking Process' : 'Show Thinking Process'}
                              </span>
                            </div>
                            
                            {expandedThinking[message.id] && (
                              <div className="p-2 bg-muted/40 rounded-md border border-primary/10 text-xs leading-relaxed mb-2">
                                <MarkdownContent content={message.thinking} />
                              </div>
                            )}
                          </div>
                        )}
                        
                        <div>
                          <MarkdownContent content={message.answer} />
                        </div>
                      </div>
                    ) : (
                      // Non-streaming, non-formatted display
                      <div>
                        <MarkdownContent content={message.text} />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Quiz prompt message */}
            {showQuizPrompt && !isLoading && (
              <div className="mb-4 flex justify-start w-full">
                <div className="flex flex-col items-start gap-2 max-w-[80%] rounded-lg px-4 py-3 bg-primary/10 text-foreground shadow-sm border border-primary/20">
                  <div className="flex items-start gap-2">
                    <span className="mt-1 text-lg flex-shrink-0">🧠</span>
                    <div className="text-sm">
                      <p className="mb-3">
                        I notice you've asked several questions about this document. Would you like to test your knowledge with a quick quiz?
                      </p>
                      <div className="flex flex-wrap gap-2">
                        <Button 
                          onClick={handleAcceptQuiz} 
                          size="sm" 
                          className="flex items-center gap-1"
                        >
                          <span role="img" aria-label="quiz" className="text-sm">📝</span>
                          Take a quiz
                        </Button>
                        <Button 
                          onClick={handleDeclineQuiz} 
                          variant="outline" 
                          size="sm"
                        >
                          No thanks
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
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
        {quizLoading && (
          <div className="mb-4 flex justify-start w-full">
            <div className="flex items-start gap-2 max-w-[80%] rounded-lg px-4 py-3 bg-secondary text-secondary-foreground shadow-sm">
              <span className="mt-1 text-lg flex-shrink-0">📝</span>
              <div className="flex flex-col gap-2">
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 animate-bounce rounded-full bg-primary"></div>
                  <div className="h-2 w-2 animate-bounce rounded-full bg-primary" style={{ animationDelay: '0.2s' }}></div>
                  <div className="h-2 w-2 animate-bounce rounded-full bg-primary" style={{ animationDelay: '0.4s' }}></div>
                </div>
                <span className="text-xs">Generating quiz questions...</span>
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
            disabled={isLoading || quizLoading}
            className="flex-1 transition-colors duration-300"
          />
          <Button 
            type="submit" 
            disabled={isLoading || quizLoading || !input.trim()}
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