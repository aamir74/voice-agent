// RAG sources panel (bonus). Polls the backend for chunks used in the last answer.
import { useEffect, useState } from 'react';
import { getSources, type RagSource } from '../lib/api';

interface Props {
  active: boolean;
}

export function RagSourcesPanel({ active }: Props) {
  const [sources, setSources] = useState<RagSource[]>([]);

  useEffect(() => {
    if (!active) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const next = await getSources();
        if (!cancelled) setSources(next);
      } catch {
        // transient errors are fine; keep showing the last good result
      }
    };
    poll();
    const id = setInterval(poll, 2000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [active]);

  return (
    <section className="flex h-full flex-col rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h2 className="mb-3 text-lg font-semibold text-gray-800">RAG Sources</h2>
      <div className="flex-1 space-y-3 overflow-y-auto">
        {sources.length === 0 ? (
          <p className="text-sm text-gray-400">
            Chunks retrieved for the latest answer will appear here.
          </p>
        ) : (
          sources.map((s, i) => (
            <div key={i} className="rounded-lg border border-gray-100 bg-gray-50 p-3">
              <div className="mb-1 flex items-center justify-between">
                <span className="text-xs font-medium text-indigo-600">{s.source}</span>
                <span className="text-xs text-gray-400">score {s.score.toFixed(2)}</span>
              </div>
              <p className="line-clamp-4 text-xs text-gray-600">{s.text}</p>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
