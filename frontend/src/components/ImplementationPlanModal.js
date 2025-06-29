import React from 'react';
import api from '../api/api';

const ImplementationPlanModal = ({ ticket, onClose }) => {
  
  // Debug logging
  console.log('🎭 ImplementationPlanModal rendered');
  console.log('🎫 Received ticket:', ticket);
  console.log('📝 Ticket plan:', ticket?.plan);
  console.log('📝 Plan type:', typeof ticket?.plan);
  console.log('📝 Plan length:', ticket?.plan?.length || 0);
  
  const handleDownloadPDF = async () => {
    if (ticket.pdf_url) {
      try {
        const filename = ticket.pdf_url.split('/').pop();
        const response = await api.downloadPDF(filename);
        
        // Create blob and download
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error('Error downloading PDF:', error);
      }
    }
  };

  // Function to format the implementation plan text
  const formatPlanText = (planText) => {
    console.log('🎨 formatPlanText called with:', planText?.substring(0, 100) + '...');
    
    if (!planText || planText.trim() === '') {
      console.log('❌ No plan text provided');
      return 'No implementation plan available.';
    }
    
    if (planText === 'No plan generated') {
      console.log('❌ Plan generation failed');
      return 'Implementation plan generation failed. Please try again.';
    }
    
    // Split by ## to identify sections
    const sections = planText.split(/^##\s*/gm).filter(section => section.trim());
    console.log('📋 Plan sections found:', sections.length);
    
    if (sections.length === 0) {
      // If no ## sections found, display as plain text
      console.log('📝 No sections found, displaying as plain text');
      return (
        <div className="mb-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-3 text-blue-600">
            Implementation Plan
          </h4>
          <div className="text-sm text-gray-700 whitespace-pre-line leading-relaxed bg-gray-50 p-4 rounded-lg">
            {planText}
          </div>
        </div>
      );
    }
    
    return sections.map((section, index) => {
      const lines = section.split('\n');
      const title = lines[0];
      const content = lines.slice(1).join('\n').trim();
      
      console.log(`📋 Section ${index + 1}: ${title}`);
      
      return (
        <div key={index} className="mb-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-3 text-blue-600">
            {title}
          </h4>
          <div className="text-sm text-gray-700 whitespace-pre-line leading-relaxed bg-gray-50 p-4 rounded-lg">
            {content || 'No content available for this section.'}
          </div>
        </div>
      );
    });
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity modal-backdrop" onClick={onClose}>
          <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full">
          <div className="bg-white px-6 pt-6 pb-4">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-xl leading-6 font-bold text-gray-900">
                  🎯 Implementation Plan
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  <span className="font-medium">{ticket.key}</span>: {ticket.summary || ticket.fields?.summary}
                </p>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <span className="sr-only">Close</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="max-h-96 overflow-y-auto border-t pt-6">
              {ticket.plan ? (
                <div className="space-y-4">
                  {formatPlanText(ticket.plan)}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="text-gray-500">
                    <svg className="mx-auto h-12 w-12 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p className="text-lg font-medium">No Implementation Plan Available</p>
                    <p className="text-sm mt-1">Generate a plan by clicking the "Generate Plan" button.</p>
                  </div>
                </div>
              )}
            </div>
            
            <div className="mt-6 flex justify-end space-x-3 border-t pt-4">
              {ticket.pdf_url && (
                <button
                  onClick={handleDownloadPDF}
                  className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors"
                >
                  📄 Download PDF
                </button>
              )}
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImplementationPlanModal; 