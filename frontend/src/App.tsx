import { Outlet } from "react-router-dom";

function App() {
  return (
    <main className="min-h-screen bg-slate-100 text-slate-900">
      <Outlet />
    </main>
  );
}

export default App;
