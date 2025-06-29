import React from 'react';
import { Link } from 'react-router-dom';

const Navigation = () => {
  return (
    <nav className="relative">
      <div className="glass backdrop-blur-lg bg-white/70 border-b border-white/20 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0 flex items-center">
                <div className="animate-slide-left">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
                      <span className="text-white font-bold text-lg">🤖</span>
                    </div>
                    <div>
                      <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                        GitHub-Jira AI Assistant
                      </h1>
                      <p className="text-xs text-gray-500">Streamline your workflow</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="animate-slide-left animate-delay-200">
                <div className="flex items-center space-x-2 px-3 py-1 rounded-full glass-dark">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-sm text-gray-600 font-medium">
                    Powered by IBM Granite
                  </span>
                </div>
              </div>
              
              <div className="animate-slide-left animate-delay-300">
                <Link
                  to="/"
                  className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium text-white btn-gradient shadow-lg"
                >
                  <span className="mr-2">🏠</span>
                  Dashboard
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Gradient line */}
      <div className="h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"></div>
    </nav>
  );
};

export default Navigation; 