import React, { useMemo } from 'react';
import { marked } from 'marked';
import katex from 'katex';

interface MarkdownViewerProps {
  content: string;
  className?: string;
}

export const MarkdownViewer: React.FC<MarkdownViewerProps> = ({
  content,
  className = '',
}) => {
  const renderedHtml = useMemo(() => {
    if (!content) return '';

    // Step 1: Extract KaTeX Display Math ($$ ... $$) and Inline Math ($ ... $)
    const mathTokens: { [key: string]: string } = {};
    let tokenIndex = 0;

    // Display math: $$ ... $$
    let processed = content.replace(/\$\$([\s\S]+?)\$\$/g, (_, math) => {
      const token = `KATEXBLOCKTOKEN${tokenIndex++}X`;
      try {
        mathTokens[token] = katex.renderToString(math.trim(), {
          displayMode: true,
          throwOnError: false,
        });
      } catch (e) {
        mathTokens[token] = `<div class="katex-error my-2 p-2 rounded bg-rose-950/50 text-rose-300 font-mono text-xs">${math}</div>`;
      }
      return token;
    });

    // Inline math: $ ... $ (negative lookbehind/lookahead to prevent escaping currency like \$100)
    processed = processed.replace(/(?<!\\)\$([^\$\n]+?)(?<!\\)\$/g, (_, math) => {
      const token = `KATEXINLINETOKEN${tokenIndex++}X`;
      try {
        mathTokens[token] = katex.renderToString(math.trim(), {
          displayMode: false,
          throwOnError: false,
        });
      } catch (e) {
        mathTokens[token] = `<span class="katex-error text-rose-300 font-mono text-xs">${math}</span>`;
      }
      return token;
    });

    // Step 2: Parse Markdown into HTML via marked
    marked.setOptions({
      gfm: true,
      breaks: true,
    });

    let html = marked.parse(processed) as string;

    // Step 3: Replace tokens back with KaTeX rendered HTML
    for (const [token, katexHtml] of Object.entries(mathTokens)) {
      html = html.split(token).join(katexHtml);
    }

    return html;
  }, [content]);

  return (
    <div
      className={`markdown-scientific-content text-slate-200 text-xs leading-relaxed ${className}`}
      dangerouslySetInnerHTML={{ __html: renderedHtml }}
    />
  );
};
