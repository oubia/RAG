import React, { useState, useRef, useEffect, useCallback } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';

import { FaArrowLeft, FaArrowDown, FaRegStopCircle} from "react-icons/fa";
import { RiVoiceprintLine } from "react-icons/ri";

import SuggestedQuestions from './components/SuggestedQuestions';
import Message from './components/Messages';
import PermissionAlert from "./components/PermissionAlert";
import FormattedText from "./components/FormattedText";
import Layout from './components/Layouts';

const chatApiUrl = process.env.REACT_APP_BASE_URL;

const App = () => {
  const [messageHistory, setMessageHistory] = useState([]);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState('');
  const [showChat, setShowChat] = useState(false);
  const [showSuggestedQuestions, setShowSuggestedQuestions] = useState(true);
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);

  const [isListening, setIsListening] = useState(false);
  const [hasMicrophonePermission, setHasMicrophonePermission] = useState(false);
  const [isPermissionAlertVisible, setIsPermissionAlertVisible] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const bottomRef = useRef(null);
  const textareaRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const microphoneStreamRef = useRef(null);

  const disabled = loading || input.trim() === '';

  const suggestedQuestions = [
    "Quale legge ha istituito il Ministero del Turismo?",
    'Cosa prevede il comma 3 dell’articolo 6 del Decreto-Legge 1° marzo 2021, n. 22?',
    "Cosa stabilisce il DPCM del 20 maggio 2021, n. 102?",
    "Cos’è il Regolamento (UE) n. 2021/241 del 12 febbraio 2021?",
    'Quando è stato approvato il PNRR italiano dal Consiglio ECOFIN?',
  ];

  const [selectedapproach, setselectedapproach] = useState('Native-chunking');
  const approach = ['Native-chunking', 'Late-chunking'];
 
  const [selectedChunkSize, setselectedChunkSize] = useState('750');
  const chunksize = ['750',"250"];

  const [selectedapproachRetriever, setselectedapproachRetriever] = useState('Similarity-research');
  const retrieverOptions = ['Similarity-research', 'Contextual-Compression', 'Parent-document','Hybrid-fusion'];

  const handleLLMChange = (e) => { 
    setselectedapproach(e.target.value);
  };

  const handleVectordbChange = (e) => {
    setselectedChunkSize(e.target.value);
  };
 

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messageHistory]);

  const adjustTextareaHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = 'auto';
    const newHeight = Math.min(textarea.scrollHeight, 160);
    textarea.style.height = `${newHeight}px`;
    textarea.style.overflowY = newHeight === 160 ? 'auto' : 'hidden';
  }, []);

  useEffect(() => {
    adjustTextareaHeight();
  }, [input, adjustTextareaHeight]);

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (container) {
      container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }
  }, [messageHistory]);

  const handleStreamResponse = async (response) => {
    if (!response.ok) {
      const errorText = await response.text();
      console.error("Server error:", errorText);
      setError(`Server error: ${response.status}`);
      setLoading(false);
      return;
    }

    if (!response.body) {
      setError("Stream error: no response body");
      setLoading(false);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let done = false;
    let newMessage = "";

    setMessageHistory((prev) => [...prev, { role: "assistant", content: "", selectedapproach, selectedChunkSize, selectedapproachRetriever}]);

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;

      if (value) {
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.trim().startsWith("data:")) {
            try {
              const jsonString = line.trim().substring(5);
              const parsedChunk = JSON.parse(jsonString);

              if (parsedChunk.response) {
                newMessage += parsedChunk.response;
                setMessageHistory((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1].content = newMessage;
                  return updated;
                });
              }
            } catch (parseError) {
              console.error("Failed to parse JSON chunk:", parseError, line);
            }
          }
        }
      }
    }

    setLoading(false);
  };

  const sendMessage = async (message = input) => {
    if (!message?.trim()) return;

    setShowSuggestedQuestions(false);
    setShowChat(true);
    setLoading(true);
    setError(null);

    setMessageHistory((prev) => [...prev, { role: "user", content: message }]);
    setInput("");

    try {
      const response = await fetch(`http://127.0.0.1:8000/chat/`, {
        headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
        method: "POST",
        body: JSON.stringify({ 
          content: message,
          selectedapproach:selectedapproach,
          selectedChunkSize:selectedChunkSize,
          selectedapproachRetriever: selectedapproachRetriever,
        }),
        // credentials: "include",
      });
      await handleStreamResponse(response);
    } catch (networkError) {
      console.error("Network error:", networkError);
      setError("Network error");
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !disabled) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleDeleteChat = async () => {
    try {
      const response = await fetch(`${chatApiUrl}/delete_chat/`, {
        method: 'DELETE',
        // credentials: 'include',
      });

      if (response.ok) {
        setMessageHistory([]);
        setSuccess(true);
        setTimeout(() => setSuccess(false), 2000);
        setShowSuggestedQuestions(true);
        setShowChat(false);
      } else {
        setError('Failed to delete chat history');
      }
    } catch (err) {
      console.error('Error deleting chat:', err);
      setError('Network error');
    }
  };

  const handleScroll = () => {
    const container = messagesContainerRef.current;
    if (!container) return;

    const { scrollTop, scrollHeight, clientHeight } = container;
    setShowScrollToBottom(!(scrollHeight - scrollTop === clientHeight));
  };

  const scrollToBottom = () => {
    const container = messagesContainerRef.current;
    if (container) {
      container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }
  };

  const findLastIndex = (array, predicate) => {
    for (let i = array.length - 1; i >= 0; i--) {
      if (predicate(array[i])) return i;
    }
    return -1;
  };

  const handleAudioResponse = async (response) => {
    if (!response.ok) {
      const errorText = await response.text();
      console.error("Server error:", errorText);
      setError(`Server error: ${response.status}`);
      setLoading(false);
      return;
    }

    if (!response.body) {
      setError("Stream error: no response body");
      setLoading(false);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let done = false;
    let transcriptionText = "";
    let assistantMessage = "";

    setMessageHistory((prev) => [
      ...prev,
      { role: "user", content: "" },
      { role: "assistant", content: "" },
    ]);

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;

      if (value) {
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.trim().startsWith("data:")) {
            try {
              const jsonString = line.trim().substring(5);
              const parsedChunk = JSON.parse(jsonString);

              if (parsedChunk.type === "transcription") {
                transcriptionText += parsedChunk.response;
                setMessageHistory((prev) => {
                  const updated = [...prev];
                  const lastUserIndex = findLastIndex(updated, (msg) => msg.role === "user");
                  if (lastUserIndex !== -1) {
                    updated[lastUserIndex].content = transcriptionText;
                  }
                  return updated;
                });
              }

              if (parsedChunk.type === "assistant") {
                assistantMessage += parsedChunk.response;
                setMessageHistory((prev) => {
                  const updated = [...prev];
                  const lastAssistantIndex = findLastIndex(updated, (msg) => msg.role === "assistant");
                  if (lastAssistantIndex !== -1) {
                    updated[lastAssistantIndex].content = assistantMessage;
                  }
                  return updated;
                });
              }
            } catch (parseError) {
              console.error("Failed to parse JSON chunk:", parseError, line);
            }
          }
        }
      }
    }

    setLoading(false);
    setIsSubmitting(false);
  };

  const sendAudioToBackend = async (audioBlob) => {
    const formData = new FormData();
    formData.append("audio", audioBlob, "audio.wav");

    setShowSuggestedQuestions(false);
    setShowChat(true);
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`http://127.0.0.1:8000/process_audio/`, {
        method: "POST",
        mode: "no-cors",
        body: formData,
      });

      await handleAudioResponse(response);
    } catch (sendError) {
      console.error("Error sending audio to backend:", sendError);
      setError("Failed to process audio. Please try again.");
      setLoading(false);
      setIsSubmitting(false);
    }
  };

  const initializeMediaRecorder = (stream) => {
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorderRef.current = mediaRecorder;
    audioChunksRef.current = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
      sendAudioToBackend(audioBlob);
    };

    mediaRecorder.start();
    setIsListening(true);
  };

  const startListening = async () => {
    try {
      if (hasMicrophonePermission && microphoneStreamRef.current) {
        initializeMediaRecorder(microphoneStreamRef.current);
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setHasMicrophonePermission(true);
      microphoneStreamRef.current = stream;
      initializeMediaRecorder(stream);
    } catch (error) {
      console.error("Microphone access denied or error occurred:", error);
      setIsPermissionAlertVisible(true);
    }
  };

  const handleAllow = (stream) => {
    setIsPermissionAlertVisible(false);
    microphoneStreamRef.current = stream;
    setHasMicrophonePermission(true);
    initializeMediaRecorder(stream);
  };

  const handleDeny = () => {
    setIsPermissionAlertVisible(false);
    console.error("Microphone permission denied.");
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
    }
    setIsListening(false);
    setIsSubmitting(true);
  };


  return (
    <Router>
      <Layout />
      <div className="absolute top-40 right-10 w-48 sm:w-50 md:w-60 max-w-xs p-2 rounded-md shadow-md bg-white border">
      <h2 className="text-xl font-semibold mb-4">Select Chunking Approach</h2>
            {approach.map((llm) => (
              <label key={llm} className="flex items-center space-x-2 mb-2">
                <input
                  type="radio"
                  name="llm"
                  value={llm}
                  checked={selectedapproach === llm}
                  onChange={handleLLMChange}
                  className="accent-[#1665b5] cursor-pointer"
                />
                <span>{llm}</span>
              </label>
            ))}

            <h2 className="text-xl font-semibold mt-4">Select Chunk Size</h2>
              {chunksize.map((vector) => (
                <label key={vector} className="flex items-center space-x-2 mb-2">
                  <input
                    type="radio"
                    name="vector"
                    value={vector}
                    checked={selectedChunkSize === vector}
                    onChange={handleVectordbChange}
                    className="accent-[#1665b5] cursor-pointer"
                  />
                  <span>{vector}</span>
                </label>
              
              
              ))}
              <h2 className="text-xl font-semibold mb-4">Select Retriever Type</h2>
                {retrieverOptions.map((retriever) => (
                  <label key={retriever} className="flex items-center space-x-2 mb-2">
                    <input
                      type="radio"
                      name="retriever"
                      value={retriever}
                      checked={selectedapproachRetriever === retriever}
                      onChange={(e) => setselectedapproachRetriever(e.target.value)}
                      className="accent-[#1665b5] cursor-pointer"
                    />
                    <span>{retriever}</span>
                  </label>
                ))}
              
            {/* <button
              className="mt-6 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
              onClick={handleSubmit}
            >
              Submit
            </button> */}
        </div>
      <div
          className="container mx-auto px-6 flex flex-col items-center overflow-y-scroll hide-scrollbar"
          style={{ height: 'calc(105vh - 64px)' }}
        >
        {isPermissionAlertVisible && (
          <PermissionAlert onAllow={handleAllow} onDeny={handleDeny} />
        )}

        <div className="relative w-full">
            <div className="absolute top-4 left-10">
              <button
                onClick={() => {
                  setShowSuggestedQuestions(true);
                  setShowChat(false);
                }}
                className="flex items-center px-2 py-2 rounded-md shadow-md bg-white text-[#1665b5] hover:bg-[#1665b5] hover:text-white"
                
              >
                <FaArrowLeft className="text-lg" />
                <span className="sr-only">Torna alle domande suggerite</span>
              </button>
            </div>
            
        </div>
        


        {showSuggestedQuestions && !showChat ? (
          <div className="flex-grow">
            <SuggestedQuestions
              suggestedQuestions={suggestedQuestions}
              setShowChat={setShowChat}
              sendMessage={(msg) => {
                sendMessage(msg);
                setShowChat(true);
              }}
            />
          </div>
        ) : (
          <div className="flex-grow w-full max-w-4xl mx-auto">
            <div
              className="flex flex-col space-y-4 p-6 rounded-lg max-w-5xl mx-auto mt-6 overflow-y-scroll hide-scrollbar"
              ref={messagesContainerRef}
              onScroll={handleScroll}
              style={{ maxHeight: 'calc(98vh - 200px)' }}
            >
              {messageHistory.map((msg, index) => {
                const isUser = msg.role === 'user';
                const isAssistant = msg.role === 'assistant';
                const isLastMessage = index === messageHistory.length - 1;
                const isAssistantTyping = isAssistant && !msg.content && loading && isLastMessage;

                return (
                  <Message
                    key={index}
                    msg={msg}
                    isUser={isUser}
                    isAssistantTyping={isAssistantTyping}
                  />
                );
              })}
              <div ref={bottomRef}></div>
              
            </div>
          </div>
        )}

        <div className="sticky bottom-0 left-0 w-full p-4 bg-white max-w-4xl mx-auto flex items-center space-x-4">
          <div className="relative w-full">
            {error && (
              <div className="animate-fadeIn p-2 px-4 w-full bg-red-500 text-white rounded-md mb-2">
                <FormattedText>{error}</FormattedText>
              </div>
            )}

            {success && (
              <div className="animate-fadeIn p-2 px-4 w-full bg-[#00a481] text-white rounded-md mb-2">
                <FormattedText>Chat history has been deleted</FormattedText>
              </div>
            )}

            {isListening ? (
              <div className="w-full pr-24 border rounded-md py-4 text-gray-700 px-4 bg-red-100 animate-pulse">
                <span className="text-red-500 font-semibold">Recording...</span>
              </div>
            ) : (
              <textarea
                ref={textareaRef}
                value={input || ''}
                className="w-full pr-24 border rounded-md py-3 text-gray-700 leading-tight px-4 focus:outline-none focus:ring-2 focus:ring-[#1665b5] resize-none min-h-[2.5rem] max-h-40"
                onChange={(e) => {
                  setInput(e.target.value);
                  setError(null);
                }}
                onKeyDown={handleKeyDown}
                rows="1"
                placeholder="Scrivi un messaggio..."
              />
            )}

            {loading && (
              <div className="animate-fadeIn absolute bottom-5 right-14 h-5 w-5 animate-spin rounded-full border-2 border-solid border-[#1665b5] border-r-transparent" />
            )}

            <div className="absolute right-2 bottom-3 flex space-x-0">
              {input.trim() ? (
                <button
                  className={`flex justify-center items-center p-2 rounded-md ${
                    disabled
                      ? 'bg-gray-300 cursor-not-allowed text-[#1665b5]'
                      : 'bg-[#1665b5] hover:bg-[#1665b5] text-white'
                  }`}
                  onClick={() => sendMessage()}
                  disabled={disabled}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="17"
                    height="17"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <circle cx="12" cy="12" r="10" />
                    <path d="M16 12l-4-4-4 4" />
                    <path d="M12 16V8" />
                  </svg>
                  <span className="sr-only">Send message</span>
                </button>
              ) : (
                <button
                  className={`flex justify-center items-center p-2 rounded-md ${
                    isSubmitting
                      ? 'bg-gray-300 cursor-not-allowed text-[#1665b5]'
                      : isListening
                      ? 'bg-[#1665b5] text-white'
                      : 'bg-[#1665b5] hover:bg-[#1665b5] text-white'
                  }`}
                  onClick={isListening ? handleStopRecording : startListening}
                  disabled={isSubmitting}
                >
                  {isListening ? <FaRegStopCircle size={17} /> : <RiVoiceprintLine size={17} />}
                  <span className="sr-only">
                    {isListening ? 'Stop recording' : 'Start recording'}
                  </span>
                </button>
              )}
            </div>
          </div>
        </div>

        {showScrollToBottom && (
          <button
            className="fixed bottom-20 left-1/2 transform -translate-x-1/2 p-3 rounded-full bg-[#1665b5] text-white hover:bg-[#1665b5] shadow-md"
            onClick={scrollToBottom}
          >
            <FaArrowDown size={15} />
            <span className="sr-only">Scroll to Bottom</span>
          </button>
        )}
      </div>
    </Router>
  );
};

export default App;
