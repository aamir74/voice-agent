// Editable system prompt. Loads the current value and saves edits to the backend.
import { useEffect, useState } from 'react';
import { getPrompt, updatePrompt } from '../lib/api';

type SaveState = 'idle' | 'saving' | 'saved' | 'error';

export function SystemPromptEditor() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(true);
  const [saveState, setSaveState] = useState<SaveState>('idle');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPrompt()
      .then(setPrompt)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load prompt'))
      .finally(() => setLoading(false));
  }, []);

  async function save() {
    setSaveState('saving');
    setError(null);
    try {
      const stored = await updatePrompt(prompt);
      setPrompt(stored);
      setSaveState('saved');
      setTimeout(() => setSaveState('idle'), 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save');
      setSaveState('error');
    }
  }

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h2 className="mb-3 text-lg font-semibold text-gray-800">System Prompt</h2>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        disabled={loading}
        rows={6}
        placeholder={loading ? 'Loading…' : 'You are a helpful assistant…'}
        className="w-full resize-y rounded-lg border border-gray-300 p-3 text-sm text-gray-800 focus:border-blue-500 focus:outline-none"
      />
      <div className="mt-3 flex items-center gap-3">
        <button
          onClick={save}
          disabled={loading || saveState === 'saving'}
          className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {saveState === 'saving' ? 'Saving…' : 'Save Prompt'}
        </button>
        {saveState === 'saved' && <span className="text-sm text-emerald-600">Saved ✓</span>}
        {error && <span className="text-sm text-red-600">{error}</span>}
      </div>
    </section>
  );
}
