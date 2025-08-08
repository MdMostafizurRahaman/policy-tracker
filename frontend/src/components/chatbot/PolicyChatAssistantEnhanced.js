import React, { useState, useEffect, useRef } from 'react';
import { Send, Mic, Search, Globe, BookOpen, Users, Sparkles, ExternalLink, User, Bot } from 'lucide-react';

const PolicyChatAssistant = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const suggestedQuestions = [
    "🇺🇸 What AI policies does United States have?",
    "🇨🇦 Compare AI policies between USA and Canada",
    "🌍 Show me all available countries",
    "🤖 What are the latest AI safety policies?",
    "📚 Bangladesh digital education policies",
    "🔍 Search policies by area"
  ];

  const welcomeMessage = {
    id: 'welcome',
    role: 'assistant',
    content: `Hello! 👋 I'm your **AI Policy Expert Assistant**. I have access to comprehensive policy data from **15 countries** covering **9 key areas** with **61+ policies**.

**I can help you with:**
• 🔍 **Search** policies by country, area, or topic
• 📊 **Compare** policies between different countries  
• 📋 **Analyze** policy details and implementations
• 🌍 **Explore** global AI governance trends

**What would you like to know about AI policies today?**`,
    timestamp: new Date(),
    sources: []
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setShowWelcome(false);

    try {
      const response = await fetch('/api/chat/public', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          conversation_id: null
        })
      });

      const data = await response.json();
      
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        sources: data.sources || [],
        conversation_id: data.conversation_id
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
        timestamp: new Date(),
        sources: []
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestedClick = (question) => {
    setInputMessage(question.replace(/^[🇺🇸🇨🇦🌍🤖📚🔍]\s/, ''));
    setShowWelcome(false);
  };

  const renderMessage = (message) => {
    const isUser = message.role === 'user';
    const isWelcome = message.id === 'welcome';
    
    return (
      <div key={message.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
        <div className={`flex max-w-4xl ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start space-x-3`}>
          {/* Avatar */}
          <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
            isUser 
              ? 'bg-blue-500 text-white' 
              : isWelcome 
                ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                : 'bg-green-500 text-white'
          }`}>
            {isUser ? <User size={18} /> : <Bot size={18} />}
          </div>
          
          {/* Message Content */}
          <div className={`px-4 py-3 rounded-2xl ${
            isUser 
              ? 'bg-blue-500 text-white ml-3' 
              : isWelcome
                ? 'bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 mr-3'
                : 'bg-gray-100 border border-gray-200 mr-3'
          } ${isWelcome ? 'shadow-lg' : 'shadow-sm'}`}>
            
            {/* Message text */}
            <div className={`prose prose-sm max-w-none ${isUser ? 'text-white' : 'text-gray-800'}`}>
              {message.content.split('\\n\\n').map((paragraph, idx) => (
                <p key={idx} className="mb-2 last:mb-0">
                  {paragraph.split('**').map((part, i) => 
                    i % 2 === 1 ? <strong key={i} className="font-semibold">{part}</strong> : part
                  )}
                </p>
              ))}
            </div>
            
            {/* Sources */}
            {message.sources && message.sources.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-300">
                <div className="text-xs font-medium text-gray-600 mb-2">📚 Sources:</div>
                <div className="space-y-1">
                  {message.sources.map((source, idx) => (
                    <div key={idx} className="text-xs bg-white p-2 rounded border">
                      <div className="font-medium">{source.policy_name}</div>
                      <div className="text-gray-500">{source.country} • {source.area_name}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Timestamp */}
            <div className={`text-xs mt-2 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-800">AI Policy Expert Assistant</h1>
                <p className="text-sm text-gray-600">Powered by GPT • 61+ Policies • 15 Countries</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors">
                <ExternalLink size={16} />
                <span>Submit Policy</span>
              </button>
              <button className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">
                <User size={16} />
                <span>Register</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="bg-white rounded-2xl shadow-lg min-h-[600px] flex flex-col">
          
          {/* Messages Area */}
          <div className="flex-1 p-6 overflow-y-auto">
            {/* Welcome Message */}
            {showWelcome && (
              <div className="mb-8">
                {renderMessage(welcomeMessage)}
                
                {/* Suggested Questions */}
                <div className="mt-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4">🚀 Try asking:</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {suggestedQuestions.map((question, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSuggestedClick(question)}
                        className="text-left p-3 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg hover:from-blue-100 hover:to-purple-100 transition-all duration-200 text-sm"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
            
            {/* Chat Messages */}
            {messages.map(renderMessage)}
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start mb-6">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
                    <Bot size={18} className="text-white" />
                  </div>
                  <div className="bg-gray-100 rounded-2xl px-4 py-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          
          {/* Input Area */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex items-center space-x-3">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder="Ask about AI policies, countries, or specific policy areas..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-800 placeholder-gray-500"
                  disabled={isLoading}
                />
              </div>
              
              <button
                onClick={sendMessage}
                disabled={isLoading || !inputMessage.trim()}
                className="px-6 py-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
              >
                <Send size={18} />
                <span>Send</span>
              </button>
            </div>
            
            {/* Quick stats */}
            <div className="mt-3 flex items-center justify-center space-x-6 text-xs text-gray-500">
              <div className="flex items-center space-x-1">
                <Globe size={12} />
                <span>15 Countries</span>
              </div>
              <div className="flex items-center space-x-1">
                <BookOpen size={12} />
                <span>61+ Policies</span>
              </div>
              <div className="flex items-center space-x-1">
                <Users size={12} />
                <span>9 Key Areas</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PolicyChatAssistant;
