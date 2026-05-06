import { BrowserRouter, Route, Routes } from 'react-router-dom';
import InsightList from './pages/InsightList';
import InsightDetail from './pages/InsightDetail';
import Layout from './components/Layout';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<InsightList />} />
          <Route path="/insights/:id" element={<InsightDetail />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
