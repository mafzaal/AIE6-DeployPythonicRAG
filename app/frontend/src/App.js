import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import FileUpload from './components/FileUpload';
import Chat from './components/Chat';

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
    <div className="min-h-screen bg-background text-foreground">
      <header className="bg-primary text-primary-foreground py-4 px-6 shadow-md">
        <div className="container mx-auto">
          <h1 className="text-2xl font-bold">RAG Chat Application</h1>
        </div>
      </header>
      <main className="container mx-auto py-6 px-4">
        {!isFileUploaded ? (
          <FileUpload 
            sessionId={sessionId} 
            onUploadSuccess={handleFileUploadSuccess} 
          />
        ) : (
          <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
            <div className="mb-6">
              <div className="rounded-md bg-muted p-3 mb-3">
                <h3 className="font-medium mb-1">Using file: <span className="font-bold">{fileName}</span></h3>
                <p className="text-sm text-muted-foreground">{docDescription}</p>
              </div>
              
              {suggestedQuestions && suggestedQuestions.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Suggested questions:</h4>
                  <div className="flex flex-wrap gap-2">
                    {suggestedQuestions.map((question, idx) => (
                      <button
                        key={idx}
                        className="text-xs bg-secondary text-secondary-foreground px-3 py-1 rounded-full hover:bg-secondary/80"
                        onClick={() => handleQuestionSelect(question)}
                      >
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
    </div>
  );
}

export default App; 