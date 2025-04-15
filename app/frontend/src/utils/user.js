import axios from 'axios';

// Variable to store user ID once obtained
let cachedUserId = null;

/**
 * Identify the current user, either by getting existing ID from API 
 * or creating a new user ID if none exists
 * 
 * @returns {Promise<string>} The user ID
 */
export const identifyUser = async () => {
  try {
    // First check localStorage for existing user ID
    const storedUserId = localStorage.getItem('user_id');
    
    // Return cached or stored user ID if available
    if (cachedUserId) {
      return cachedUserId;
    }
    
    if (storedUserId) {
      cachedUserId = storedUserId;
      return storedUserId;
    }
    
    // Get user ID from the server
    const response = await axios.get('/identify');
    const userId = response.data.user_id;
    
    // Cache the user ID for future use
    cachedUserId = userId;
    
    // Store in localStorage for persistence across sessions
    localStorage.setItem('user_id', userId);
    
    return userId;
  } catch (error) {
    console.error('Error identifying user:', error);
    return null;
  }
};

/**
 * Get the cached user ID or null if not identified yet
 * 
 * @returns {string|null} The cached user ID
 */
export const getCachedUserId = () => {
  if (!cachedUserId) {
    // Try to get from localStorage if not in memory
    cachedUserId = localStorage.getItem('user_id');
  }
  return cachedUserId;
};

/**
 * Configure axios to automatically include user ID in requests
 */
export const setupUserIdInterceptor = () => {
  axios.interceptors.request.use(function (config) {
    const userId = getCachedUserId();
    if (userId) {
      // Add user ID as a header
      config.headers['X-User-ID'] = userId;
      
      // Add user ID as a URL parameter for GET requests
      if (config.method === 'get') {
        config.params = config.params || {};
        if (!config.params.user_id) {
          config.params.user_id = userId;
        }
      }
    }
    return config;
  }, function (error) {
    return Promise.reject(error);
  });
};

export default {
  identifyUser,
  getCachedUserId,
  setupUserIdInterceptor
}; 