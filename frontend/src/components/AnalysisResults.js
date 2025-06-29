import React from 'react';

const AnalysisResults = ({ analysis }) => {
  const getStatusColor = (status) => {
    const colors = {
      'valid': 'text-green-600 bg-green-50 border-green-200',
      'needs_improvement': 'text-yellow-600 bg-yellow-50 border-yellow-200',
      'invalid': 'text-red-600 bg-red-50 border-red-200'
    };
    return colors[status] || 'text-gray-600 bg-gray-50 border-gray-200';
  };

  const getMergeRecommendationColor = (recommendation) => {
    const colors = {
      'ready_to_merge': 'text-green-600 bg-green-50 border-green-200',
      'needs_improvements': 'text-yellow-600 bg-yellow-50 border-yellow-200',
      'major_changes_required': 'text-red-600 bg-red-50 border-red-200'
    };
    return colors[recommendation] || 'text-gray-600 bg-gray-50 border-gray-200';
  };

  const getRiskLevelColor = (riskLevel) => {
    const colors = {
      'low': 'text-green-600 bg-green-50',
      'medium': 'text-yellow-600 bg-yellow-50',
      'high': 'text-red-600 bg-red-50'
    };
    return colors[riskLevel] || 'text-gray-600 bg-gray-50';
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-6">
      {/* Main Status Card */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">
            🔍 PR Analysis Results
          </h2>
          {analysis.can_merge ? (
            <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-bold text-green-700 bg-green-100 border border-green-300">
              ✅ Ready to Merge
            </span>
          ) : (
            <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-bold text-red-700 bg-red-100 border border-red-300">
              ❌ Not Ready
            </span>
          )}
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Status */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-500">Validation Status</span>
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(analysis.validation_status)}`}>
                {analysis.validation_status.replace('_', ' ').toUpperCase()}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-500">Merge Recommendation</span>
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getMergeRecommendationColor(analysis.merge_recommendation)}`}>
                {analysis.merge_recommendation.replace('_', ' ').toUpperCase()}
              </span>
            </div>

            {analysis.pr_summary && (
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-500">Risk Level</span>
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getRiskLevelColor(analysis.pr_summary.risk_level)}`}>
                  {analysis.pr_summary.risk_level.toUpperCase()}
                </span>
              </div>
            )}
          </div>

          {/* Completeness Score */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-500">Completeness Score</span>
              <span className="text-sm font-bold text-gray-900">
                {analysis.completeness_score}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div 
                className={`h-3 rounded-full transition-all duration-500 ${getScoreColor(analysis.completeness_score)}`}
                style={{ width: `${analysis.completeness_score}%` }}
              ></div>
            </div>
            
            {analysis.pr_summary && (
              <>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">Addresses Ticket:</span>
                  <span className={analysis.pr_summary.addresses_ticket ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                    {analysis.pr_summary.addresses_ticket ? '✅ Yes' : '❌ No'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">Code Quality:</span>
                  <span className={analysis.pr_summary.code_quality === 'good' ? 'text-green-600 font-medium' : 'text-yellow-600 font-medium'}>
                    {analysis.pr_summary.code_quality === 'good' ? '✅ Good' : '⚠️ Needs Review'}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Merge Blockers (if any) */}
      {analysis.merge_blockers && analysis.merge_blockers.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6 border-l-4 border-red-500">
          <h3 className="text-lg font-medium text-red-700 mb-3 flex items-center">
            🚫 Merge Blockers
          </h3>
          <ul className="list-disc list-inside space-y-1">
            {analysis.merge_blockers.map((blocker, index) => (
              <li key={index} className="text-sm text-red-600 font-medium">{blocker}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Missing Requirements */}
      {analysis.missing_requirements && analysis.missing_requirements.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6 border-l-4 border-yellow-500">
          <h3 className="text-lg font-medium text-yellow-700 mb-3 flex items-center">
            📋 Missing Requirements
          </h3>
          <ul className="list-disc list-inside space-y-1">
            {analysis.missing_requirements.map((req, index) => (
              <li key={index} className="text-sm text-yellow-600">{req}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Code Quality Issues */}
      {analysis.code_quality_issues && analysis.code_quality_issues.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6 border-l-4 border-orange-500">
          <h3 className="text-lg font-medium text-orange-700 mb-3 flex items-center">
            🔧 Code Quality Issues
          </h3>
          <ul className="list-disc list-inside space-y-1">
            {analysis.code_quality_issues.map((issue, index) => (
              <li key={index} className="text-sm text-orange-600">{issue}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Suggestions */}
      {analysis.suggestions && analysis.suggestions.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6 border-l-4 border-blue-500">
          <h3 className="text-lg font-medium text-blue-700 mb-3 flex items-center">
            💡 Suggestions for Improvement
          </h3>
          <ul className="list-disc list-inside space-y-1">
            {analysis.suggestions.map((suggestion, index) => (
              <li key={index} className="text-sm text-blue-600">{suggestion}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Detailed Feedback */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
          📝 Detailed Analysis Report
        </h3>
        <div className="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-4 rounded-lg border">
          {analysis.feedback}
        </div>
        
        {analysis.analysis_timestamp && (
          <div className="mt-3 text-xs text-gray-500">
            Analysis completed: {new Date(analysis.analysis_timestamp).toLocaleString()}
          </div>
        )}
      </div>

      {/* Action Recommendations */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
          🎯 Next Steps
        </h3>
        <div className="space-y-2">
          {analysis.can_merge ? (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm font-medium text-green-800">
                ✅ This PR is ready to merge! All requirements have been met.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm font-medium text-yellow-800">
                  ⚠️ This PR needs attention before merging.
                </p>
              </div>
              <div className="text-sm text-gray-600">
                <p className="font-medium mb-1">Recommended actions:</p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  {analysis.completeness_score < 70 && (
                    <li>Address missing requirements listed above</li>
                  )}
                  {analysis.merge_blockers && analysis.merge_blockers.length > 0 && (
                    <li>Resolve all merge blockers</li>
                  )}
                  {analysis.code_quality_issues && analysis.code_quality_issues.length > 0 && (
                    <li>Fix code quality issues</li>
                  )}
                  <li>Review and implement suggestions</li>
                  <li>Run tests to ensure functionality</li>
                  <li>Request code review from team members</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnalysisResults; 