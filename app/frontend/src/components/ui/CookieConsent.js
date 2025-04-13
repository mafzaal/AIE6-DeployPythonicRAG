import React, { useState, useEffect } from 'react';
import { Button } from './button';

const CookieConsent = () => {
  const [showConsent, setShowConsent] = useState(false);

  useEffect(() => {
    // Check if user has already consented
    const hasConsented = localStorage.getItem('cookieConsent');
    if (!hasConsented) {
      setShowConsent(true);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem('cookieConsent', 'true');
    setShowConsent(false);
  };

  if (!showConsent) {
    return null;
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-primary/95 text-primary-foreground p-4 shadow-lg z-50 transition-all duration-300 ease-in-out">
      <div className="container mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="text-sm md:text-base">
          <p className="mb-1 font-medium">We use cookies to enhance your experience.</p>
          <p className="text-xs opacity-80">
            This site uses cookies to store information about your preferences, including custom prompts settings. 
            By using this site, you consent to the placement of these cookies on your device.
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            onClick={handleAccept}
            variant="secondary"
            size="sm"
            className="whitespace-nowrap"
          >
            Accept Cookies
          </Button>
        </div>
      </div>
    </div>
  );
};

export default CookieConsent; 