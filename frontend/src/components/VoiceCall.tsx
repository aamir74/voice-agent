// Voice call controls: connect/disconnect, mic mute, and connection status.
import type { VoiceRoomState } from '../hooks/useVoiceRoom';

interface Props {
  room: VoiceRoomState;
}

export function VoiceCall({ room }: Props) {
  const { connected, connecting, micEnabled, error, connect, disconnect, toggleMic } = room;

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">Voice Call</h2>
        <StatusBadge connected={connected} connecting={connecting} />
      </div>

      <div className="flex flex-wrap gap-3">
        {!connected ? (
          <button
            onClick={connect}
            disabled={connecting}
            className="rounded-lg bg-emerald-600 px-4 py-2 font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {connecting ? 'Connecting…' : 'Connect'}
          </button>
        ) : (
          <>
            <button
              onClick={toggleMic}
              className={`rounded-lg px-4 py-2 font-medium text-white ${
                micEnabled ? 'bg-blue-600 hover:bg-blue-700' : 'bg-amber-600 hover:bg-amber-700'
              }`}
            >
              {micEnabled ? 'Mute' : 'Unmute'}
            </button>
            <button
              onClick={disconnect}
              className="rounded-lg bg-red-600 px-4 py-2 font-medium text-white hover:bg-red-700"
            >
              Disconnect
            </button>
          </>
        )}
      </div>

      {error && (
        <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      )}
    </section>
  );
}

function StatusBadge({ connected, connecting }: { connected: boolean; connecting: boolean }) {
  const { label, color } = connecting
    ? { label: 'Connecting', color: 'bg-amber-100 text-amber-800' }
    : connected
      ? { label: 'Connected', color: 'bg-emerald-100 text-emerald-800' }
      : { label: 'Disconnected', color: 'bg-gray-100 text-gray-600' };
  return <span className={`rounded-full px-3 py-1 text-xs font-medium ${color}`}>{label}</span>;
}
