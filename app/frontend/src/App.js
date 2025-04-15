import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import FileUpload from './components/FileUpload';
import FileManager from './components/FileManager';
import Chat from './components/Chat';
import DocumentSummary from './components/DocumentSummary';
import { ThemeProvider } from './components/ui/theme-provider';
import { ThemeToggle } from './components/ui/theme-toggle';
import { SettingsDialog } from './components/ui/settings-dialog';
import { getVersionString, fetchApiVersion } from './utils/version';
import { identifyUser, setupUserIdInterceptor } from './utils/user';
import PromptEditor from './components/ui/PromptEditor';

// Setup the axios interceptor to include user ID in all requests
setupUserIdInterceptor();

function App() {
  const [sessionId, setSessionId] = useState('');
  const [showUploadForm, setShowUploadForm] = useState(true);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [activeFileIndex, setActiveFileIndex] = useState(0);
  const [selectedQuestion, setSelectedQuestion] = useState('');
  const [apiVersion, setApiVersion] = useState(null);
  const [userId, setUserId] = useState(null);
  
  // App settings with localStorage persistence
  const [settings, setSettings] = useState(() => {
    // Initialize from localStorage, default to true if not set
    const saved = localStorage.getItem('appSettings');
    return saved ? JSON.parse(saved) : { showDashboard: true };
  });

  // Get active file data
  const activeFile = uploadedFiles[activeFileIndex] || null;

  useEffect(() => {
    // Generate a unique session ID if one doesn't exist
    if (!sessionId) {
      setSessionId(uuidv4());
    }
  }, [sessionId]);

  // Identify user on app load
  useEffect(() => {
    const identify = async () => {
      const id = await identifyUser();
      setUserId(id);
    };
    
    identify();
  }, []);

  // Fetch API version information
  useEffect(() => {
    const getApiVersion = async () => {
      const versionInfo = await fetchApiVersion();
      setApiVersion(versionInfo);
    };
    
    getApiVersion();
  }, []);

  // Save settings to localStorage when they change
  useEffect(() => {
    localStorage.setItem('appSettings', JSON.stringify(settings));
  }, [settings]);

  const handleSettingsChange = (newSettings) => {
    setSettings(newSettings);
  };

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

  const handlePromptsChange = () => {
    // Optional: Handle updates to prompts if needed
    console.log('Prompts were updated');
  };

  return (
    <ThemeProvider defaultTheme="light">
      <div className="min-h-screen bg-background text-foreground transition-colors duration-300 flex flex-col">
        <header className="bg-primary text-primary-foreground py-4 px-6 shadow-md w-full dark:bg-gray-900">
          <div className="container mx-auto flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span role="img" aria-label="brain" className="text-2xl">🧠</span>
              <h1 className="text-2xl font-bold">Quick Understand</h1>
            </div>
            <div className="flex items-center gap-4">
              {userId && <PromptEditor userId={userId} onPromptsChange={handlePromptsChange} />}
              
              {!showUploadForm && uploadedFiles.length > 0 && (
                <SettingsDialog 
                  settings={settings}
                  onSettingsChange={handleSettingsChange}
                />
              )}
              <ThemeToggle />
            </div>
          </div>
        </header>
        
        <main className="container mx-auto py-6 px-4 flex-1 flex items-center justify-center">
          <div className="w-full max-w-4xl">
            {showUploadForm && (
              <FileUpload 
                sessionId={sessionId} 
                onUploadSuccess={handleFileUploadSuccess}
              />
            )}

            {!showUploadForm && uploadedFiles.length > 0 && (
              <div className="rounded-lg border border-border bg-card p-6 shadow-sm transition-colors duration-300 w-full">
                <FileManager 
                  files={uploadedFiles}
                  activeFileIndex={activeFileIndex}
                  onSelectFile={handleSelectFile}
                  onUploadNew={handleUploadNew}
                />
                
                <div className="rounded-md bg-muted p-4 mb-4 transition-colors duration-300 min-h-[100px]">
                  <h3 className="font-medium mb-2 flex items-center gap-2">
                    <span role="img" aria-label="document" className="text-xl flex-shrink-0">
                      {activeFile.name.toLowerCase().endsWith('.pdf') ? '📕' : '📄'}
                    </span>
                    <span className="truncate">File: <span className="font-bold">{activeFile.name}</span></span>
                  </h3>
                  <p className="text-sm text-muted-foreground line-clamp-3">{activeFile.description}</p>
                </div>
                
                {settings.showDashboard && 
                  <DocumentSummary 
                    fileName={activeFile.name} 
                    sessionId={activeFile.sessionId}
                    userId={userId}
                  />
                }
                
                <div className="min-h-[100px] mb-4">
                  {activeFile.suggestedQuestions && activeFile.suggestedQuestions.length > 0 && (
                    <div className="space-y-2 bg-card p-4 rounded-md border border-border transition-colors duration-300 h-full">
                      <h4 className="text-sm font-medium flex items-center gap-2">
                        <span role="img" aria-label="lightbulb" className="text-xl flex-shrink-0">💡</span>
                        <span>Suggested questions:</span>
                      </h4>
                      <div className="flex flex-wrap gap-2 overflow-y-auto max-h-[100px] pb-1">
                        {activeFile.suggestedQuestions.map((question, idx) => (
                          <button
                            key={idx}
                            className="text-xs bg-secondary text-secondary-foreground px-3 py-2 rounded-full hover:bg-secondary/80 transition-colors duration-200 flex items-center gap-1 flex-shrink-0"
                            onClick={() => handleQuestionSelect(question)}
                          >
                            <span role="img" aria-label="question" className="text-xs flex-shrink-0">❓</span>
                            <span className="truncate max-w-[200px]">{question}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                
                <Chat 
                  sessionId={activeFile.sessionId}
                  userId={userId}
                  docDescription={activeFile.description}
                  suggestedQuestions={activeFile.suggestedQuestions}
                  selectedQuestion={selectedQuestion}
                  onQuestionSelected={() => setSelectedQuestion('')}
                />
              </div>
            )}
          </div>
        </main>
        
        <footer className="w-full py-4 px-6 text-center text-sm text-muted-foreground">
          <div className="flex flex-col items-center justify-center">
            <p>Made with <span role="img" aria-label="heart" className="text-red-500">❤️</span> and Shadcn/UI</p>
            <div className="text-xs opacity-70 mt-1 flex items-center gap-2 justify-center">
              <span>UI: {getVersionString()}</span>
              {apiVersion && (
                <>
                  <span className="bg-border/30 w-[1px] h-3 inline-block"></span>
                  <span>API: v{apiVersion.api_version}</span>
                  <span className={`w-2 h-2 rounded-full ${
                    apiVersion.status === 'operational' 
                      ? 'bg-green-500' 
                      : 'bg-amber-500'
                  }`} title={`Status: ${apiVersion.status}`}></span>
                </>
              )}
            </div>
          </div>
        </footer>
      </div>
    </ThemeProvider>
  );
}

export default App; 