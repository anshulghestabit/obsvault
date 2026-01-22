import Link from "next/link";
import Button from "@/components/ui/Button";

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#212529] text-white">
      <h1 className="text-5xl font-bold mb-6">Welcome to SB Admin</h1>
      <p className="text-gray-400 mb-8">Day 3: Routing and Layouts Demo</p>
      
      <div className="flex gap-4">
        <Link href="/dashboard">
          <Button variant="primary" size="lg">Go to Dashboard</Button>
        </Link>
      </div>
    </div>
  );
}
