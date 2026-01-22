import Link from "next/link";

const Sidebar = () => {
  return (
    <aside className="w-64 bg-[#212529] text-[rgba(255,255,255,0.5)] flex flex-col h-full border-t border-gray-700">
      
      <div className="p-4 space-y-6 overflow-y-auto font-medium text-sm">
        
        {/* CORE */}
        <div>
          <div className="text-[0.65rem] font-bold text-gray-500 uppercase mb-2 tracking-wider">Core</div>
          <Link href="/" className="flex items-center gap-3 hover:text-white transition">
            <span>📊</span>
            <span>Dashboard</span>
          </Link>
        </div>

        {/* INTERFACE */}
        <div>
          <div className="text-[0.65rem] font-bold text-gray-500 uppercase mb-2 mt-4 tracking-wider">Interface</div>
          
          <div className="space-y-3">
            <Link href="#" className="flex items-center justify-between hover:text-white transition">
              <div className="flex items-center gap-3"><span>📄</span> Layouts</div>
              <span className="text-[10px]">▼</span>
            </Link>

            <Link href="#" className="flex items-center justify-between hover:text-white transition">
              <div className="flex items-center gap-3"><span>📖</span> Pages</div>
              <span className="text-[10px]">▼</span>
            </Link>
          </div>
        </div>

        {/* ADDONS */}
        <div>
          <div className="text-[0.65rem] font-bold text-gray-500 uppercase mb-2 mt-4 tracking-wider">Addons</div>
          <div className="space-y-3">
            <Link href="#" className="flex items-center gap-3 hover:text-white transition">
              <span>📈</span> Charts
            </Link>
            <Link href="#" className="flex items-center gap-3 hover:text-white transition">
              <span>📅</span> Tables
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-auto p-4 bg-[#343a40] text-[0.7rem] text-center">
        <div className="opacity-70">Logged in as:</div>
        <div className="text-white font-medium">Start Bootstrap</div>
      </div>
    </aside>
  );
};

export default Sidebar;


