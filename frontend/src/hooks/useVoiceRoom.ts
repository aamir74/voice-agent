// Manages a LiveKit Room lifecycle: connect, disconnect, mic mute, and transcript.
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ConnectionState,
  Room,
  RoomEvent,
  Track,
  type TranscriptionSegment,
  type Participant,
} from 'livekit-client';
import { fetchToken } from '../lib/api';

export interface TranscriptLine {
  id: string;
  speaker: 'you' | 'agent';
  text: string;
  final: boolean;
}

export interface VoiceRoomState {
  connectionState: ConnectionState;
  connected: boolean;
  connecting: boolean;
  micEnabled: boolean;
  error: string | null;
  transcript: TranscriptLine[];
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  toggleMic: () => Promise<void>;
  clearTranscript: () => void;
}

export function useVoiceRoom(): VoiceRoomState {
  const roomRef = useRef<Room | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>(
    ConnectionState.Disconnected,
  );
  const [micEnabled, setMicEnabled] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);

  // Attach agent audio so we can actually hear the response.
  useEffect(() => {
    return () => {
      roomRef.current?.disconnect();
    };
  }, []);

  const handleTranscription = useCallback(
    (
      segments: TranscriptionSegment[],
      participant?: Participant,
    ) => {
      const isAgent = participant?.isAgent ?? false;
      setTranscript((prev) => {
        const next = [...prev];
        for (const seg of segments) {
          const line: TranscriptLine = {
            id: seg.id,
            speaker: isAgent ? 'agent' : 'you',
            text: seg.text,
            final: seg.final,
          };
          const idx = next.findIndex((l) => l.id === seg.id);
          if (idx >= 0) next[idx] = line;
          else next.push(line);
        }
        return next;
      });
    },
    [],
  );

  const connect = useCallback(async () => {
    setError(null);
    try {
      const { token, url } = await fetchToken();
      const room = new Room({ adaptiveStream: true, dynacast: true });

      room
        .on(RoomEvent.ConnectionStateChanged, (s) => setConnectionState(s))
        .on(RoomEvent.TranscriptionReceived, handleTranscription)
        .on(RoomEvent.TrackSubscribed, (track) => {
          if (track.kind === Track.Kind.Audio) {
            const el = track.attach();
            el.style.display = 'none';
            document.body.appendChild(el);
          }
        })
        .on(RoomEvent.Disconnected, () => {
          setMicEnabled(false);
        });

      await room.connect(url, token);
      await room.localParticipant.setMicrophoneEnabled(true);
      roomRef.current = room;
      setMicEnabled(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to connect');
      setConnectionState(ConnectionState.Disconnected);
    }
  }, [handleTranscription]);

  const disconnect = useCallback(async () => {
    await roomRef.current?.disconnect();
    roomRef.current = null;
  }, []);

  const toggleMic = useCallback(async () => {
    const room = roomRef.current;
    if (!room) return;
    const next = !micEnabled;
    await room.localParticipant.setMicrophoneEnabled(next);
    setMicEnabled(next);
  }, [micEnabled]);

  const clearTranscript = useCallback(() => setTranscript([]), []);

  return {
    connectionState,
    connected: connectionState === ConnectionState.Connected,
    connecting: connectionState === ConnectionState.Connecting,
    micEnabled,
    error,
    transcript,
    connect,
    disconnect,
    toggleMic,
    clearTranscript,
  };
}
