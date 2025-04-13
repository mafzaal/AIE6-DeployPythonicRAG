import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './button';
import { Textarea } from './textarea';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from './dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './tabs';

const PromptEditor = ({ userId, onPromptsChange }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [prompts, setPrompts] = useState({
    system_template: '',
    user_template: ''
  });
  const [isOpen, setIsOpen] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');

  // Fetch current prompts when the component mounts or userId changes
  useEffect(() => {
    if (isOpen && userId) {
      fetchPrompts();
    }
  }, [userId, isOpen]);

  const fetchPrompts = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`/prompts${userId ? `?user_id=${userId}` : ''}`);
      setPrompts({
        system_template: response.data.system_template,
        user_template: response.data.user_template
      });
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching prompts:', error);
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setIsLoading(true);
      setSaveStatus('Saving...');
      
      await axios.post('/prompts', prompts, {
        params: userId ? { user_id: userId } : {}
      });
      
      setSaveStatus('Saved successfully!');
      
      // Notify parent component about the prompt change
      if (onPromptsChange) {
        onPromptsChange(prompts);
      }
      
      setTimeout(() => {
        setSaveStatus('');
        setIsOpen(false);
      }, 1500);
      
      setIsLoading(false);
    } catch (error) {
      console.error('Error saving prompts:', error);
      setSaveStatus('Error saving prompts');
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    try {
      setIsLoading(true);
      
      await axios.post('/prompts/reset', {}, {
        params: userId ? { user_id: userId } : {}
      });
      
      // Fetch the reset prompts
      await fetchPrompts();
      
      setSaveStatus('Reset to defaults');
      setTimeout(() => setSaveStatus(''), 1500);
      
      // Notify parent component about the prompt change
      if (onPromptsChange) {
        onPromptsChange(prompts);
      }
      
      setIsLoading(false);
    } catch (error) {
      console.error('Error resetting prompts:', error);
      setSaveStatus('Error resetting prompts');
      setIsLoading(false);
    }
  };

  const handlePromptChange = (type, value) => {
    setPrompts(prev => ({
      ...prev,
      [type]: value
    }));
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button 
          variant="outline" 
          size="sm" 
          className="flex items-center gap-1 bg-secondary dark:bg-gray-700 text-foreground dark:text-gray-100 hover:bg-secondary/80 dark:hover:bg-gray-600 border-secondary dark:border-gray-600"
        >
          <span role="img" aria-label="customize" className="text-sm">⚙️</span>
          <span>Customize Prompts</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Customize AI Prompts</DialogTitle>
          <DialogDescription>
            Customize how the AI responds to your questions. Changes are saved automatically to your browser.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="system" className="w-full mt-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="system">System Prompt</TabsTrigger>
            <TabsTrigger value="user">User Prompt</TabsTrigger>
          </TabsList>
          
          <TabsContent value="system" className="mt-4">
            <div className="space-y-2">
              <h3 className="text-sm font-medium">System Prompt Template</h3>
              <p className="text-xs text-muted-foreground">
                This controls how the AI formats its response and interacts with the context.
              </p>
              <Textarea
                className="min-h-[450px] font-mono text-sm"
                value={prompts.system_template}
                onChange={(e) => handlePromptChange('system_template', e.target.value)}
                placeholder="Enter system prompt template..."
                disabled={isLoading}
              />
            </div>
          </TabsContent>
          
          <TabsContent value="user" className="mt-4">
            <div className="space-y-2">
              <h3 className="text-sm font-medium">User Prompt Template</h3>
              <p className="text-xs text-muted-foreground">
                This controls how your question and the document context are combined. <code>{"{context}"}</code> and <code>{"{question}"}</code> are replaced with the actual values.
              </p>
              <Textarea
                className="min-h-[450px] font-mono text-sm"
                value={prompts.user_template}
                onChange={(e) => handlePromptChange('user_template', e.target.value)}
                placeholder="Enter user prompt template..."
                disabled={isLoading}
              />
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter className="flex justify-between items-center">
          <div className="text-sm text-muted-foreground">
            {saveStatus}
          </div>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              onClick={handleReset}
              disabled={isLoading}
            >
              Reset to Default
            </Button>
            <Button
              onClick={handleSave}
              disabled={isLoading}
            >
              Save Changes
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default PromptEditor; 