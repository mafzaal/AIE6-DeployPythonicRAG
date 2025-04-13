// Version information
import packageInfo from '../../package.json';
import axios from 'axios';

// App version from package.json
export const APP_VERSION = packageInfo.version;

// Build date (when the file is imported/executed)
export const BUILD_DATE = new Date().toISOString().split('T')[0];

// Format the version string for display
export const getVersionString = () => {
  return `v${APP_VERSION} (${BUILD_DATE})`;
};

// API version information
export const fetchApiVersion = async () => {
  try {
    const response = await axios.get('/version');
    return response.data;
  } catch (error) {
    console.error('Error fetching API version:', error);
    return { 
      api_version: 'unknown', 
      build_date: 'unknown',
      status: 'unknown'
    };
  }
};

// Check if version is newer than stored version
export const isNewVersion = (storedVersion) => {
  if (!storedVersion) return true;
  return storedVersion !== APP_VERSION;
};

export default {
  APP_VERSION,
  BUILD_DATE,
  getVersionString,
  fetchApiVersion,
  isNewVersion
}; 