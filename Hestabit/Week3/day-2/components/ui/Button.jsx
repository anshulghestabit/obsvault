const Button = ({ children, variant = "primary", size = "md", className = "", ...props }) => {
  const baseStyles = "inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 rounded-md";
  
  const variants = {
    primary: "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500",
    secondary: "bg-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500",
    success: "bg-green-500 text-white hover:bg-green-600 focus:ring-green-400",
    danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
    outline: "bg-transparent border border-gray-300 text-gray-700 hover:bg-gray-50",
  };

  const sizes = {
    sm: "px-2.5 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };

  return (
    <button 
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`} 
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
