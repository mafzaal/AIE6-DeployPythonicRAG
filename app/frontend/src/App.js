import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import FileUpload from './components/FileUpload';
import Chat from './components/Chat';
import { ThemeProvider } from './components/ui/theme-provider';
import { ThemeToggle } from './components/ui/theme-toggle';

function App() {
  const [sessionId, setSessionId] = useState('');
  const [isFileUploaded, setIsFileUploaded] = useState(false);
  const [fileName, setFileName] = useState('');
  const [docDescription, setDocDescription] = useState('');
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);
  const [selectedQuestion, setSelectedQuestion] = useState('');

  useEffect(() => {
    // Generate a unique session ID if one doesn't exist
    if (!sessionId) {
      setSessionId(uuidv4());
    }
  }, [sessionId]);

  const handleFileUploadSuccess = (fileName, description, questions) => {
    setIsFileUploaded(true);
    setFileName(fileName);
    setDocDescription(description);
    setSuggestedQuestions(questions);
  };

  const handleQuestionSelect = (question) => {
    setSelectedQuestion(question);
  };

  return (
    <ThemeProvider defaultTheme="light">
      <div className="min-h-screen bg-background text-foreground transition-colors duration-300">
        <header className="bg-primary text-primary-foreground py-4 px-6 shadow-md">
          <div className="container mx-auto flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span role="img" aria-label="brain" className="text-2xl">🧠</span>
              <h1 className="text-2xl font-bold">RAG Chat</h1>
            </div>
            <ThemeToggle />
          </div>
        </header>
        <main className="container mx-auto py-6 px-4">
          {!isFileUploaded ? (
            <FileUpload 
              sessionId={sessionId} 
              onUploadSuccess={handleFileUploadSuccess} 
            />
          ) : (
            <div className="rounded-lg border border-border bg-card p-6 shadow-sm transition-colors duration-300">
              <div className="mb-6">
                <div className="rounded-md bg-muted p-4 mb-4 transition-colors duration-300">
                  <h3 className="font-medium mb-2 flex items-center gap-2">
                    <span role="img" aria-label="document" className="text-xl">📄</span>
                    <span>Using file: <span className="font-bold">{fileName}</span></span>
                  </h3>
                  <p className="text-sm text-muted-foreground">{docDescription}</p>
                </div>
                
                {suggestedQuestions && suggestedQuestions.length > 0 && (
                  <div className="space-y-2 bg-card p-4 rounded-md border border-border transition-colors duration-300">
                    <h4 className="text-sm font-medium flex items-center gap-2">
                      <span role="img" aria-label="lightbulb" className="text-xl">💡</span>
                      <span>Suggested questions:</span>
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {suggestedQuestions.map((question, idx) => (
                        <button
                          key={idx}
                          className="text-xs bg-secondary text-secondary-foreground px-3 py-2 rounded-full hover:bg-secondary/80 transition-colors duration-200 flex items-center gap-1"
                          onClick={() => handleQuestionSelect(question)}
                        >
                          <span role="img" aria-label="question" className="text-xs">❓</span>
                          {question}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <Chat 
                sessionId={sessionId} 
                docDescription={docDescription}
                suggestedQuestions={suggestedQuestions}
                selectedQuestion={selectedQuestion}
                onQuestionSelected={() => setSelectedQuestion('')}
              />
            </div>
          )}
        </main>
        <footer className="container mx-auto py-4 px-6 text-center text-sm text-muted-foreground">
          <p>Made with <span role="img" aria-label="heart" className="text-red-500">❤️</span> and Shadcn/UI</p>
        </footer>
      </div>
    </ThemeProvider>
  );
}

export default App; 