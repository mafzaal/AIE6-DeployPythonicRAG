import React from 'react';
import { Button } from './ui/button';

const FileManager = ({ files, activeFileIndex, onSelectFile, onUploadNew }) => {
  if (!files.length) return null;
  
  return (
    <div className="mb-6 min-h-[80px]">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-md font-medium flex items-center gap-2">
          <span role="img" aria-label="files" className="text-lg flex-shrink-0">📚</span>
          <span>Your Documents</span>
        </h3>
        <Button 
          onClick={onUploadNew}
          size="sm"
          variant="outline"
          className="flex items-center gap-1 text-xs"
        >
          <span role="img" aria-label="upload" className="flex-shrink-0">📄</span>
          <span>Upload New</span>
        </Button>
      </div>
      
      <div className="overflow-x-auto pb-2 scrollbar-thin">
        <div className="flex gap-2 pb-1 min-w-[300px]">
          {files.map((file, index) => (
            <button
              key={index}
              onClick={() => onSelectFile(index)}
              className={`
                px-3 py-2 rounded-md text-sm whitespace-nowrap flex items-center gap-1.5 min-w-0 flex-shrink-0 transition-colors
                ${activeFileIndex === index 
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary/70 hover:bg-secondary text-secondary-foreground'}
              `}
              style={{ minWidth: '120px', maxWidth: '200px' }}
            >
              <span role="img" aria-label="document" className="flex-shrink-0">
                {file.name.toLowerCase().endsWith('.pdf') ? '📕' : '📄'}
              </span>
              <span className="truncate">{file.name}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FileManager; 