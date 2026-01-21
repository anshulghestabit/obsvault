import "./globals.css";
import Navbar from "@/components/ui/Navbar";
import Sidebar from "@/components/ui/Sidebar";

export const metadata = {
  title: "Dashboard - Week 3",
  description: "Admin Dashboard Skeleton",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="flex flex-col h-screen bg-[#f8f9fa]">
        <Navbar />
        <div className="flex flex-1 overflow-hidden">
          <Sidebar />
          <main className="flex-1 overflow-y-auto p-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
