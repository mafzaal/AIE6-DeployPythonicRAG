import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import FileUpload from './components/FileUpload';
import Chat from './components/Chat';
import './App.css';

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
    <div className="App">
      <header className="App-header">
        <h1>RAG Chat Application</h1>
      </header>
      <main>
        {!isFileUploaded ? (
          <FileUpload 
            sessionId={sessionId} 
            onUploadSuccess={handleFileUploadSuccess} 
          />
        ) : (
          <div className="chat-container">
            <div className="file-info">
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