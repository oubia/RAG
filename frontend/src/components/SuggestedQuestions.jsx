import React, { useState, useEffect } from "react";

const SuggestedQuestions = ({ suggestedQuestions, setShowChat, sendMessage }) => {
  const fullText = "Come posso aiutarti oggi?";
  const [displayedText, setDisplayedText] = useState("");

  useEffect(() => {
    let currentIndex = 1;
    const typingSpeed = 100; // Typing speed in milliseconds
    let isCancelled = false;

    const typeText = () => {
      if (isCancelled) return;

      setDisplayedText(fullText.substring(0, currentIndex));
      if (currentIndex < fullText.length) {
        currentIndex++;
        setTimeout(typeText, typingSpeed);
      }
    };

    typeText();

    return () => {
      isCancelled = true;
    };
  }, []);

  return (
    <div className="flex flex-col items-center mt-10 text-center">
      <h2 className="text-3xl font-bold text-gray-800 mb-8 self-center">
        {displayedText}
      </h2>
      <div className="flex flex-wrap justify-center gap-8">
        {suggestedQuestions.map((question, index) => (
          <button
            key={index}
            onClick={() => {
              setShowChat(true);
              sendMessage(question);
            }}
            className="flex items-center space-x-2 px-6 py-4 border rounded-lg shadow-lg text-lg font-semibold text-gray-800 bg-white hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-[#1665b5]"
          >
            <span>{question}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default SuggestedQuestions;
