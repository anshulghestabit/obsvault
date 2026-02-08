import Link from "next/link";

const Navbar = () => {
  return (
    <nav className="h-14 bg-[#212529] text-white flex items-center justify-between px-4 shadow-md z-50">
      
      {/* Left: Brand */}
      <div className="flex items-center gap-4">
        <Link href="/" className="text-lg font-bold tracking-wider">
          Start Bootstrap
        </Link>
      </div>

      {/* Right: Search & Profile (Hidden on mobile usually, but keeping simple here) */}
      <div className="hidden md:flex items-center gap-4">
        <div className="flex">
          <input 
            type="text" 
            placeholder="Search for..." 
            className="bg-white text-gray-900 rounded-l-md py-1 px-3 text-sm focus:outline-none w-64"
          />
          <button className="bg-blue-600 text-white rounded-r-md py-1 px-3 hover:bg-blue-700 transition">
            🔍
          </button>
        </div>
        
        {/* User Icon */}
        <div className="text-gray-400 hover:text-white cursor-pointer ml-2">👤</div>
      </div>

    </nav>
  );
};

export default Navbar;
