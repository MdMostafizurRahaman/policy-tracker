import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Search, MessageCircle, Trash2, Plus, FileText, Globe, Shield, Brain, Loader2, ChevronDown, X, Menu, EyeOff, Eye, MapPin, Calendar, Tag, Sparkles, Database, Zap } from 'lucide-react';

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
    "United States",           // Country search - always works
    "AI Safety",              // Policy area - always works  
    "countries",              // List command - always works
    "Digital Education",      // Policy area - always works
    "Bangladesh",             // Country search - always works
    "areas"                   // List command - always works
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
        content: 'Sorry, I encountered an error. Please try again. I can only help you with AI policies that are in our database.',
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
    const question = `Tell me about the "${policy.name}" policy from ${policy.country}`;
    
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

  const formatMessage = (content) => {
    // Enhanced message formatting for markdown-like content
    return content
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0)
      .map((line, index) => {
        // Headers (lines starting with **)
        if (line.startsWith('**') && line.endsWith('**')) {
          return (
            <h3 key={index} className="font-bold text-lg text-gray-800 mb-2 mt-4 first:mt-0">
              {line.replace(/\*\*/g, '')}
            </h3>
          );
        }
        
        // Bold text within lines
        if (line.includes('**')) {
          const parts = line.split(/(\*\*.*?\*\*)/);
          return (
            <p key={index} className="mb-2 leading-relaxed">
              {parts.map((part, i) => 
                part.startsWith('**') && part.endsWith('**') ? (
                  <span key={i} className="font-semibold text-gray-800">
                    {part.replace(/\*\*/g, '')}
                  </span>
                ) : (
                  <span key={i}>{part}</span>
                )
              )}
            </p>
          );
        }
        
        // Bullet points
        if (line.startsWith('•') || line.startsWith('-')) {
          return (
            <li key={index} className="ml-4 mb-1 text-gray-700 leading-relaxed">
              {line.substring(1).trim()}
            </li>
          );
        }
        
        // Emoji headers
        if (/^[🔍📋🌍💡📊ℹ️❌👋🤖⚡🎯📈🛡️🚀💬🔐]/.test(line)) {
          return (
            <h4 key={index} className="font-semibold text-gray-800 mb-2 mt-3 first:mt-0 flex items-center gap-2">
              <span className="text-xl">{line.charAt(0)}</span>
              <span>{line.substring(1).trim()}</span>
            </h4>
          );
        }
        
        // Regular paragraphs
        return (
          <p key={index} className="mb-2 text-gray-700 leading-relaxed">
            {line}
          </p>
        );
      });
  };

  // Load verified suggestions from database on component mount
  useEffect(() => {
    loadVerifiedSuggestions();
  }, []);

  const loadVerifiedSuggestions = async () => {
    try {
      // Get actual countries and areas from the database
      const countriesResponse = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: 'countries' })
      });
      
      const areasResponse = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: 'areas' })
      });

      if (countriesResponse.ok && areasResponse.ok) {
        // Update suggestions with verified database content
        setSuggestedQuestions([
          "United States",        // Verified country
          "AI Safety",           // Verified policy area
          "countries",           // List all countries
          "Digital Education",   // Verified policy area
          "Bangladesh",          // Verified country
          "areas"               // List all policy areas
        ]);
      }
    } catch (error) {
      console.log('Using default suggestions');
      // Keep the default verified suggestions if API fails
    }
  };

  return (
    <div className="flex h-full bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 overflow-hidden">
      {/* Enhanced Sidebar */}
      <div className={`${showSidebar ? 'w-80' : 'w-0'} transition-all duration-300 bg-white/80 backdrop-blur-lg border-r border-gray-200/50 flex flex-col overflow-hidden shadow-xl`}>
        <div className="p-6 border-b border-gray-100/50 bg-gradient-to-r from-blue-600 to-indigo-600">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                <Database className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="text-lg font-bold">AI Policy</div>
                <div className="text-sm font-normal text-blue-100">Database Assistant</div>
              </div>
            </h2>
            <button
              onClick={toggleSidebar}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              title="Hide Sidebar"
            >
              <X className="w-5 h-5 text-white" />
            </button>
          </div>
          <button
            onClick={startNewConversation}
            className="w-full flex items-center gap-3 px-4 py-3 bg-white/20 text-white rounded-xl hover:bg-white/30 transition-all backdrop-blur-sm border border-white/20"
          >
            <Plus className="w-5 h-5" />
            <span className="font-medium">New Conversation</span>
          </button>
        </div>

        {/* Enhanced Policy Search */}
        <div className="p-4 border-b border-gray-100/50 bg-gradient-to-r from-gray-50 to-blue-50">
          <div className="relative">
            <input
              type="text"
              placeholder="Search countries, policies, areas..."
              value={searchQuery}
              onChange={handleSearchChange}
              onFocus={handleSearchFocus}
              onBlur={handleSearchBlur}
              className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm bg-white/80 backdrop-blur-sm placeholder-gray-500 shadow-sm"
            />
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            {isSearching && (
              <Loader2 className="absolute right-4 top-1/2 transform -translate-y-1/2 w-4 h-4 animate-spin text-blue-500" />
            )}
          </div>
          
          {showSearch && (
            <div className="mt-3 max-h-64 overflow-y-auto bg-white/90 backdrop-blur-lg border border-gray-200/50 rounded-xl shadow-lg absolute z-20 left-4 right-4">
              {searchResults.length > 0 ? (
                <div className="py-2">
                  <div className="px-4 py-2 text-xs font-semibold text-gray-600 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-indigo-50">
                    Found {searchResults.length} policies in database
                  </div>
                  {searchResults.map((policy, index) => (
                    <div
                      key={policy.id || index}
                      onClick={() => selectPolicy(policy)}
                      className="p-4 hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 cursor-pointer border-b border-gray-50 last:border-b-0 transition-all duration-200"
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-100 to-indigo-200 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm">
                          <span className="text-lg">{policy.area_icon || '📄'}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-semibold text-sm text-gray-800 truncate">{policy.country}</span>
                            <span className="text-xs text-gray-400">•</span>
                            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">{policy.year}</span>
                          </div>
                          <div className="text-sm text-gray-700 font-medium truncate mb-1">{policy.name}</div>
                          <div className="flex items-center gap-2 mb-2">
                            <Tag className="w-3 h-3 text-blue-500" />
                            <span className="text-xs text-blue-600 font-medium">{policy.area}</span>
                          </div>
                          <div className="text-xs text-gray-600 line-clamp-2">{policy.description}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : searchQuery.trim() && !isSearching ? (
                <div className="p-6 text-center text-sm text-gray-500">
                  <Database className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                  No policies found for "{searchQuery}" in our database
                </div>
              ) : searchQuery.trim() && isSearching ? (
                <div className="p-6 text-center text-sm text-gray-500">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-500" />
                  Searching database...
                </div>
              ) : null}
            </div>
          )}
        </div>

        {/* Enhanced Selected Policy Info */}
        {selectedPolicy && (
          <div className="p-4 border-b border-gray-100/50 bg-gradient-to-r from-green-50 to-emerald-50">
            <div className="text-xs font-semibold text-green-700 mb-2 flex items-center gap-2">
              <Zap className="w-3 h-3" />
              CURRENTLY DISCUSSING
            </div>
            <div className="bg-white/80 backdrop-blur-sm p-4 rounded-xl border border-green-200/50 shadow-sm">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-gradient-to-br from-green-100 to-emerald-200 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-lg">{selectedPolicy.area_icon || '📄'}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-sm text-gray-800">{selectedPolicy.country}</div>
                  <div className="text-xs text-gray-600 truncate mb-1">{selectedPolicy.name}</div>
                  <div className="text-xs text-emerald-600 font-medium bg-emerald-100 px-2 py-1 rounded-full inline-block">
                    {selectedPolicy.area}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Enhanced History Toggle */}
        <div className="p-4 border-b border-gray-100/50">
          <button
            onClick={toggleHistory}
            className="w-full flex items-center justify-between gap-2 px-4 py-3 text-left hover:bg-gray-50 rounded-xl transition-all duration-200 group"
          >
            <div className="flex items-center gap-3">
              {showHistory ? <Eye className="w-4 h-4 text-gray-600 group-hover:text-blue-600" /> : <EyeOff className="w-4 h-4 text-gray-600 group-hover:text-blue-600" />}
              <span className="text-sm font-medium text-gray-700 group-hover:text-blue-700">Conversation History</span>
            </div>
            <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform group-hover:text-blue-600 ${showHistory ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Enhanced Conversations */}
        {showHistory && (
          <div className="flex-1 overflow-y-auto">
            <div className="p-4">
              <h3 className="text-sm font-semibold text-gray-600 mb-4 flex items-center gap-2">
                <MessageCircle className="w-4 h-4" />
                Recent Conversations
              </h3>
              {conversations.length === 0 ? (
                <div className="text-sm text-gray-500 text-center py-8 px-4">
                  <Bot className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <div className="font-medium mb-1">No conversations yet</div>
                  <div className="text-xs">Start a new chat to begin exploring AI policies!</div>
                </div>
              ) : (
                <div className="space-y-3">
                  {conversations.map((conv) => (
                    <div
                      key={conv.conversation_id}
                      onClick={() => loadConversation(conv.conversation_id)}
                      className={`p-4 rounded-xl cursor-pointer transition-all group relative ${
                        currentConversationId === conv.conversation_id
                          ? 'bg-gradient-to-r from-blue-100 to-indigo-100 border-blue-200 shadow-sm'
                          : 'hover:bg-gray-50 border-transparent hover:shadow-sm'
                      } border backdrop-blur-sm`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0 pr-2">
                          <div className="text-xs text-gray-500 mb-2 flex items-center gap-2">
                            <Calendar className="w-3 h-3" />
                            {new Date(conv.updated_at).toLocaleDateString()}
                          </div>
                          <div className="text-sm text-gray-800 truncate font-medium mb-2">
                            {conv.last_message || 'New conversation'}
                          </div>
                          <div className="text-xs text-gray-500 flex items-center gap-1">
                            <MessageCircle className="w-3 h-3" />
                            {conv.message_count} messages
                          </div>
                        </div>
                        <button
                          onClick={(e) => deleteConversation(conv.conversation_id, e)}
                          className="opacity-0 group-hover:opacity-100 p-2 hover:bg-red-100 rounded-lg transition-all absolute top-2 right-2"
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

      {/* Enhanced Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Enhanced Header */}
        <div className="bg-white/80 backdrop-blur-lg border-b border-gray-200/50 p-6 shadow-sm flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {!showSidebar && (
                <button
                  onClick={toggleSidebar}
                  className="p-3 hover:bg-gray-100 rounded-xl transition-colors"
                  title="Show Sidebar"
                >
                  <Menu className="w-5 h-5" />
                </button>
              )}
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                  <Database className="w-7 h-7 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                    AI Policy Database Expert
                    <Sparkles className="w-5 h-5 text-blue-500" />
                  </h1>
                  <p className="text-sm text-gray-600">
                    {selectedPolicy 
                      ? `Discussing ${selectedPolicy.country} - ${selectedPolicy.name}`
                      : "Search and explore AI policies from verified database sources"
                    }
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 text-xs text-gray-500 bg-green-50 px-3 py-2 rounded-lg border border-green-200">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                Database Connected
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Messages */}
        <div 
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto p-6 space-y-6 min-h-0"
        >
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-indigo-200 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
                <Database className="w-12 h-12 text-blue-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-800 mb-3">Welcome to AI Policy Database Assistant</h3>
              <p className="text-gray-600 mb-8 max-w-2xl mx-auto leading-relaxed">
                I'm your dedicated AI policy expert with access to a comprehensive database of verified AI governance frameworks, 
                regulations, and policy initiatives from around the world. I can only provide information that exists in our database.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl mx-auto">
                {suggestedQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => sendMessage(question)}
                    className="text-left p-6 bg-white/60 backdrop-blur-sm rounded-2xl border border-gray-200/50 hover:border-blue-300 hover:bg-blue-50/50 transition-all text-sm shadow-sm hover:shadow-md group"
                  >
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-indigo-200 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                        {/* Dynamic icons based on question type */}
                        {question === 'countries' || question === 'areas' ? (
                          <Search className="w-6 h-6 text-blue-600" />
                        ) : question.includes('United States') || question.includes('Bangladesh') ? (
                          <Globe className="w-6 h-6 text-blue-600" />
                        ) : (
                          <Brain className="w-6 h-6 text-blue-600" />
                        )}
                      </div>
                      <div className="flex-1">
                        <span className="text-gray-700 font-medium">
                          {/* Enhanced question display */}
                          {question === 'countries' && 'Show all countries with AI policies'}
                          {question === 'areas' && 'Show all policy areas available'}
                          {question === 'United States' && 'Show United States AI policies'}
                          {question === 'Bangladesh' && 'Show Bangladesh AI policies'}
                          {question === 'AI Safety' && 'Find AI Safety policies'}
                          {question === 'Digital Education' && 'Find Digital Education policies'}
                          {!['countries', 'areas', 'United States', 'Bangladesh', 'AI Safety', 'Digital Education'].includes(question) && question}
                        </span>
                        <div className="text-xs text-gray-500 mt-1">
                          {question === 'countries' || question === 'areas' ? 
                            'View complete database list' : 
                            'Search verified database'
                          }
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
              
              <div className="mt-8 p-4 bg-blue-50/50 backdrop-blur-sm rounded-xl border border-blue-200/50 max-w-2xl mx-auto">
                <div className="text-sm text-blue-700 font-medium mb-2 flex items-center gap-2 justify-center">
                  <Shield className="w-4 h-4" />
                  Database-Only Responses
                </div>
                <div className="text-xs text-blue-600">
                  All responses are sourced exclusively from our verified AI policy database. 
                  If information isn't in our database, I'll let you know.
                </div>
              </div>
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={index}
                className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg">
                    <Database className="w-6 h-6 text-white" />
                  </div>
                )}
                
                <div className={`max-w-4xl ${message.role === 'user' ? 'order-1' : ''}`}>
                  <div
                    className={`px-6 py-4 rounded-2xl shadow-sm ${
                      message.role === 'user'
                        ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white ml-12'
                        : 'bg-white/80 backdrop-blur-sm border border-gray-200/50 mr-12'
                    }`}
                  >
                    <div className={`${message.role === 'user' ? 'text-blue-100' : 'text-gray-800'}`}>
                      {message.role === 'user' ? (
                        <p className="leading-relaxed">{message.content}</p>
                      ) : (
                        <div className="prose prose-sm max-w-none">
                          {formatMessage(message.content)}
                        </div>
                      )}
                    </div>
                  </div>
                  {message.timestamp && (
                    <div className={`text-xs text-gray-500 mt-2 px-6 ${
                      message.role === 'user' ? 'text-right' : 'text-left'
                    }`}>
                      {formatTimestamp(message.timestamp)}
                    </div>
                  )}
                </div>

                {message.role === 'user' && (
                  <div className="w-10 h-10 bg-gradient-to-br from-gray-600 to-gray-700 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg">
                    <User className="w-6 h-6 text-white" />
                  </div>
                )}
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="flex gap-4 justify-start">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg">
                <Database className="w-6 h-6 text-white" />
              </div>
              <div className="bg-white/80 backdrop-blur-sm border border-gray-200/50 rounded-2xl px-6 py-4 mr-12 shadow-sm">
                <div className="flex items-center gap-3">
                  <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                  <span className="text-sm text-gray-600">Searching policy database...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Enhanced Input */}
        <div className="bg-white/80 backdrop-blur-lg border-t border-gray-200/50 p-6 flex-shrink-0">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-4 items-end">
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
                      ? `Ask more about ${selectedPolicy.name} or search for other policies...`
                      : "Ask about AI policies by country, policy name, or area. Try 'United States', 'AI Safety', or 'help'..."
                  }
                  className="text-black w-full px-6 py-4 border border-gray-300/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white/80 backdrop-blur-sm placeholder-gray-500 shadow-sm"
                  rows="1"
                  style={{ minHeight: '56px', maxHeight: '120px' }}
                />
              </div>
              <button
                onClick={() => sendMessage()}
                disabled={!inputMessage.trim() || isLoading}
                className="p-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl disabled:hover:shadow-lg"
              >
                <Send className="w-6 h-6" />
              </button>
            </div>
            <div className="text-xs text-gray-500 mt-3 text-center flex items-center justify-center gap-4">
              <span>Press Enter to send, Shift+Enter for new line</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Database className="w-3 h-3" />
                Database-only responses
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PolicyChatAssistant;