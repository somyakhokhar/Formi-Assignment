import React, { useState, useEffect, useRef } from "react";
import { formatTime } from "../utils/utils";
import WebSocketService from "../utils/network";

const ChatComponent = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [currentResponse, setCurrentResponse] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const wsServiceRef = useRef(null);
  const messagesEndRef = useRef(null);
  const currentResponseRef = useRef("");
  const [currentResponseTimestamp, setCurrentResponseTimestamp] =
    useState(null);

  // Get existing session ID or create new one
  const getOrCreateSessionId = () => {
    let sessionId = localStorage.getItem("chatSessionId");
    if (!sessionId) {
      sessionId = crypto.randomUUID();
      localStorage.setItem("chatSessionId", sessionId);
    }
    return sessionId;
  };

  const sessionIdRef = useRef(getOrCreateSessionId());

  useEffect(() => {
    // Initialize WebSocket service with session ID
    wsServiceRef.current = new WebSocketService(
      "ws://localhost:8765",
      sessionIdRef.current
    );

    // Set up callbacks
    wsServiceRef.current.setOnConnectionChangeCallback((connected) => {
      setIsConnected(connected);
    });

    wsServiceRef.current.setOnMessageCallback((data) => {
      console.log("Received chunk:", data);

      if (data.status === "end") {
        // Add the complete response to messages
        const completeMessage = currentResponseRef.current;
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: completeMessage,
            timestamp: currentResponseTimestamp || new Date(),
          },
        ]);
        setCurrentResponse("");
        currentResponseRef.current = "";
        setCurrentResponseTimestamp(null);
        setIsTyping(false);
      } else if (data.content !== undefined) {
        // Update both the state and ref with the new chunk
        const newContent = currentResponseRef.current + data.content;
        currentResponseRef.current = newContent;
        setCurrentResponse(newContent);
        setIsTyping(true);
        if (!currentResponseTimestamp) setCurrentResponseTimestamp(new Date());
      }
    });

    // Connect to WebSocket
    wsServiceRef.current.connect();

    return () => {
      if (wsServiceRef.current) {
        wsServiceRef.current.disconnect();
      }
    };
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentResponse]);

  const sendMessage = () => {
    if (!inputMessage.trim() || !wsServiceRef.current) return;

    // Add user message to chat
    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: inputMessage,
        timestamp: new Date(),
      },
    ]);

    // Send message through WebSocket
    wsServiceRef.current.sendMessage(inputMessage);

    setInputMessage("");
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="flex flex-col h-[80vh] w-[600px] border-2 border-gray-900 rounded-3xl shadow-xl overflow-hidden">
        <h1 className="text-2xl font-bold text-center py-[16px] text-blacl">
          Formi Chatbot
        </h1>
        <div className="py-[16px] text-center text-gray-700 font-medium ">
          Welcome to Formi Chatbot,
          <br />
          Im here to answer your questions about Barbique Nation, related to
          booking etc.
        </div>
        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-[16px] py-[8px] space-y-4 ">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${
                msg.role === "user" ? "justify-end" : "justify-start"
              } mx-2`}
            >
              <div
                className={`relative max-w-[90%] px-[32px] py-[12px] ${
                  msg.role === "user"
                    ? "ml-auto bg-[#005c4b] text-white rounded-2xl rounded-br-sm"
                    : "mr-auto bg-[#202c33] text-white rounded-2xl rounded-bl-sm"
                }`}
              >
                <div className="whitespace-pre-wrap break-words text-base font-normal">
                  {msg.content}
                </div>
                <div className="text-xs mt-1 text-gray-400 text-right">
                  {formatTime(new Date(msg.timestamp))}
                </div>
              </div>
            </div>
          ))}
          {currentResponse && (
            <div className="flex justify-start">
              <div className="relative mx-2 px-[20px] py-[16px] rounded-2xl shadow-md bg-white text-gray-800 rounded-tl-none">
                <div className="whitespace-pre-wrap break-words text-base font-normal">
                  {currentResponse}
                </div>
                <div className="text-xs mt-2 text-gray-500">
                  {formatTime(currentResponseTimestamp || new Date())}
                </div>
              </div>
            </div>
          )}
          {isTyping && !currentResponse && (
            <div className="flex justify-start">
              <div className="px-[20px] py-[16px] rounded-2xl shadow-md bg-white text-gray-800 rounded-tl-none">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        {/* Input */}
        <div className="flex">
          <input
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a message"
            className="flex-1 pl-[48px] pr-[32px] py-[16px] h-[40px] rounded-full border-2 border-gray-900 outline-none text-base"
          />
          <button
            onClick={sendMessage}
            disabled={!isConnected || !inputMessage.trim()}
            className={`ml-[8px] p-[16px] rounded-full transition-all duration-200 ${
              isConnected && inputMessage.trim()
                ? "bg-[#005c4b] text-white hover:scale-110"
                : "bg-gray-700 text-gray-400 cursor-not-allowed"
            }`}
          ></button>
        </div>
        {!isConnected && (
          <div className="absolute left-0 right-0 bottom-20 text-center text-red-500 text-sm animate-pulse">
            Disconnected from server. Please refresh the page.
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatComponent;
