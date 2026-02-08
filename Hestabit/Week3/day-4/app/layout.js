import "./globals.css";

export const metadata = {
  title: "Acme UI – Build Faster with Modern UI",
  description: "A modern SaaS UI built with Next.js and Tailwind CSS",
}
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-white text-gray-800">
        {children}
      </body>
    </html>
  );
}
