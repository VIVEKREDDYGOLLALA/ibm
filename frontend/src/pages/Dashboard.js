import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import api from '../api/api';
import JiraTicketList from '../components/JiraTicketList';
import ImplementationPlanModal from '../components/ImplementationPlanModal';
import PRValidationForm from '../components/PRValidationForm';
import AnalysisResults from '../components/AnalysisResults';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('tickets');
  const [jiraTickets, setJiraTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [graniteTestResult, setGraniteTestResult] = useState(null);

  useEffect(() => {
    fetchJiraTickets();
  }, []);

  const fetchJiraTickets = async () => {
    setLoading(true);
    try {
      // First, get available projects
      const projectsResponse = await api.getJiraProjects();
      console.log('Available projects:', projectsResponse.data.projects);
      
      if (projectsResponse.data.projects.length > 0) {
        // Use the first available project
        const firstProject = projectsResponse.data.projects[0];
        const projectKey = firstProject.key;
        
        toast.info(`Loading tickets from project: ${projectKey}`);
        
        const response = await api.getJiraIssues(projectKey);
        setJiraTickets(response.data.issues);
        if (response.data.issues.length > 0) {
          toast.success(`Loaded ${response.data.issues.length} tickets from ${projectKey} successfully!`);
        } else {
          toast.info(`No tickets found in ${projectKey} project`);
        }
      } else {
        toast.warning('No Jira projects found. Please check your Jira configuration.');
        setJiraTickets([]);
      }
    } catch (error) {
      toast.error('Failed to fetch Jira tickets. Please check your configuration.');
      console.error('Jira fetch error:', error);
      setJiraTickets([]);
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePlan = async (ticket, repoUrl) => {
    setLoading(true);
    try {
      console.log('🎯 Generating plan for ticket:', ticket.key);
      console.log('🔗 Repository URL:', repoUrl);
      console.log('📋 Ticket data:', ticket);
      
      const response = await api.generateImplementationPlan({
        issue_key: ticket.key,
        github_url: repoUrl
      });
      
      console.log('📋 Full API Response:', response);
      console.log('📋 Response data:', response.data);
      console.log('📋 Response status:', response.status);
      
      // Extract the implementation plan from the response
      const implementationPlan = response.data.implementation_plan || response.data.analysis || 'No plan generated';
      
      console.log('📝 Extracted implementation plan:', implementationPlan);
      console.log('📝 Plan length:', implementationPlan.length);
      console.log('📝 Plan type:', typeof implementationPlan);
      
      if (!implementationPlan || implementationPlan === 'No plan generated') {
        console.error('❌ No valid implementation plan found in response');
        console.log('Available response keys:', Object.keys(response.data));
        toast.error('No implementation plan was generated. Please try again.');
        return;
      }
      
      const ticketWithPlan = { 
        ...ticket, 
        plan: implementationPlan, 
        pdf_url: response.data.pdf_url 
      };
      
      console.log('📋 Setting selected ticket:', ticketWithPlan);
      console.log('📋 Plan in ticket:', ticketWithPlan.plan);
      
      toast.success('Implementation plan generated successfully!');
      setSelectedTicket(ticketWithPlan);
      setShowPlanModal(true);
      
      console.log('✅ Modal should be showing now');
      
    } catch (error) {
      console.error('❌ Implementation plan generation error:', error);
      console.error('❌ Error response:', error.response?.data);
      console.error('❌ Error status:', error.response?.status);
      
      // More specific error messages
      let errorMessage = 'Failed to generate implementation plan.';
      
      if (error.response?.status === 500) {
        const errorData = error.response?.data;
        if (errorData?.error?.includes('empty response from AI')) {
          errorMessage = 'IBM Granite AI did not respond. Please check your API configuration and quota limits.';
        } else if (errorData?.error?.includes('Bearer token')) {
          errorMessage = 'IBM API authentication failed. Please check your API key.';
        } else {
          errorMessage = `Server error: ${errorData?.error || 'Unknown error'}`;
        }
      } else if (error.response?.status === 400) {
        errorMessage = 'Invalid request. Please check your ticket and repository URL.';
      } else if (error.code === 'NETWORK_ERROR' || error.message?.includes('Network Error')) {
        errorMessage = 'Network error. Please check if the backend server is running.';
      }
      
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleValidatePR = async (formData) => {
    setLoading(true);
    try {
      console.log('🔍 Starting PR validation...', formData);
      const response = await api.validatePR(formData);
      
      console.log('📋 PR Validation Response:', response.data);
      
      if (response.data.analysis) {
        setAnalysisResults(response.data.analysis);
        
        // Show success message with merge recommendation
        const canMerge = response.data.analysis.can_merge;
        const completenessScore = response.data.analysis.completeness_score;
        
        if (canMerge) {
          toast.success(`🎉 PR analysis complete! Ready to merge (${completenessScore}% complete)`);
        } else if (completenessScore >= 70) {
          toast.warning(`⚠️ PR analysis complete! Needs minor improvements (${completenessScore}% complete)`);
        } else {
          toast.error(`❌ PR analysis complete! Major changes required (${completenessScore}% complete)`);
        }
        
        setActiveTab('analysis');
      } else {
        toast.error('PR validation completed but no analysis data received.');
        console.error('No analysis data in response:', response.data);
      }
    } catch (error) {
      console.error('❌ PR validation error:', error);
      console.error('❌ Error response:', error.response?.data);
      console.error('❌ Error status:', error.response?.status);
      
      // More specific error messages
      let errorMessage = 'Failed to validate PR.';
      
      if (error.response?.status === 404) {
        errorMessage = 'Jira issue not found. Please check the issue key.';
      } else if (error.response?.status === 400) {
        const errorData = error.response?.data;
        if (errorData?.detail?.includes('GitHub PR URL')) {
          errorMessage = 'Invalid GitHub PR URL format. Please check the URL.';
        } else {
          errorMessage = 'Invalid request. Please check your inputs.';
        }
      } else if (error.response?.status === 500) {
        const errorData = error.response?.data;
        if (errorData?.detail?.includes('GitHub')) {
          errorMessage = 'Failed to fetch PR from GitHub. Check if the repository is accessible.';
        } else if (errorData?.detail?.includes('Granite')) {
          errorMessage = 'AI analysis failed. Please try again or check IBM Granite configuration.';
        } else {
          errorMessage = `Server error: ${errorData?.detail || 'Unknown error'}`;
        }
      } else if (error.code === 'NETWORK_ERROR' || error.message?.includes('Network Error')) {
        errorMessage = 'Network error. Please check if the backend server is running.';
      }
      
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleTestGranite = async () => {
    setLoading(true);
    try {
      console.log('🧪 Testing IBM Granite connection...');
      const response = await api.testGraniteConnection();
      
      setGraniteTestResult(response.data);
      
      if (response.data.connection_test?.status === 'success') {
        toast.success('IBM Granite connection test successful!');
      } else {
        toast.error(`IBM Granite test failed: ${response.data.connection_test?.message || 'Unknown error'}`);
      }
      
      console.log('🧪 Granite test result:', response.data);
    } catch (error) {
      console.error('❌ Granite test error:', error);
      toast.error('Failed to test IBM Granite connection. Check console for details.');
      setGraniteTestResult({
        connection_test: {
          status: 'error',
          message: error.response?.data?.detail || error.message
        }
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTestPRValidation = async () => {
    setLoading(true);
    try {
      console.log('🧪 Testing PR validation functionality...');
      const response = await api.testPRValidation({
        jira_issue_key: 'TEST-123',
        pr_url: 'https://github.com/octocat/Hello-World/pull/1'
      });
      
      console.log('🧪 PR validation test result:', response.data);
      
      if (response.data.status === 'success' && response.data.result?.success) {
        setAnalysisResults(response.data.result.analysis);
        toast.success('PR validation test successful! Check the analysis results.');
        setActiveTab('analysis');
      } else {
        toast.error(`PR validation test failed: ${response.data.result?.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('❌ PR validation test error:', error);
      toast.error('Failed to test PR validation. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  const handleTestVisionAnalysis = async () => {
    setLoading(true);
    try {
      console.log('🧪 Testing Vision AI...');
      const response = await api.testSimpleGeneration({
        prompt: "Analyze this image and provide insights.",
        task_type: "vision_analysis"
      });
      
      console.log('🧪 Vision AI test result:', response.data);
      
      if (response.data.status === 'success') {
        toast.success('Vision AI test successful!');
      } else {
        toast.error(`Vision AI test failed: ${response.data.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('❌ Vision AI test error:', error);
      toast.error('Failed to test Vision AI. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header Section */}
      <div className="text-center mb-12 animate-fade-in">
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-4">
            AI-Powered Developer Dashboard
          </h1>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Streamline your development workflow with AI-powered implementation plans, 
            intelligent code analysis, and seamless GitHub-Jira integration.
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="glass card-hover rounded-xl p-6 animate-slide-up animate-delay-100">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-xl font-bold text-gray-800 mb-2">IBM Granite AI</h3>
            <p className="text-gray-600 text-sm">Advanced AI analysis with 128k context capacity for detailed implementation plans</p>
          </div>
          
          <div className="glass card-hover rounded-xl p-6 animate-slide-up animate-delay-200">
            <div className="text-4xl mb-4">🔍</div>
            <h3 className="text-xl font-bold text-gray-800 mb-2">Smart Analysis</h3>
            <p className="text-gray-600 text-sm">Intelligent repository scanning with focused file detection and priority-based suggestions</p>
          </div>
          
          <div className="glass card-hover rounded-xl p-6 animate-slide-up animate-delay-300">
            <div className="text-4xl mb-4">⚡</div>
            <h3 className="text-xl font-bold text-gray-800 mb-2">Fast & Reliable</h3>
            <p className="text-gray-600 text-sm">Optimized performance with enhanced retry logic and connection reliability</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap justify-center gap-3 animate-slide-up animate-delay-400">
          <button
            onClick={handleTestGranite}
            disabled={loading}
            className="px-6 py-3 btn-gradient text-white rounded-lg font-medium shadow-lg disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center space-x-2"
          >
            <span>🧪</span>
            <span>{loading ? 'Testing...' : 'Test Granite'}</span>
          </button>
          <button
            onClick={handleTestPRValidation}
            disabled={loading}
            className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-lg font-medium shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 hover:transform hover:scale-105 inline-flex items-center space-x-2"
          >
            <span>🔍</span>
            <span>{loading ? 'Testing...' : 'Test PR Analysis'}</span>
          </button>
          <button
            onClick={handleTestVisionAnalysis}
            disabled={loading}
            className="px-6 py-3 bg-gradient-to-r from-green-500 to-teal-500 hover:from-green-600 hover:to-teal-600 text-white rounded-lg font-medium shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 hover:transform hover:scale-105 inline-flex items-center space-x-2"
          >
            <span>👁️</span>
            <span>{loading ? 'Testing...' : 'Test Vision AI'}</span>
          </button>
        </div>
      </div>

      {/* IBM Granite Test Results */}
      {graniteTestResult && (
        <div className="mb-8 glass rounded-xl p-6 animate-slide-up">
          <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
            <span className="mr-2">🧪</span>
            IBM Granite Connection Test Results
          </h3>
          <div className="space-y-3">
            <div className={`p-3 rounded-lg border ${graniteTestResult.connection_test?.status === 'success' ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
              <strong>Connection:</strong> {graniteTestResult.connection_test?.status} - {graniteTestResult.connection_test?.message}
            </div>
            {graniteTestResult.simple_generation_test && (
              <div className={`p-3 rounded-lg border ${graniteTestResult.simple_generation_test?.success ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                <strong>Text Generation:</strong> {graniteTestResult.simple_generation_test?.success ? 'Success' : 'Failed'}
                {graniteTestResult.simple_generation_test?.response && (
                  <div className="mt-1 text-sm">Response: "{graniteTestResult.simple_generation_test.response}"</div>
                )}
              </div>
            )}
            <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
              <strong>Configuration:</strong> 
              API Key: {graniteTestResult.configuration_status?.api_key_configured ? '✅ Configured' : '❌ Missing'} | 
              Project ID: {graniteTestResult.configuration_status?.project_id_configured ? '✅ Configured' : '❌ Missing'}
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="glass rounded-xl p-1 mb-8 animate-slide-up">
        <nav className="flex space-x-1">
          <button
            onClick={() => setActiveTab('tickets')}
            className={`${
              activeTab === 'tickets'
                ? 'bg-white text-blue-600 shadow-md'
                : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
            } px-6 py-3 rounded-lg font-medium text-sm transition-all duration-200 flex-1`}
          >
            📋 Jira Tickets
          </button>
          <button
            onClick={() => setActiveTab('validation')}
            className={`${
              activeTab === 'validation'
                ? 'bg-white text-purple-600 shadow-md'
                : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
            } px-6 py-3 rounded-lg font-medium text-sm transition-all duration-200 flex-1`}
          >
            🔍 PR Validation
          </button>
          {analysisResults && (
            <button
              onClick={() => setActiveTab('analysis')}
              className={`${
                activeTab === 'analysis'
                  ? 'bg-white text-green-600 shadow-md'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
              } px-6 py-3 rounded-lg font-medium text-sm transition-all duration-200 flex-1`}
            >
              📊 Analysis Results
            </button>
          )}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="animate-fade-in">
        {activeTab === 'tickets' && (
          <JiraTicketList
            tickets={jiraTickets}
            loading={loading}
            onGeneratePlan={handleGeneratePlan}
            onRefresh={fetchJiraTickets}
          />
        )}

        {activeTab === 'validation' && (
          <PRValidationForm
            onSubmit={handleValidatePR}
            loading={loading}
          />
        )}

        {activeTab === 'analysis' && analysisResults && (
          <AnalysisResults analysis={analysisResults} />
        )}
      </div>

      {/* Implementation Plan Modal */}
      {showPlanModal && selectedTicket && (
        <ImplementationPlanModal
          ticket={selectedTicket}
          onClose={() => {
            console.log('🚪 Closing implementation plan modal');
            setShowPlanModal(false);
            setSelectedTicket(null);
          }}
        />
      )}
    </div>
  );
};

export default Dashboard; 