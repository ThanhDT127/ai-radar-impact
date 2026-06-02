import { BrowserRouter, Route, Routes } from 'react-router-dom';
import InsightList from './pages/InsightList';
import InsightDetail from './pages/InsightDetail';
import Layout from './components/Layout';
import { ThemeProvider } from './contexts/ThemeContext';
import ErrorBoundary from './components/ErrorBoundary';

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Layout>
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<InsightList />} />
              <Route path="/insights/:id" element={<InsightDetail />} />
            </Routes>
          </ErrorBoundary>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  );
}
