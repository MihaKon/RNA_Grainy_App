import type { ModelDocumentation } from "@/api/types";

const CITATION_MARKER = /(\[\d+\])/;

export function ModelDescription({ model }: { model: ModelDocumentation }) {
  const citationUrls = new Map(
    model.citations.map((citation) => [
      `[${citation.number.toString()}]`,
      citation.url,
    ]),
  );

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-ink-2">
        {model.description.split(CITATION_MARKER).map((part, index) => {
          const url = citationUrls.get(part);
          return url ? (
            <a
              key={index}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-accent hover:text-accent-hover"
            >
              {part}
            </a>
          ) : (
            part
          );
        })}
      </p>

      {model.citations.length > 0 && (
        <ol className="flex flex-col gap-2 border-t border-dashed border-line-soft pt-3">
          {model.citations.map((citation) => (
            <li
              key={citation.number}
              className="flex gap-2 font-mono text-xs text-ink-3"
            >
              <span className="text-ink-2">[{citation.number}]</span>
              <a
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-accent"
              >
                {citation.text}
              </a>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
