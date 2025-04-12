import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import FileUpload from './components/FileUpload';
import FileManager from './components/FileManager';
import Chat from './components/Chat';
import { ThemeProvider } from './components/ui/theme-provider';
import { ThemeToggle } from './components/ui/theme-toggle';

function App() {
  const [sessionId, setSessionId] = useState('');
  const [showUploadForm, setShowUploadForm] = useState(true);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [activeFileIndex, setActiveFileIndex] = useState(0);
  const [selectedQuestion, setSelectedQuestion] = useState('');

  // Get active file data
  const activeFile = uploadedFiles[activeFileIndex] || null;

  useEffect(() => {
    // Generate a unique session ID if one doesn't exist
    if (!sessionId) {
      setSessionId(uuidv4());
    }
  }, [sessionId]);

  const handleFileUploadSuccess = (fileName, description, questions) => {
    // Add the new file to the uploaded files array
    setUploadedFiles(prev => [
      ...prev,
      { 
        name: fileName, 
        description, 
        suggestedQuestions: questions,
        sessionId // Save the sessionId associated with this file
      }
    ]);
    
    // Set the newly uploaded file as active
    setActiveFileIndex(uploadedFiles.length);
    
    // Hide the upload form
    setShowUploadForm(false);
  };

  const handleSelectFile = (index) => {
    setActiveFileIndex(index);
  };

  const handleUploadNew = () => {
    // Generate a new session ID for the new file
    setSessionId(uuidv4());
    setShowUploadForm(true);
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
          {showUploadForm && (
            <FileUpload 
              sessionId={sessionId} 
              onUploadSuccess={handleFileUploadSuccess}
            />
          )}

          {!showUploadForm && uploadedFiles.length > 0 && (
            <div className="rounded-lg border border-border bg-card p-6 shadow-sm transition-colors duration-300">
              <FileManager 
                files={uploadedFiles}
                activeFileIndex={activeFileIndex}
                onSelectFile={handleSelectFile}
                onUploadNew={handleUploadNew}
              />
              
              <div className="rounded-md bg-muted p-4 mb-4 transition-colors duration-300">
                <h3 className="font-medium mb-2 flex items-center gap-2">
                  <span role="img" aria-label="document" className="text-xl">
                    {activeFile.name.toLowerCase().endsWith('.pdf') ? '📕' : '📄'}
                  </span>
                  <span>File: <span className="font-bold">{activeFile.name}</span></span>
                </h3>
                <p className="text-sm text-muted-foreground">{activeFile.description}</p>
              </div>
              
              {activeFile.suggestedQuestions && activeFile.suggestedQuestions.length > 0 && (
                <div className="space-y-2 bg-card p-4 rounded-md border border-border mb-4 transition-colors duration-300">
                  <h4 className="text-sm font-medium flex items-center gap-2">
                    <span role="img" aria-label="lightbulb" className="text-xl">💡</span>
                    <span>Suggested questions:</span>
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {activeFile.suggestedQuestions.map((question, idx) => (
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
              
              <Chat 
                sessionId={activeFile.sessionId}
                docDescription={activeFile.description}
                suggestedQuestions={activeFile.suggestedQuestions}
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