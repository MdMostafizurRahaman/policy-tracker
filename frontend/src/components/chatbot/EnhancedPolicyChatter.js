import React, { useState, useEffect, useRef } from 'react';
import { Send, MessageCircle, Search, Trash2, Plus, Globe, BookOpen, Users, BarChart3, Sparkles, ExternalLink } from 'lucide-react';

const EnhancedPolicyChatter = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [suggestedQuestions, setSuggestedQuestions] = useState([
    "Tell me about AI policies in the United States",
    "Compare AI safety policies between different countries",
    "What are the main AI policy areas we have data for?",
    "Show me policies related to Digital Education",
    "Which countries have the most comprehensive AI policies?",
    "What's the difference between European and Asian AI approaches?"
  ]);
  
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const searchTimeoutRef = useRef(null);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://policy-tracker-platform-backend.onrender.com/api';
  const FRONTEND_URL = process.env.NEXT_PUBLIC_FRONTEND_URL || 'http://localhost:3000';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadConversations();
    // Add welcome message
    setMessages([{
      role: 'assistant',
      content: '👋 Hello! I\'m your AI Policy Expert Assistant. I have access to comprehensive AI policy data from around the world. I can help you:\n\n🌍 **Explore policies by country**\n📋 **Compare different policy approaches**\n🎯 **Find specific policy areas**\n📊 **Analyze policy trends**\n\nWhat would you like to discover today?',
      timestamp: new Date(),
      id: 'welcome'
    }]);
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

  const sendMessage = async (messageText = inputMessage, isQuickQuestion = false) => {
    if (!messageText.trim()) return;

    const userMessage = {
      role: 'user',
      content: messageText,
      timestamp: new Date(),
      id: Date.now().toString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          conversation_id: currentConversationId
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        const assistantMessage = {
          role: 'assistant',
          content: data.message,
          timestamp: new Date(),
          id: (Date.now() + 1).toString()
        };

        setMessages(prev => [...prev, assistantMessage]);
        
        if (data.conversation_id && data.conversation_id !== currentConversationId) {
          setCurrentConversationId(data.conversation_id);
          await loadConversations();
        }
      } else {
        throw new Error('Failed to send message');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        role: 'assistant',
        content: '❌ I apologize, but I\'m experiencing some technical difficulties. Please try again in a moment.',
        timestamp: new Date(),
        id: (Date.now() + 1).toString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const startNewConversation = () => {
    setMessages([{
      role: 'assistant',
      content: '🎉 New conversation started! I\'m here to help you explore AI policies from around the world. What would you like to learn about?',
      timestamp: new Date(),
      id: 'new_conversation'
    }]);
    setCurrentConversationId(null);
  };

  const deleteConversation = async (conversationId, event) => {
    event.stopPropagation();
    try {
      const response = await fetch(`${API_BASE_URL}/chat/conversation/${conversationId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        await loadConversations();
        if (currentConversationId === conversationId) {
          startNewConversation();
        }
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

  const searchPolicies = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch(`${API_BASE_URL}/chat/policy-search?q=${encodeURIComponent(query)}`);
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.policies || []);
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
    
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    searchTimeoutRef.current = setTimeout(() => {
      searchPolicies(query);
    }, 500);
  };

  const formatMessage = (content) => {
    // Convert markdown-like formatting to HTML
    let formatted = content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/🔗 \*\*(.*?)\*\*: (http[^\s]+)/g, '<div class="mt-2"><a href="$2" target="_blank" class="inline-flex items-center px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"><span>$1</span><svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg></a></div>')
      .replace(/📝 \*\*(.*?)\*\*: (http[^\s]+)/g, '<div class="mt-2"><a href="$2" target="_blank" class="inline-flex items-center px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-sm"><span>$1</span><svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg></a></div>')
      .replace(/\n/g, '<br>');
    
    return formatted;
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Sidebar */}
      <div className={`bg-white border-r border-gray-200 transition-all duration-300 ${showSidebar ? 'w-80' : 'w-0 overflow-hidden'}`}>
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-6 h-6" />
                <h2 className="font-bold text-lg">Policy Chatter</h2>
              </div>
              <button
                onClick={startNewConversation}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                title="New Conversation"
              >
                <Plus className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Search */}
          <div className="p-4 border-b border-gray-200">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search policies..."
                value={searchQuery}
                onChange={handleSearchChange}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
              />
            </div>
            
            {/* Search Results */}
            {searchQuery && (
              <div className="mt-3 max-h-40 overflow-y-auto">
                {isSearching ? (
                  <div className="text-center py-2 text-gray-500 text-sm">Searching...</div>
                ) : searchResults.length > 0 ? (
                  <div className="space-y-2">
                    {searchResults.slice(0, 5).map((policy, index) => (
                      <div
                        key={index}
                        onClick={() => sendMessage(`Tell me about ${policy.policy_name} in ${policy.country}`)}
                        className="p-2 hover:bg-gray-50 rounded cursor-pointer border border-gray-200"
                      >
                        <div className="font-medium text-xs text-blue-600">{policy.country}</div>
                        <div className="text-sm truncate">{policy.policy_name}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-2 text-gray-500 text-sm">No policies found</div>
                )}
              </div>
            )}
          </div>

          {/* Quick Questions */}
          <div className="p-4 border-b border-gray-200">
            <h3 className="font-medium text-gray-700 mb-3 flex items-center">
              <MessageCircle className="w-4 h-4 mr-2" />
              Quick Questions
            </h3>
            <div className="space-y-2">
              {suggestedQuestions.slice(0, 4).map((question, index) => (
                <button
                  key={index}
                  onClick={() => sendMessage(question)}
                  className="w-full text-left p-2 text-sm bg-gray-50 hover:bg-blue-50 hover:text-blue-700 rounded-lg transition-colors border border-gray-200"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>

          {/* Conversation History */}
          <div className="flex-1 overflow-y-auto p-4">
            <h3 className="font-medium text-gray-700 mb-3 flex items-center">
              <BookOpen className="w-4 h-4 mr-2" />
              Recent Conversations
            </h3>
            <div className="space-y-2">
              {conversations.map((conv) => (
                <div
                  key={conv.conversation_id}
                  onClick={() => loadConversation(conv.conversation_id)}
                  className={`p-3 rounded-lg cursor-pointer border transition-colors ${
                    currentConversationId === conv.conversation_id
                      ? 'bg-blue-50 border-blue-200'
                      : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {conv.last_message || 'New conversation'}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatTimestamp(conv.updated_at)}
                      </div>
                    </div>
                    <button
                      onClick={(e) => deleteConversation(conv.conversation_id, e)}
                      className="ml-2 p-1 hover:bg-red-100 rounded transition-colors"
                    >
                      <Trash2 className="w-3 h-3 text-red-500" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowSidebar(!showSidebar)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <MessageCircle className="w-5 h-5 text-gray-600" />
              </button>
              <div>
                <h1 className="text-xl font-bold text-gray-900 flex items-center">
                  <Globe className="w-6 h-6 mr-2 text-blue-600" />
                  AI Policy Expert Assistant
                </h1>
                <p className="text-sm text-gray-500">Powered by GPT • Database-driven responses</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                Online
              </span>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div 
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-4"
        >
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl rounded-2xl px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-900 shadow-sm'
                }`}
              >
                <div 
                  className="prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }}
                />
                <div className={`text-xs mt-2 ${message.role === 'user' ? 'text-blue-100' : 'text-gray-500'}`}>
                  {formatTimestamp(message.timestamp)}
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
                <div className="flex items-center space-x-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                  <span className="text-sm text-gray-500">Analyzing policies...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-end space-x-3">
              <div className="flex-1">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage();
                    }
                  }}
                  placeholder="Ask me about AI policies around the world..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
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
            
            {/* Quick Actions */}
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                onClick={() => sendMessage("What countries do you have AI policy data for?")}
                className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full text-sm transition-colors"
              >
                Available Countries
              </button>
              <button
                onClick={() => sendMessage("What are the main AI policy areas covered?")}
                className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full text-sm transition-colors"
              >
                Policy Areas
              </button>
              <button
                onClick={() => sendMessage("Compare AI policies between United States and European Union")}
                className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full text-sm transition-colors"
              >
                Compare Policies
              </button>
            </div>
            
            <div className="mt-2 text-xs text-gray-500 text-center">
              I only provide information from our curated AI policy database. 
              <a href={`${FRONTEND_URL}/register`} className="text-blue-600 hover:underline ml-1">
                Join as an expert
              </a> to contribute more data.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedPolicyChatter;
