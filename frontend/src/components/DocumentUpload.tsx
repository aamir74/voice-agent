// PDF upload to the knowledge base with progress and result feedback.
import { useRef, useState } from 'react';
import { uploadDocument } from '../lib/api';

type Status = 'idle' | 'uploading' | 'success' | 'error';

interface UploadedDoc {
  filename: string;
  chunkCount: number;
}

export function DocumentUpload() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [message, setMessage] = useState<string | null>(null);
  const [docs, setDocs] = useState<UploadedDoc[]>([]);

  async function handleUpload() {
    if (!file) return;
    setStatus('uploading');
    setMessage(null);
    try {
      const res = await uploadDocument(file);
      setDocs((prev) => [...prev, { filename: res.filename, chunkCount: res.chunk_count }]);
      setStatus('success');
      setMessage(`Indexed "${res.filename}" — ${res.chunk_count} chunks`);
      setFile(null);
      if (inputRef.current) inputRef.current.value = '';
    } catch (e) {
      setStatus('error');
      setMessage(e instanceof Error ? e.message : 'Upload failed');
    }
  }

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h2 className="mb-3 text-lg font-semibold text-gray-800">Knowledge Base</h2>

      <div className="flex flex-wrap items-center gap-3">
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="text-sm text-gray-700 file:mr-3 file:rounded-lg file:border-0 file:bg-gray-100 file:px-3 file:py-2 file:text-sm file:font-medium hover:file:bg-gray-200"
        />
        <button
          onClick={handleUpload}
          disabled={!file || status === 'uploading'}
          className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {status === 'uploading' ? 'Uploading…' : 'Upload PDF'}
        </button>
      </div>

      {message && (
        <p
          className={`mt-3 rounded-lg px-3 py-2 text-sm ${
            status === 'error' ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'
          }`}
        >
          {message}
        </p>
      )}

      {docs.length > 0 && (
        <ul className="mt-4 space-y-1 text-sm text-gray-700">
          {docs.map((d, i) => (
            <li key={i} className="flex justify-between rounded bg-gray-50 px-3 py-1.5">
              <span className="truncate">{d.filename}</span>
              <span className="text-gray-500">{d.chunkCount} chunks</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
