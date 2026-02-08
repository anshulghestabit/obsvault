"use client";
import Card from "@/components/ui/Card";

export default function Dashboard() {
  return (
    <div>
      <h1 className="text-4xl font-medium text-gray-800 mb-2">Dashboard</h1>
      
      {/* Breadcrumb */}
      <div className="bg-[#e9ecef] p-3 rounded mb-6 text-gray-500 text-sm">
        <span className="text-blue-600 hover:underline cursor-pointer">Dashboard</span> 
        <span className="mx-2">/</span> 
        Overview
      </div>

      {/* TOP ROW: Colored Cards (Matches Image: Primary, Warning, Success, Danger) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        
        {/* Blue */}
        <Card color="primary" footer={<><span>View Details</span><span>&gt;</span></>}>
          <div className="text-white mb-2">Primary Card</div>
        </Card>

        {/* Yellow */}
        <Card color="warning" footer={<><span>View Details</span><span>&gt;</span></>}>
          <div className="text-white mb-2">Warning Card</div>
        </Card>

        {/* Green */}
        <Card color="success" footer={<><span>View Details</span><span>&gt;</span></>}>
          <div className="text-white mb-2">Success Card</div>
        </Card>

        {/* Red */}
        <Card color="danger" footer={<><span>View Details</span><span>&gt;</span></>}>
          <div className="text-white mb-2">Danger Card</div>
        </Card>
      </div>
      
      {/* MIDDLE ROW: Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        
        {/* Area Chart */}
        <Card 
          title="Area Chart Example" 
          icon="📈" 
          footer="Updated yesterday at 11:59 PM"
        >
          {/* Fake Visual for Area Chart */}
          <div className="h-64 w-full relative flex items-end px-2 pb-6">
            <svg className="w-full h-full" viewBox="0 0 100 50" preserveAspectRatio="none">
              <path d="M0,50 L0,40 L10,15 L20,30 L30,25 L40,40 L50,30 L60,25 L70,35 L80,20 L90,15 L100,5 L100,50 Z" fill="rgba(59, 130, 246, 0.1)" stroke="none" />
              <path d="M0,40 L10,15 L20,30 L30,25 L40,40 L50,30 L60,25 L70,35 L80,20 L90,15 L100,5" fill="none" stroke="#3b82f6" strokeWidth="0.5" />
            </svg>
            <div className="absolute bottom-0 w-full flex justify-between text-[10px] text-gray-400 px-1">
              <span>Mar 1</span><span>Mar 5</span><span>Mar 9</span><span>Mar 13</span>
            </div>
          </div>
        </Card>

        {/* Bar Chart */}
        <Card 
          title="Bar Chart Example" 
          icon="📊" 
          footer="Updated yesterday at 11:59 PM"
        >
          {/* Fake Visual for Bar Chart */}
          <div className="h-64 w-full flex items-end justify-between gap-2 px-2 pb-6 pt-4">
             <div className="w-full bg-blue-600 h-[30%] rounded-t-sm"></div>
             <div className="w-full bg-blue-600 h-[45%] rounded-t-sm"></div>
             <div className="w-full bg-blue-600 h-[55%] rounded-t-sm"></div>
             <div className="w-full bg-blue-600 h-[65%] rounded-t-sm"></div>
             <div className="w-full bg-blue-600 h-[80%] rounded-t-sm"></div>
             <div className="w-full bg-blue-600 h-[100%] rounded-t-sm"></div>
          </div>
           <div className="flex justify-between text-[10px] text-gray-400 mt-[-20px] px-2">
              <span>Jan</span><span>Feb</span><span>Mar</span><span>Apr</span><span>May</span><span>Jun</span>
            </div>
        </Card>
      </div>

      {/* BOTTOM ROW: Data Table */}
      <Card title="DataTable Example" icon="📅" footer="Updated yesterday at 11:59 PM">
        
        {/* Table Controls */}
        <div className="flex flex-col sm:flex-row justify-between items-center mb-4 gap-4">
          <div className="text-sm text-gray-600">
            Show <select className="border border-gray-300 rounded mx-1 p-1"><option>10</option></select> entries
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            Search: <input type="text" className="border border-gray-300 rounded p-1 focus:outline-blue-500" />
          </div>
        </div>

        {/* Table Data */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse border border-gray-200 text-sm">
            <thead>
              <tr className="bg-white">
                <th className="border border-gray-200 p-2 font-bold text-gray-700 cursor-pointer">Name ⇅</th>
                <th className="border border-gray-200 p-2 font-bold text-gray-700 cursor-pointer">Position ⇅</th>
                <th className="border border-gray-200 p-2 font-bold text-gray-700 cursor-pointer">Office ⇅</th>
                <th className="border border-gray-200 p-2 font-bold text-gray-700 cursor-pointer">Age ⇅</th>
                <th className="border border-gray-200 p-2 font-bold text-gray-700 cursor-pointer">Start date ⇅</th>
                <th className="border border-gray-200 p-2 font-bold text-gray-700 cursor-pointer">Salary ⇅</th>
              </tr>
            </thead>
            <tbody>
              <tr className="odd:bg-[#f2f2f2] even:bg-white text-gray-600">
                <td className="border border-gray-200 p-2">Tiger Nixon</td>
                <td className="border border-gray-200 p-2">System Architect</td>
                <td className="border border-gray-200 p-2">Edinburgh</td>
                <td className="border border-gray-200 p-2">61</td>
                <td className="border border-gray-200 p-2">2011/04/25</td>
                <td className="border border-gray-200 p-2">$320,800</td>
              </tr>
              <tr className="odd:bg-[#f2f2f2] even:bg-white text-gray-600">
                <td className="border border-gray-200 p-2">Garrett Winters</td>
                <td className="border border-gray-200 p-2">Accountant</td>
                <td className="border border-gray-200 p-2">Tokyo</td>
                <td className="border border-gray-200 p-2">63</td>
                <td className="border border-gray-200 p-2">2011/07/25</td>
                <td className="border border-gray-200 p-2">$170,750</td>
              </tr>
               <tr className="odd:bg-[#f2f2f2] even:bg-white text-gray-600">
                <td className="border border-gray-200 p-2">Ashton Cox</td>
                <td className="border border-gray-200 p-2">Junior Technical Author</td>
                <td className="border border-gray-200 p-2">San Francisco</td>
                <td className="border border-gray-200 p-2">66</td>
                <td className="border border-gray-200 p-2">2009/01/12</td>
                <td className="border border-gray-200 p-2">$86,000</td>
              </tr>
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        <div className="flex justify-between items-center mt-4 text-sm text-gray-600">
            <div>Showing 1 to 3 of 57 entries</div>
            <div className="flex gap-0">
                <button className="px-3 py-1 border border-gray-300 rounded-l bg-white hover:bg-gray-100">Previous</button>
                <button className="px-3 py-1 border border-gray-300 bg-blue-600 text-white">1</button>
                <button className="px-3 py-1 border border-gray-300 bg-white hover:bg-gray-100">2</button>
                <button className="px-3 py-1 border border-gray-300 bg-white hover:bg-gray-100">3</button>
                <button className="px-3 py-1 border border-gray-300 bg-white hover:bg-gray-100">4</button>
                <button className="px-3 py-1 border border-gray-300 bg-white hover:bg-gray-100">5</button>
                <button className="px-3 py-1 border border-gray-300 bg-white hover:bg-gray-100">6</button>
                <button className="px-3 py-1 border border-gray-300 rounded-r bg-white hover:bg-gray-100">Next</button>
            </div>
        </div>

      </Card>
    </div>
  );
}
