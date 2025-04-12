import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import FileUpload from './components/FileUpload';
import Chat from './components/Chat';

function App() {
  const [sessionId, setSessionId] = useState('');
  const [isFileUploaded, setIsFileUploaded] = useState(false);
  const [fileName, setFileName] = useState('');

  useEffect(() => {
    // Generate a unique session ID if one doesn't exist
    if (!sessionId) {
      setSessionId(uuidv4());
    }
  }, [sessionId]);

  const handleFileUploadSuccess = (fileName) => {
    setIsFileUploaded(true);
    setFileName(fileName);
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
            <div className="mb-4 rounded-md bg-muted p-3 text-sm">
              <p>Using file: <strong>{fileName}</strong></p>
            </div>
            <Chat sessionId={sessionId} />
          </div>
        )}
      </main>
    </div>
  );
}

export default App; 