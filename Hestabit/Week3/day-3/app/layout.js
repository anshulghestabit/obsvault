import "./globals.css";

export const metadata = {
  title: "Next.js App",
  description: "Day 3 Routing",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-white text-gray-800">
        {children}
      </body>
    </html>
  );
}
