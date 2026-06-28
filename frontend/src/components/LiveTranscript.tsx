// Live transcript view (bonus). Shows partial/final segments from both speakers.
import { useEffect, useLayoutEffect, useRef } from 'react';
import type { TranscriptLine } from '../hooks/useVoiceRoom';

interface Props {
  transcript: TranscriptLine[];
  onClear: () => void;
}

// Treat the user as "at the bottom" within this many pixels. Transcript updates
// stream in many partial segments per second, so we only auto-scroll when the
// user is already near the bottom — and we scroll the container instantly to
// avoid the self-interrupting smooth-scroll animation (the source of flicker).
const STICK_THRESHOLD_PX = 48;

export function LiveTranscript({ transcript, onClear }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const stickToBottomRef = useRef(true);

  // Track whether the user is parked at the bottom; pause auto-scroll if they
  // scroll up to read, resume once they return to the bottom.
  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    stickToBottomRef.current = distanceFromBottom <= STICK_THRESHOLD_PX;
  };

  // useLayoutEffect so the scroll is applied before paint — no visible jump.
  useLayoutEffect(() => {
    const el = containerRef.current;
    if (el && stickToBottomRef.current) {
      el.scrollTop = el.scrollHeight;
    }
  }, [transcript]);

  // Always snap to bottom when the transcript is cleared/reset.
  useEffect(() => {
    if (transcript.length === 0) stickToBottomRef.current = true;
  }, [transcript.length]);

  return (
    <section className="flex h-full flex-col rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">Live Transcript</h2>
        {transcript.length > 0 && (
          <button onClick={onClear} className="text-sm text-gray-500 hover:text-gray-700">
            Clear
          </button>
        )}
      </div>

      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="min-h-[120px] flex-1 space-y-2 overflow-y-auto"
      >
        {transcript.length === 0 ? (
          <p className="text-sm text-gray-400">Transcript will appear here during the call…</p>
        ) : (
          transcript.map((line) => (
            <div key={line.id} className="text-sm">
              <span
                className={`font-medium ${
                  line.speaker === 'agent' ? 'text-indigo-600' : 'text-gray-800'
                }`}
              >
                {line.speaker === 'agent' ? 'Agent' : 'You'}:
              </span>{' '}
              <span className={line.final ? 'text-gray-700' : 'text-gray-400 italic'}>
                {line.text}
              </span>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
