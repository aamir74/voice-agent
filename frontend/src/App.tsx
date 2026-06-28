import { useVoiceRoom } from './hooks/useVoiceRoom';
import { VoiceCall } from './components/VoiceCall';
import { SystemPromptEditor } from './components/SystemPromptEditor';
import { DocumentUpload } from './components/DocumentUpload';
import { LiveTranscript } from './components/LiveTranscript';
import { RagSourcesPanel } from './components/RagSourcesPanel';

export default function App() {
  const room = useVoiceRoom();

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-4">
          <h1 className="text-xl font-bold text-gray-800">Voice AI Agent</h1>
          <p className="text-sm text-gray-500">
            Talk to an assistant grounded in your uploaded documents.
          </p>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-6 px-6 py-6 lg:grid-cols-2">
        <div className="space-y-6">
          <VoiceCall room={room} />
          <SystemPromptEditor />
          <DocumentUpload />
        </div>
        <div className="grid gap-6 lg:grid-rows-2">
          <LiveTranscript transcript={room.transcript} onClear={room.clearTranscript} />
          <RagSourcesPanel active={room.connected} />
        </div>
      </main>
    </div>
  );
}
