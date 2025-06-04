import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Search, MessageCircle, Trash2, Plus, FileText, Globe, Shield, Brain, Loader2, ChevronDown, X, Menu, EyeOff, Eye, MapPin, Calendar, Tag } from 'lucide-react';

const PolicyChatAssistant = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showHistory, setShowHistory] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSearch, setShowSearch] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState([
    "What are the latest AI governance frameworks?",
    "Compare AI policies between USA and EU",
    "Tell me about AI safety regulations",
    "What are the key principles of responsible AI?",
    "How do countries approach AI ethics?",
    "What are AI policy implementation challenges?"
  ]);
  
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const searchTimeoutRef = useRef(null);

  // Mock API base URL - replace with your actual API URL
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://policy-tracker-5.onrender.com/api';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/conversations`);
      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations || []);
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  const loadConversation = async (conversationId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/conversation/${conversationId}`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
        setCurrentConversationId(conversationId);
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };

  const sendMessage = async (messageText = inputMessage, policyContext = null) => {
    if (!messageText.trim() || isLoading) return;

    const userMessage = {
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const requestBody = {
        message: messageText,
        conversation_id: currentConversationId
      };

      // Add policy context if provided (when user clicks on a search result)
      if (policyContext) {
        requestBody.context = `Based on the following policy information: ${JSON.stringify(policyContext)}`;
      }

      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        const data = await response.json();
        
        const assistantMessage = {
          role: 'assistant',
          content: data.response,
          timestamp: data.timestamp
        };

        setMessages(prev => [...prev, assistantMessage]);
        setCurrentConversationId(data.conversation_id);
        
        // Refresh conversations list
        loadConversations();
      } else {
        throw new Error('Failed to send message');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const startNewConversation = () => {
    setMessages([]);
    setCurrentConversationId(null);
    setSelectedPolicy(null);
  };

  const deleteConversation = async (conversationId, event) => {
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this conversation?')) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/chat/conversation/${conversationId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        if (currentConversationId === conversationId) {
          startNewConversation();
        }
        loadConversations();
      } else {
        console.error('Failed to delete conversation');
        alert('Failed to delete conversation. Please try again.');
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
      alert('Error deleting conversation. Please try again.');
    }
  };

  const searchPolicies = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat/policy-search?q=${encodeURIComponent(query)}`);
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.policies || []);
      } else {
        setSearchResults([]);
      }
    } catch (error) {
      console.error('Error searching policies:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    // Debounce search
    searchTimeoutRef.current = setTimeout(() => {
      searchPolicies(query);
    }, 300);
  };

  const selectPolicy = async (policy) => {
    setSelectedPolicy(policy);
    setShowSearch(false);
    setSearchQuery('');
    setSearchResults([]);
    
    // Create a comprehensive question about the selected policy
    const question = `Please provide comprehensive information about the "${policy.name}" policy from ${policy.country}. Include details about its key features, implementation strategies, objectives, governance framework, and any other relevant information available in the database.`;
    
    // Send message with policy context for better AI response
    await sendMessage(question, policy);
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const toggleSidebar = () => {
    setShowSidebar(!showSidebar);
  };

  const toggleHistory = () => {
    setShowHistory(!showHistory);
  };

  const handleSearchFocus = () => {
    setShowSearch(true);
  };

  const handleSearchBlur = () => {
    // Delay hiding to allow clicking on results
    setTimeout(() => setShowSearch(false), 200);
  };

  return (
    <div className="flex h-full bg-gradient-to-br from-slate-50 to-blue-50 overflow-hidden">
      {/* Sidebar */}
      <div className={`${showSidebar ? 'w-80' : 'w-0'} transition-all duration-300 bg-white border-r border-gray-200 flex flex-col overflow-hidden shadow-lg`}>
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <Bot className="w-6 h-6 text-blue-600" />
              Policy Assistant
            </h2>
            <button
              onClick={toggleSidebar}
              className="p-1 hover:bg-gray-100 rounded-md transition-colors"
              title="Hide Sidebar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <button
            onClick={startNewConversation}
            className="w-full flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Conversation
          </button>
        </div>

        {/* Global Policy Search */}
        <div className="p-4 border-b border-gray-100">
          <div className="relative">
            <input
              type="text"
              placeholder="Search countries, policies, or areas..."
              value={searchQuery}
              onChange={handleSearchChange}
              onFocus={handleSearchFocus}
              onBlur={handleSearchBlur}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
            {isSearching && (
              <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 animate-spin text-gray-400" />
            )}
          </div>
          
          {showSearch && (
            <div className="mt-2 max-h-64 overflow-y-auto bg-white border border-gray-200 rounded-lg shadow-lg absolute z-20 left-4 right-4">
              {searchResults.length > 0 ? (
                <div className="py-2">
                  <div className="px-3 py-1 text-xs font-semibold text-gray-500 border-b border-gray-100">
                    Found {searchResults.length} policies
                  </div>
                  {searchResults.map((policy, index) => (
                    <div
                      key={policy.id || index}
                      onClick={() => selectPolicy(policy)}
                      className="p-3 hover:bg-blue-50 cursor-pointer border-b border-gray-50 last:border-b-0 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full flex items-center justify-center flex-shrink-0">
                          <Globe className="w-4 h-4 text-blue-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-sm text-gray-800 truncate">{policy.country}</span>
                            <span className="text-xs text-gray-500">•</span>
                            <span className="text-xs text-gray-500">{policy.year}</span>
                          </div>
                          <div className="text-sm text-gray-700 font-medium truncate mb-1">{policy.name}</div>
                          <div className="flex items-center gap-2 mb-1">
                            <Tag className="w-3 h-3 text-gray-400" />
                            <span className="text-xs text-gray-500">{policy.area}</span>
                          </div>
                          <div className="text-xs text-gray-600 line-clamp-2">{policy.description}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : searchQuery.trim() && !isSearching ? (
                <div className="p-4 text-center text-sm text-gray-500">
                  No policies found for "{searchQuery}"
                </div>
              ) : searchQuery.trim() && isSearching ? (
                <div className="p-4 text-center text-sm text-gray-500">
                  <Loader2 className="w-4 h-4 animate-spin mx-auto mb-2" />
                  Searching...
                </div>
              ) : null}
            </div>
          )}
        </div>

        {/* Selected Policy Info */}
        {selectedPolicy && (
          <div className="p-4 border-b border-gray-100 bg-blue-50">
            <div className="text-xs font-semibold text-blue-600 mb-2">CURRENTLY DISCUSSING</div>
            <div className="bg-white p-3 rounded-lg border border-blue-200">
              <div className="flex items-start gap-2">
                <Globe className="w-4 h-4 text-blue-600 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm text-gray-800">{selectedPolicy.country}</div>
                  <div className="text-xs text-gray-600 truncate">{selectedPolicy.name}</div>
                  <div className="text-xs text-blue-600 mt-1">{selectedPolicy.area}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* History Toggle */}
        <div className="p-4 border-b border-gray-100">
          <button
            onClick={toggleHistory}
            className="w-full flex items-center justify-between gap-2 px-3 py-2 text-left hover:bg-gray-50 rounded-lg transition-colors"
          >
            <div className="flex items-center gap-2">
              {showHistory ? <Eye className="w-4 h-4 text-gray-600" /> : <EyeOff className="w-4 h-4 text-gray-600" />}
              <span className="text-sm font-medium text-gray-700">Conversation History</span>
            </div>
            <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform ${showHistory ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Conversations */}
        {showHistory && (
          <div className="flex-1 overflow-y-auto">
            <div className="p-4">
              <h3 className="text-sm font-semibold text-gray-600 mb-3">Recent Conversations</h3>
              {conversations.length === 0 ? (
                <div className="text-sm text-gray-500 text-center py-8">
                  No conversations yet.<br />Start a new chat to begin!
                </div>
              ) : (
                <div className="space-y-2">
                  {conversations.map((conv) => (
                    <div
                      key={conv.conversation_id}
                      onClick={() => loadConversation(conv.conversation_id)}
                      className={`p-3 rounded-lg cursor-pointer transition-all group relative ${
                        currentConversationId === conv.conversation_id
                          ? 'bg-blue-100 border-blue-200'
                          : 'hover:bg-gray-50 border-transparent'
                      } border`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0 pr-2">
                          <div className="text-xs text-gray-500 mb-1">
                            {new Date(conv.updated_at).toLocaleDateString()}
                          </div>
                          <div className="text-sm text-gray-800 truncate">
                            {conv.last_message || 'New conversation'}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {conv.message_count} messages
                          </div>
                        </div>
                        <button
                          onClick={(e) => deleteConversation(conv.conversation_id, e)}
                          className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded transition-all absolute top-2 right-2"
                          title="Delete conversation"
                        >
                          <Trash2 className="w-4 h-4 text-red-600" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-4 shadow-sm flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {!showSidebar && (
                <button
                  onClick={toggleSidebar}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  title="Show Sidebar"
                >
                  <Menu className="w-5 h-5" />
                </button>
              )}
              <div>
                <h1 className="text-xl font-bold text-gray-800">AI Policy Expert</h1>
                <p className="text-sm text-gray-600">
                  {selectedPolicy 
                    ? `Discussing ${selectedPolicy.country} - ${selectedPolicy.name}`
                    : "Ask me about AI policies and regulations worldwide"
                  }
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                Online
              </div>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div 
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0"
        >
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Bot className="w-10 h-10 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">Welcome to AI Policy Assistant</h3>
              <p className="text-gray-600 mb-6 max-w-md mx-auto">
                Search for any country or policy in the sidebar, or ask me about AI governance frameworks and regulations worldwide.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                {suggestedQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => sendMessage(question)}
                    className="text-left p-4 bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all text-sm"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                        {index < 3 ? <FileText className="w-4 h-4 text-blue-600" /> : 
                         index < 5 ? <Globe className="w-4 h-4 text-blue-600" /> : 
                         <Brain className="w-4 h-4 text-blue-600" />}
                      </div>
                      <span className="text-gray-700">{question}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={index}
                className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}
                
                <div className={`max-w-3xl ${message.role === 'user' ? 'order-1' : ''}`}>
                  <div
                    className={`px-4 py-3 rounded-2xl ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white ml-12'
                        : 'bg-white border border-gray-200 mr-12'
                    }`}
                  >
                    <div className={`text-sm ${message.role === 'user' ? 'text-blue-100' : 'text-gray-800'}`}>
                      {message.content.split('\n').map((line, i) => (
                        <p key={i} className={i > 0 ? 'mt-2' : ''}>
                          {line}
                        </p>
                      ))}
                    </div>
                  </div>
                  {message.timestamp && (
                    <div className={`text-xs text-gray-500 mt-1 px-4 ${
                      message.role === 'user' ? 'text-right' : 'text-left'
                    }`}>
                      {formatTimestamp(message.timestamp)}
                    </div>
                  )}
                </div>

                {message.role === 'user' && (
                  <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <User className="w-5 h-5 text-white" />
                  </div>
                )}
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 mr-12">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  <span className="text-sm text-gray-600">Analyzing policy data...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="bg-white border-t border-gray-200 p-4 flex-shrink-0">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3 items-end">
              <div className="flex-1 relative">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage();
                    }
                  }}
                  placeholder={
                    selectedPolicy 
                      ? `Ask more about ${selectedPolicy.name} or any other policy question...`
                      : "Ask me about AI policies, governance frameworks, or search for specific policies in the sidebar..."
                  }
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows="1"
                  style={{ minHeight: '48px', maxHeight: '120px' }}
                />
              </div>
              <button
                onClick={() => sendMessage()}
                disabled={!inputMessage.trim() || isLoading}
                className="p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            <div className="text-xs text-gray-500 mt-2 text-center">
              Press Enter to send, Shift+Enter for new line • Search policies in the sidebar
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PolicyChatAssistant;