import React, { useState } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';

const FileUpload = ({ sessionId, onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [progress, setProgress] = useState(0);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setErrorMessage('');
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setErrorMessage('Please select a file to upload');
      return;
    }

    setIsUploading(true);
    setProgress(0);
    setErrorMessage('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);

    try {
      const response = await axios.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percentCompleted);
        }
      });

      if (response.data.status === 'success') {
        setIsUploading(false);
        onUploadSuccess(
          file.name, 
          response.data.document_description || 'No description available', 
          response.data.suggested_questions || []
        );
      } else {
        setIsUploading(false);
        setErrorMessage(response.data.message || 'Upload failed');
      }
    } catch (error) {
      setIsUploading(false);
      setErrorMessage(error.response?.data?.message || 'Error uploading file');
      console.error('Error:', error);
    }
  };

  return (
    <div className="mx-auto max-w-md rounded-lg border border-border bg-card p-6 shadow-sm transition-colors duration-300">
      <div className="mb-6 text-center">
        <div className="mx-auto w-16 h-16 mb-4 rounded-full bg-primary/10 flex items-center justify-center">
          <span role="img" aria-label="upload" className="text-3xl">📄</span>
        </div>
        <h2 className="text-xl font-semibold mb-2">Upload Document</h2>
        <p className="text-sm text-muted-foreground">
          Upload a document to start chatting with AI about its contents ✨
        </p>
      </div>

      <form onSubmit={handleUpload} className="flex flex-col gap-4">
        <div className="grid w-full items-center gap-1.5">
          <label htmlFor="file-upload" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 flex items-center gap-1.5">
            <span role="img" aria-label="document" className="text-base">📋</span>
            <span>Select Document</span>
          </label>
          <Input
            id="file-upload"
            type="file"
            onChange={handleFileChange}
            disabled={isUploading}
            accept=".pdf,.txt,.doc,.docx"
            className="cursor-pointer transition-colors duration-300"
          />
          {file && (
            <p className="mt-1 text-xs text-muted-foreground flex items-center gap-1">
              <span role="img" aria-label="check" className="text-green-500">✅</span>
              <span>Selected: {file.name}</span>
            </p>
          )}
        </div>

        {errorMessage && (
          <div className="mb-4 rounded-md bg-destructive/15 p-3 text-sm text-destructive flex items-start gap-2">
            <span role="img" aria-label="error" className="mt-0.5">⚠️</span>
            <span>{errorMessage}</span>
          </div>
        )}

        {isUploading && (
          <div className="mb-4">
            <div className="mb-1 flex justify-between text-xs">
              <span className="flex items-center gap-1">
                <span role="img" aria-label="upload" className="text-xs">📤</span>
                <span>Uploading...</span>
              </span>
              <span>{progress}%</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
              <div 
                className="h-full bg-primary transition-all duration-300" 
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        <Button 
          type="submit" 
          disabled={isUploading || !file}
          className="w-full transition-colors duration-300 flex items-center justify-center gap-2"
        >
          {isUploading ? (
            <>
              <span>Processing...</span>
              <span role="img" aria-label="processing" className="animate-pulse">⏳</span>
            </>
          ) : (
            <>
              <span>Upload Document</span>
              <span role="img" aria-label="upload">🚀</span>
            </>
          )}
        </Button>
      </form>
    </div>
  );
};

export default FileUpload; 