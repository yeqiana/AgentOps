import { Outlet } from "react-router-dom";
import { Footer } from "../components/layout/Footer";
import { Header } from "../components/layout/Header";
import { PageNavigation } from "../components/layout/PageNavigation";
import { Sidebar } from "../components/layout/Sidebar";

export function AppLayout() {
  return (
    <div className="app-layout">
      <Sidebar />
      <div className="app-main-layout">
        <Header />
        <PageNavigation />
        <main className="app-content">
          <Outlet />
        </main>
        <Footer />
      </div>
    </div>
  );
}
