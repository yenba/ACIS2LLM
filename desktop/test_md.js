import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { renderToString } from 'react-dom/server';
import React from 'react';

const markdown = `
Yes — June 2026 was 4th wettest.

| Rank | Year | Precipitation |

|------|------|---------------|

| 1 | 1960 | 11.69" |

| 2 | 1998 | 10.81" |
`;

const fixedMarkdown = markdown.replace(/\|\n\n\|/g, '|\n|');

const html = renderToString(
  React.createElement(ReactMarkdown, { remarkPlugins: [remarkGfm] }, fixedMarkdown)
);

console.log(html);
