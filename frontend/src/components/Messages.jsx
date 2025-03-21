import React from 'react';
import PropTypes from 'prop-types';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
const Message = ({ msg, isUser, isAssistantTyping }) => {
  const FormattedText = ({ children }) => (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkBreaks]}
      components={{
        li: ({ node, ...props }) => <li className="my-2" {...props} />,
        ol: ({ node, ...props }) => <ol className="list-disc my-4" {...props} />,
      }}
    >
      {children}
    </ReactMarkdown>
  );
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`relative max-w-3xl px-6 py-3 rounded-lg ${
          isUser
            ? 'bg-[#EE182B] text-white rounded-br-none'
            : 'bg-gray-100 text-gray-800 rounded-bl-none'
        }`}
      >
        {isAssistantTyping ? (
          <div className="flex items-center">
            <div className="loading-spinner"></div>
            <span className="ml-2">Sto pensando...</span>
          </div>
        ) : (
          <FormattedText>{msg.content}</FormattedText>
        )}
      </div>
    </div>
  );
};

Message.propTypes = {
  msg: PropTypes.shape({
    role: PropTypes.string.isRequired,
    content: PropTypes.string,
  }).isRequired,
  isUser: PropTypes.bool.isRequired,
  isAssistantTyping: PropTypes.bool.isRequired,
};

export default Message;
