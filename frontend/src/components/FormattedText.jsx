import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';

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

export default FormattedText;
