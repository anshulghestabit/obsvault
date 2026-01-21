export default function Dashboard() {
  return (
    <div>
      <h1 className="text-3xl font-medium text-gray-800 mb-2">Dashboard</h1>
      
      {/* Breadcrumb */}
      <div className="bg-white p-3 rounded mb-6 text-gray-500 text-sm border border-gray-200 shadow-sm">
        <span className="text-blue-600 hover:underline cursor-pointer">Dashboard</span> 
        <span className="mx-2">/</span> 
        Overview
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        
        {/* Blue Card */}
        <div className="bg-blue-600 text-white rounded shadow-sm flex flex-col">
          <div className="p-4">Primary Card</div>
          <div className="p-3 bg-blue-700 bg-opacity-40 border-t border-blue-500 text-xs flex justify-between items-center cursor-pointer hover:underline">
            <span>View Details</span>
            <span>&gt;</span>
          </div>
        </div>

        {/* Yellow Card */}
        <div className="bg-yellow-500 text-white rounded shadow-sm flex flex-col">
          <div className="p-4">Warning Card</div>
          <div className="p-3 bg-yellow-600 bg-opacity-40 border-t border-yellow-400 text-xs flex justify-between items-center cursor-pointer hover:underline">
            <span>View Details</span>
            <span>&gt;</span>
          </div>
        </div>

        {/* Green Card */}
        <div className="bg-green-500 text-white rounded shadow-sm flex flex-col">
          <div className="p-4">Success Card</div>
          <div className="p-3 bg-green-600 bg-opacity-40 border-t border-green-400 text-xs flex justify-between items-center cursor-pointer hover:underline">
            <span>View Details</span>
            <span>&gt;</span>
          </div>
        </div>

        {/* Red Card */}
        <div className="bg-red-600 text-white rounded shadow-sm flex flex-col">
          <div className="p-4">Danger Card</div>
          <div className="p-3 bg-red-700 bg-opacity-40 border-t border-red-500 text-xs flex justify-between items-center cursor-pointer hover:underline">
            <span>View Details</span>
            <span>&gt;</span>
          </div>
        </div>
      </div>
    </div>
  );
}
