import { render, screen } from '@testing-library/react';
import App from './App';

test('renders RAG Chat Application header', () => {
  render(<App />);
  const linkElement = screen.getByText(/RAG Chat Application/i);
  expect(linkElement).toBeInTheDocument();
}); 