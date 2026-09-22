// import { Routes, Route, Navigate } from "react-router-dom";
// import Header from "./components/Header";
// import Navbar from "./components/NavBar";
// import Footer from "./components/Footer";
// import MigrationPage from "./pages/MigrationTab/MigrationPage";
// import ValidationPage from "./pages/ValidationTab/ValidationPage";

// function App() {
//   return (
//     <div className="min-h-screen bg-gray-50 flex flex-col">
//       <Header />
//       <Navbar />
//       <main className="flex-1">
//         <Routes>
//           <Route path="/" element={<Navigate to="/migration" replace />} />
//           <Route path="/migration" element={<MigrationPage />} />
//           <Route path="/validation" element={<ValidationPage />} />
//         </Routes>
//       </main>
//       <Footer />
//     </div>
//   );
// }

// export default App;

import { useEffect, useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Header from "./components/Header";
import Navbar from "./components/NavBar";
import Footer from "./components/Footer";
import MigrationPage from "./pages/MigrationTab/MigrationPage";
import ValidationPage from "./pages/ValidationTab/ValidationPage";
import { checkHealth } from "./api/client";

const HEALTH_CHECK_INTERVAL_MS = 15000;

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionChecking, setConnectionChecking] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const runCheck = async () => {
      const ok = await checkHealth();
      if (!cancelled) {
        setIsConnected(ok);
        setConnectionChecking(false);
      }
    };

    runCheck();
    const interval = setInterval(runCheck, HEALTH_CHECK_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header isConnected={isConnected} connectionChecking={connectionChecking} />
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