import { Routes, Route, Navigate } from "react-router-dom";
import Header from "./components/Header";
import Navbar from "./components/NavBar";
import Footer from "./components/Footer";
import MigrationPage from "./pages/MigrationTab/MigrationPage";
import ValidationPage from "./pages/ValidationTab/ValidationPage";

function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Navigate to="/migration" replace />} />
          <Route path="/migration" element={<MigrationPage />} />
          <Route path="/validation" element={<ValidationPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}

export default App;