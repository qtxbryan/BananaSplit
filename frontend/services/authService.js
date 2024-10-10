import axios from 'axios';

const API_URL = "http://localhost:8888/v1/auth";

export const login = async (email, password) => {
    try {
      const response = await axios.post(`${API_URL}/login`, { email, password });
      
      const { access_token, token_type, user_id } = response.data;
  
      localStorage.setItem('token', access_token);
      localStorage.setItem('user_id', user_id);  
  
      return { access_token, token_type, user_id };
    } catch (error) {
      throw new Error(error.response?.data?.msg || 'Login failed');
    }
  };
  
export const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
};