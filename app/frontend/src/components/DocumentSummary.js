import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import axios from 'axios';

// Fallback data in case of API failure
const fallbackData = {
  keyTopics: ['Document analysis unavailable'],
  entities: ['Try refreshing the page'],
  wordCloudData: [
    { text: 'Document', value: 50 },
    { text: 'Summary', value: 40 },
    { text: 'Unavailable', value: 30 },
  ],
  documentStructure: [
    { title: 'Document structure unavailable', subsections: ['Please refresh the page or try a different document'] }
  ]
};

const DocumentSummary = ({ fileName, sessionId, userId }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchSummary = async () => {
      if (!sessionId) return;
      
      try {
        setLoading(true);
        setError('');
        
        // Add user ID to the request if available
        const response = await axios.post('/document-summary', { 
          session_id: sessionId,
          user_id: userId 
        });
        
        setSummaryData(response.data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching document summary:', error);
        setError('Failed to load document summary');
        setLoading(false);
      }
    };
    
    fetchSummary();
  }, [sessionId, userId]);

  if (loading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 mb-6 transition-colors duration-300">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span role="img" aria-label="chart" className="text-xl">📊</span>
          Document Summary Dashboard
        </h2>
        <div className="py-8 text-center">
          <div className="animate-pulse flex flex-col items-center">
            <div className="h-4 bg-muted-foreground/20 rounded w-1/4 mb-4"></div>
            <div className="h-2 bg-muted-foreground/20 rounded w-1/2 mb-2"></div>
            <div className="h-2 bg-muted-foreground/20 rounded w-1/3 mb-2"></div>
            <div className="h-2 bg-muted-foreground/20 rounded w-2/5 mb-2"></div>
            <div className="mt-4 text-sm text-muted-foreground">Generating document insights...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !summaryData) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 mb-6 transition-colors duration-300">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span role="img" aria-label="chart" className="text-xl">📊</span>
          Document Summary Dashboard
        </h2>
        <div className="py-4 text-center text-destructive">
          <span role="img" aria-label="error" className="text-2xl block mb-2">⚠️</span>
          {error}
        </div>
      </div>
    );
  }

  if (!summaryData) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 mb-6 transition-colors duration-300">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span role="img" aria-label="chart" className="text-xl">📊</span>
          Document Summary Dashboard
        </h2>
        <div className="py-4 text-center">No document summary available</div>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg p-4 mb-6 transition-colors duration-300">
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <span role="img" aria-label="chart" className="text-xl">📊</span>
        Document Summary Dashboard
      </h2>
      
      <div className="mb-4 border-b border-border">
        <div className="flex space-x-2">
          <Button 
            variant={activeTab === 'overview' ? "default" : "ghost"}
            size="sm"
            onClick={() => setActiveTab('overview')}
            className="rounded-b-none"
          >
            Overview
          </Button>
          <Button 
            variant={activeTab === 'wordcloud' ? "default" : "ghost"}
            size="sm"
            onClick={() => setActiveTab('wordcloud')}
            className="rounded-b-none"
          >
            Word Cloud
          </Button>
          <Button 
            variant={activeTab === 'structure' ? "default" : "ghost"}
            size="sm"
            onClick={() => setActiveTab('structure')}
            className="rounded-b-none"
          >
            Document Structure
          </Button>
        </div>
      </div>
      
      {activeTab === 'overview' && (
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-medium mb-2">Key Topics</h3>
            <div className="flex flex-wrap gap-2">
              {summaryData.keyTopics.map((topic, idx) => (
                <span 
                  key={idx} 
                  className="bg-primary/10 text-primary px-3 py-1 rounded-full text-sm"
                >
                  {topic}
                </span>
              ))}
            </div>
          </div>
          
          <div>
            <h3 className="text-sm font-medium mb-2">Key Entities</h3>
            <div className="flex flex-wrap gap-2">
              {summaryData.entities.map((entity, idx) => (
                <span 
                  key={idx} 
                  className="bg-secondary/10 text-secondary-foreground px-3 py-1 rounded-full text-sm"
                >
                  {entity}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {activeTab === 'wordcloud' && (
        <div className="py-4">
          <div className="bg-muted rounded-lg p-4 min-h-[200px] flex items-center justify-center">
            <div className="word-cloud-container">
              {summaryData.wordCloudData.map((word, idx) => {
                // Calculate font size based on value (scale from 14 to 36)
                const fontSize = 14 + (word.value - 16) * (22 / 48);
                const opacity = 0.5 + (word.value / 64) * 0.5;
                
                return (
                  <span 
                    key={idx} 
                    className="inline-block px-2 py-1 m-1 cursor-pointer hover:text-primary transition-colors duration-200"
                    style={{ 
                      fontSize: `${fontSize}px`, 
                      opacity,
                      transform: `rotate(${Math.random() * 20 - 10}deg)`
                    }}
                  >
                    {word.text}
                  </span>
                );
              })}
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            Word size represents frequency in the document. Click on any word to search for it.
          </p>
        </div>
      )}
      
      {activeTab === 'structure' && (
        <div className="py-4">
          <div className="bg-muted rounded-lg p-4 min-h-[200px]">
            <ul className="space-y-2">
              {summaryData.documentStructure.map((section, idx) => (
                <li key={idx} className="border-l-2 border-primary pl-3 py-1">
                  <div className="font-medium">{section.title}</div>
                  {section.subsections.length > 0 && (
                    <ul className="ml-4 mt-1 space-y-1">
                      {section.subsections.map((subsection, subIdx) => (
                        <li key={subIdx} className="border-l-2 border-secondary pl-3 py-1 text-sm">
                          {subsection}
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
            </ul>
          </div>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            Document structure extracted from headings and content organization.
          </p>
        </div>
      )}
    </div>
  );
};

export default DocumentSummary; 