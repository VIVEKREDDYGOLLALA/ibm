import React from 'react';

const TicketCard = ({ ticket, onGeneratePlan }) => {
  const getStatusColor = (status) => {
    const statusColors = {
      'To Do': 'bg-gray-100 text-gray-700 border-gray-200',
      'In Progress': 'bg-blue-100 text-blue-700 border-blue-200',
      'Done': 'bg-green-100 text-green-700 border-green-200',
      'Blocked': 'bg-red-100 text-red-700 border-red-200',
    };
    return statusColors[status] || 'bg-gray-100 text-gray-700 border-gray-200';
  };

  const getPriorityColor = (priority) => {
    const priorityColors = {
      'Highest': 'text-red-600',
      'High': 'text-orange-600',
      'Medium': 'text-yellow-600',
      'Low': 'text-green-600',
      'Lowest': 'text-blue-600',
    };
    return priorityColors[priority?.name] || 'text-gray-600';
  };

  const getPriorityIcon = (priority) => {
    const priorityIcons = {
      'Highest': '🔴',
      'High': '🟠',
      'Medium': '🟡',
      'Low': '🟢',
      'Lowest': '🔵',
    };
    return priorityIcons[priority?.name] || '⚪';
  };

  return (
    <div className="glass card-hover rounded-xl p-6 border border-white/20 animate-slide-up">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-3">
            <h3 className="text-lg font-bold text-gray-800">{ticket.key}</h3>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(ticket.fields.status.name)}`}>
              {ticket.fields.status.name}
            </span>
            {ticket.fields.priority && (
              <div className="flex items-center space-x-1">
                <span className="text-sm">{getPriorityIcon(ticket.fields.priority)}</span>
                <span className={`text-xs font-medium ${getPriorityColor(ticket.fields.priority)}`}>
                  {ticket.fields.priority.name}
                </span>
              </div>
            )}
          </div>
          
          <p className="text-gray-700 mb-4 leading-relaxed">
            {ticket.fields.summary}
          </p>
          
          <div className="flex items-center justify-between text-sm text-gray-500">
            {ticket.fields.assignee && (
              <div className="flex items-center space-x-2">
                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
                  {ticket.fields.assignee.displayName.charAt(0).toUpperCase()}
                </div>
                <span>Assigned to {ticket.fields.assignee.displayName}</span>
              </div>
            )}
            
            {ticket.fields.issuetype && (
              <div className="flex items-center space-x-1">
                <span className="text-xs">{ticket.fields.issuetype.name === 'Bug' ? '🐛' : ticket.fields.issuetype.name === 'Story' ? '📖' : '📋'}</span>
                <span className="text-xs">{ticket.fields.issuetype.name}</span>
              </div>
            )}
          </div>
        </div>
        
        <button
          onClick={onGeneratePlan}
          className="ml-6 px-4 py-2 btn-gradient text-white rounded-lg font-medium shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 flex items-center space-x-2"
        >
          <span>🎯</span>
          <span>Generate Plan</span>
        </button>
      </div>
      
      {/* Description preview */}
      {ticket.fields.description && (
        <div className="mt-4 pt-4 border-t border-white/20">
          <p className="text-sm text-gray-600 line-clamp-2">
            {(() => {
              // Handle different description formats from Jira
              let description = '';
              if (typeof ticket.fields.description === 'string') {
                description = ticket.fields.description;
              } else if (ticket.fields.description && typeof ticket.fields.description === 'object') {
                // For Jira rich text format, try to extract plain text
                description = JSON.stringify(ticket.fields.description);
              }
              
              const maxLength = 150;
              if (description.length > maxLength) {
                return description.substring(0, maxLength) + '...';
              }
              return description;
            })()}
          </p>
        </div>
      )}
    </div>
  );
};

export default TicketCard; 