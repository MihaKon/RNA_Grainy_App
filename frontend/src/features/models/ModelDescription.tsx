import type { ModelDocumentation } from "@/api/types";

const CITATION_MARKER = /(\[\d+\])/;
const DOI_SUFFIX = /^(.*?)\s*doi:\s*(\S+?)\.?$/;

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
            <li key={citation.number} className="flex gap-2 text-xs text-ink-2">
              <span className="shrink-0 font-mono text-ink-3">[{citation.number}]</span>
              <CitationText text={citation.text} url={citation.url} />
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

function CitationText({ text, url }: { text: string; url: string }) {
  const match = DOI_SUFFIX.exec(text);
  const reference = match?.[1];
  const doi = match?.[2];

  if (reference === undefined || doi === undefined) {
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="min-w-0 wrap-anywhere text-accent hover:text-accent-hover"
      >
        {text}
      </a>
    );
  }

  return (
    <span className="min-w-0">
      {reference}{" "}
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        title={`doi:${doi}`}
        aria-label={`Open publication, DOI: ${doi}`}
        className="inline-flex items-center gap-1 rounded border border-line-soft px-1.5 py-0.5 font-mono whitespace-nowrap text-accent transition-colors hover:border-accent hover:bg-surface"
      >
        DOI <span aria-hidden="true">↗</span>
      </a>
    </span>
  );
}
