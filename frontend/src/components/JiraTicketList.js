import React, { useState } from 'react';
import TicketCard from './TicketCard';
import RepoUrlModal from './RepoUrlModal';

const JiraTicketList = ({ tickets, loading, onGeneratePlan, onRefresh }) => {
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showRepoModal, setShowRepoModal] = useState(false);

  const handleGeneratePlan = (ticket) => {
    setSelectedTicket(ticket);
    setShowRepoModal(true);
  };

  const handleRepoSubmit = (repoUrl) => {
    onGeneratePlan(selectedTicket, repoUrl);
    setShowRepoModal(false);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <div className="animate-spin-slow w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full"></div>
        <p className="text-gray-600 font-medium">Loading Jira tickets...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">📋 Jira Tickets</h2>
          <p className="text-gray-600">
            {tickets.length > 0 
              ? `Found ${tickets.length} ticket${tickets.length !== 1 ? 's' : ''} ready for AI analysis`
              : 'No tickets found in your Jira workspace'
            }
          </p>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="inline-flex items-center px-4 py-2 btn-gradient text-white rounded-lg font-medium shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed space-x-2"
        >
          <span className={loading ? 'animate-spin' : ''}>🔄</span>
          <span>Refresh</span>
        </button>
      </div>

      {tickets.length === 0 ? (
        <div className="text-center py-16">
          <div className="glass rounded-xl p-8 max-w-md mx-auto">
            <div className="text-6xl mb-4">📭</div>
            <h3 className="text-xl font-bold text-gray-800 mb-2">No Tickets Found</h3>
            <p className="text-gray-600 mb-6">
              Make sure your Jira configuration is correct and you have access to projects with tickets.
            </p>
            <button
              onClick={onRefresh}
              className="btn-gradient text-white px-6 py-3 rounded-lg font-medium shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
            >
              🔄 Try Again
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {tickets.map((ticket, index) => (
            <div
              key={ticket.key}
              className="animate-slide-up"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <TicketCard
                ticket={ticket}
                onGeneratePlan={() => handleGeneratePlan(ticket)}
              />
            </div>
          ))}
        </div>
      )}

      {showRepoModal && (
        <RepoUrlModal
          onSubmit={handleRepoSubmit}
          onClose={() => setShowRepoModal(false)}
        />
      )}
    </div>
  );
};

export default JiraTicketList; 