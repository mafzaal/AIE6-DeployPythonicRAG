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
    // Return cached user ID if available
    if (cachedUserId) {
      return cachedUserId;
    }
    
    // Get user ID from the server
    const response = await axios.get('/identify');
    const userId = response.data.user_id;
    
    // Cache the user ID for future use
    cachedUserId = userId;
    
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
  return cachedUserId;
};

export default {
  identifyUser,
  getCachedUserId
}; 