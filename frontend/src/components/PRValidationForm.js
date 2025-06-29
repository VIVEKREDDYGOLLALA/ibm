import React, { useState } from 'react';

const PRValidationForm = ({ onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    jira_issue_key: '',
    pr_url: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (formData.jira_issue_key && formData.pr_url) {
      onSubmit(formData);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header Section */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          🔍 Pull Request Validation
        </h2>
        <p className="text-gray-600">
          Analyze your PR against Jira ticket requirements and get merge recommendations
        </p>
      </div>

      {/* Information Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <span className="text-blue-500 text-lg mr-2">📋</span>
            <h3 className="font-medium text-blue-900">Requirements Check</h3>
          </div>
          <p className="text-sm text-blue-700">
            Validates if PR addresses all ticket requirements
          </p>
        </div>
        
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <span className="text-green-500 text-lg mr-2">✅</span>
            <h3 className="font-medium text-green-900">Merge Readiness</h3>
          </div>
          <p className="text-sm text-green-700">
            Determines if PR is ready to merge safely
          </p>
        </div>
        
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <span className="text-purple-500 text-lg mr-2">🤖</span>
            <h3 className="font-medium text-purple-900">AI Analysis</h3>
          </div>
          <p className="text-sm text-purple-700">
            Powered by IBM Granite for deep code analysis
          </p>
        </div>
      </div>

      {/* Form */}
      <div className="bg-white shadow rounded-lg p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="jira_issue_key" className="block text-sm font-medium text-gray-700 mb-1">
                Jira Issue Key
              </label>
              <input
                type="text"
                name="jira_issue_key"
                id="jira_issue_key"
                placeholder="e.g., PROJ-123, SCRUM-456"
                value={formData.jira_issue_key}
                onChange={handleChange}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                required
              />
              <p className="mt-1 text-xs text-gray-500">
                The Jira ticket this PR is intended to address
              </p>
            </div>

            <div>
              <label htmlFor="pr_url" className="block text-sm font-medium text-gray-700 mb-1">
                Pull Request URL
              </label>
              <input
                type="url"
                name="pr_url"
                id="pr_url"
                placeholder="https://github.com/owner/repo/pull/123"
                value={formData.pr_url}
                onChange={handleChange}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                required
              />
              <p className="mt-1 text-xs text-gray-500">
                Full URL to the GitHub pull request
              </p>
            </div>
          </div>

          {/* Analysis Features */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-2">
              What will be analyzed:
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <ul className="text-xs text-gray-600 space-y-1">
                <li className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  Code changes vs ticket requirements
                </li>
                <li className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  Completeness score calculation
                </li>
                <li className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  Code quality assessment
                </li>
              </ul>
              <ul className="text-xs text-gray-600 space-y-1">
                <li className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  Merge risk evaluation
                </li>
                <li className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  Missing requirements identification
                </li>
                <li className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  Actionable improvement suggestions
                </li>
              </ul>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading || !formData.jira_issue_key || !formData.pr_url}
              className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Analyzing PR...
                </>
              ) : (
                <>
                  🔍 Validate Pull Request
                </>
              )}
            </button>
          </div>
        </form>

        {/* Help Section */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-900 mb-2">
            💡 Tips for better analysis:
          </h3>
          <ul className="text-xs text-gray-600 space-y-1">
            <li>• Ensure the Jira ticket has clear requirements and acceptance criteria</li>
            <li>• Make sure the PR has a descriptive title and description</li>
            <li>• Include test files in your PR for comprehensive analysis</li>
            <li>• Link the Jira ticket in your PR description for better context</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default PRValidationForm; 