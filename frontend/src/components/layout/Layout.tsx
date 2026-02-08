import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import Header from "./Header";
import Sidebar from "./Sidebar";
import Footer from "./Footer";

/** Pages where the sidebar is shown for authenticated users. */
const SIDEBAR_ROUTES = ["/dashboard", "/problems"];

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();

  const showSidebar =
    isAuthenticated &&
    SIDEBAR_ROUTES.some((route) => location.pathname.startsWith(route));

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-950">
      <Header onMenuToggle={() => setSidebarOpen((v) => !v)} />

      <div className="flex flex-1">
        {showSidebar && (
          <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        )}

        <main
          className={`flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 ${
            showSidebar ? "lg:ml-0" : ""
          }`}
        >
          <Outlet />
        </main>
      </div>

      <Footer />
    </div>
  );
}
