const Card = ({ title, children, color = "white", className = "" }) => {
  const colorClasses = {
    white: "bg-white text-gray-800 border-gray-200",
    primary: "bg-blue-600 text-white border-blue-600",
    warning: "bg-yellow-500 text-white border-yellow-500",
    success: "bg-green-500 text-white border-green-500",
    danger: "bg-red-600 text-white border-red-600",
    dark: "bg-gray-800 text-white border-gray-700",
  };

  const selectedColor = colorClasses[color] || colorClasses.white;

  return (
    <div className={`rounded-md shadow-sm border flex flex-col h-full ${selectedColor} ${className}`}>
      {title && (
        <div className="p-4 font-medium text-sm uppercase tracking-wider opacity-90">
          {title}
        </div>
      )}
      <div className="flex-1 p-4">
        {children}
      </div>
    </div>
  );
};

export default Card;

