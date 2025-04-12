import React from 'react';
import { Button } from './ui/button';

const FileManager = ({ files, activeFileIndex, onSelectFile, onUploadNew }) => {
  if (!files.length) return null;
  
  return (
    <div className="mb-6">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-md font-medium flex items-center gap-2">
          <span role="img" aria-label="files" className="text-lg">📚</span>
          <span>Your Documents</span>
        </h3>
        <Button 
          onClick={onUploadNew}
          size="sm"
          variant="outline"
          className="flex items-center gap-1 text-xs"
        >
          <span role="img" aria-label="upload">📄</span>
          <span>Upload New</span>
        </Button>
      </div>
      
      <div className="overflow-x-auto">
        <div className="flex gap-2 pb-2">
          {files.map((file, index) => (
            <button
              key={index}
              onClick={() => onSelectFile(index)}
              className={`
                px-3 py-2 rounded-md text-sm whitespace-nowrap flex items-center gap-1.5 min-w-0 transition-colors
                ${activeFileIndex === index 
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary/70 hover:bg-secondary text-secondary-foreground'}
              `}
            >
              <span role="img" aria-label="document" className="flex-none">
                {file.name.toLowerCase().endsWith('.pdf') ? '📕' : '📄'}
              </span>
              <span className="truncate max-w-[150px]">{file.name}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FileManager; 