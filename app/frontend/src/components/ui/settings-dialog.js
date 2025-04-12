import React from 'react';
import { Button } from './button';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from './dialog';
import { Switch } from './switch';
import { Label } from './label';

export function SettingsDialog({ settings, onSettingsChange }) {
  const handleDashboardToggle = (checked) => {
    onSettingsChange({
      ...settings,
      showDashboard: checked
    });
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button 
          variant="ghost" 
          size="sm"
          className="flex items-center gap-1"
        >
          <span role="img" aria-label="settings" className="text-lg">⚙️</span>
          <span className="hidden sm:inline">Settings</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Application Settings</DialogTitle>
          <DialogDescription>
            Customize your document analysis experience
          </DialogDescription>
        </DialogHeader>
        <div className="py-4 space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="dashboard-toggle">Document Dashboard</Label>
              <p className="text-sm text-muted-foreground">
                Show document summary with topics and structure visualization
              </p>
            </div>
            <Switch 
              id="dashboard-toggle"
              checked={settings.showDashboard}
              onCheckedChange={handleDashboardToggle}
            />
          </div>
        </div>
        <DialogFooter>
          <p className="text-sm text-muted-foreground mr-auto">
            Settings are saved automatically
          </p>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 