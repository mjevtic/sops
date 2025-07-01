import { apiClient } from './apiClient';

export const authService = {
  async login(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    return response.data;
  },

  async logout() {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      // Ignore logout errors - we'll clear local storage anyway
      console.warn('Logout API call failed:', error);
    }
  },

  async refreshToken(refreshToken) {
    const response = await apiClient.post('/auth/refresh', {
      refresh_token: refreshToken
    });
    
    return response.data;
  },

  async getCurrentUser() {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  async changePassword(currentPassword, newPassword) {
    const response = await apiClient.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    });
    
    return response.data;
  },

  async requestPasswordReset(email) {
    const response = await apiClient.post('/auth/request-password-reset', {
      email
    });
    
    return response.data;
  },

  async resetPassword(token, newPassword) {
    const response = await apiClient.post('/auth/reset-password', {
      token,
      new_password: newPassword
    });
    
    return response.data;
  }
};

