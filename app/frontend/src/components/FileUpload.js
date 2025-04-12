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
        onUploadSuccess(file.name);
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
    <div className="mx-auto max-w-md rounded-lg border border-border bg-card p-6 shadow-sm">
      <div className="mb-6 text-center">
        <h2 className="text-xl font-semibold">Upload Document</h2>
        <p className="text-sm text-muted-foreground">
          Upload a document to start chatting with AI about its contents
        </p>
      </div>

      <form onSubmit={handleUpload} className="flex flex-col gap-4">
        <div className="grid w-full items-center gap-1.5">
          <label htmlFor="file-upload" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
            Document
          </label>
          <Input
            id="file-upload"
            type="file"
            onChange={handleFileChange}
            disabled={isUploading}
            accept=".pdf,.txt,.doc,.docx"
            className="cursor-pointer"
          />
        </div>

        {errorMessage && (
          <div className="mb-4 rounded-md bg-destructive/15 p-3 text-sm text-destructive">
            {errorMessage}
          </div>
        )}

        {isUploading && (
          <div className="mb-4">
            <div className="mb-1 flex justify-between text-xs">
              <span>Uploading...</span>
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
          className="w-full"
        >
          {isUploading ? 'Uploading...' : 'Upload Document'}
        </Button>
      </form>
    </div>
  );
};

export default FileUpload; 