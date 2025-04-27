import React, { useState } from "react";
import { FaMicrophone } from "react-icons/fa";

const PermissionAlert = ({ onAllow, onDeny }) => {
  const [visible, setVisible] = useState(true);

  const handleAllow = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setVisible(false);
      onAllow(stream); // Pass the stream back to the parent to initialize the recorder
    } catch (error) {
      console.error("Microphone access denied by user or browser settings.", error);
      setVisible(false);
      onDeny(); // Handle denial
    }
  };

  const handleDeny = () => {
    setVisible(false);
    onDeny();
  };

  if (!visible) return null;

  return (
    <div className="fixed inset-0 bg-gray-800 bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-96">
        <div className="flex items-center justify-center mb-4">
          <FaMicrophone size={32} className="text-[#1665b5]" />
        </div>
        <h2 className="text-lg font-bold text-gray-800 text-center mb-2">
          Microphone Permission
        </h2>
        <p className="text-gray-600 text-center mb-6">
          We need your permission to access the microphone for recording your voice.
        </p>
        <div className="flex justify-center space-x-4">
          <button
            onClick={handleAllow}
            className="px-4 py-2 bg-[#1665b5] text-white rounded-md hover:bg-[#CA1424]"
          >
            Allow
          </button>
          <button
            onClick={handleDeny}
            className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
          >
            Deny
          </button>
        </div>
      </div>
    </div>
  );
};

export default PermissionAlert;
