import React, { useState } from 'react';
import axios from 'axios';
import './FileUpload.css';

const FileUpload = ({ sessionId, onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    
    if (!selectedFile) return;
    
    // Check file type
    const fileType = selectedFile.type;
    if (fileType !== 'text/plain' && fileType !== 'application/pdf') {
      setError('Please select a text or PDF file');
      return;
    }
    
    // Check file size (2MB max)
    if (selectedFile.size > 2 * 1024 * 1024) {
      setError('File size must be less than 2MB');
      return;
    }
    
    setFile(selectedFile);
    setError('');
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a file to upload');
      return;
    }
    
    setIsUploading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);
    
    try {
      const response = await axios.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      if (response.data.status === 'success') {
        onUploadSuccess(file.name);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      setError(error.response?.data?.detail || 'Failed to upload file');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="file-upload-container">
      <div className="upload-card">
        <h2>Upload a Document</h2>
        <p>Upload a text or PDF file to start chatting</p>
        
        <form onSubmit={handleUpload}>
          <div className="file-input-container">
            <input 
              type="file" 
              id="file" 
              onChange={handleFileChange}
              accept=".txt,.pdf"
              disabled={isUploading}
            />
            <label htmlFor="file" className={`file-label ${isUploading ? 'disabled' : ''}`}>
              {file ? file.name : 'Choose a file'}
            </label>
          </div>
          
          {error && <div className="error-message">{error}</div>}
          
          <button 
            type="submit" 
            className="upload-button"
            disabled={!file || isUploading}
          >
            {isUploading ? 'Uploading...' : 'Upload'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default FileUpload; 