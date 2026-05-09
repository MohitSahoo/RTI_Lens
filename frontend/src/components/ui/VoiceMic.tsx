import React, { useState, useRef } from 'react';
import { Mic, Square, Loader2, CheckCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface VoiceMicProps {
  onTranscript: (text: string) => void;
  className?: string;
}

export const VoiceMic: React.FC<VoiceMicProps> = ({ onTranscript, className }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [provider, setProvider] = useState<string | null>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/wav';
      mediaRecorder.current = new MediaRecorder(stream, { mimeType });
      audioChunks.current = [];

      mediaRecorder.current.ondataavailable = (event) => {
        audioChunks.current.push(event.data);
      };

      mediaRecorder.current.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: mimeType });
        await sendToTranscribe(audioBlob, mimeType);
      };

      mediaRecorder.current.start();
      setIsRecording(true);
      setProvider(null);
    } catch (err) {
      console.error("Microphone access denied:", err);
      alert("Please allow microphone access to use voice dictation.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      setIsRecording(false);
      mediaRecorder.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const sendToTranscribe = async (blob: Blob, mimeType: string) => {
    setIsTranscribing(true);
    const formData = new FormData();
    const extension = mimeType.includes('webm') ? 'webm' : 'wav';
    formData.append('file', blob, `audio.${extension}`);

    try {
      const response = await fetch('/api/voice/transcribe', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        if (data.text) {
          onTranscript(data.text);
          setProvider(data.provider);
          console.log(`Transcribed via ${data.provider}:`, data.text);
          // Hide provider notification after 3s
          setTimeout(() => setProvider(null), 3000);
        }
      } else {
        const error = await response.json();
        console.error("Transcription failed:", error.detail);
        alert(`Transcription error: ${error.detail}`);
      }
    } catch (err) {
      console.error("Transcription network error:", err);
    } finally {
      setIsTranscribing(false);
    }
  };

  return (
    <div className={`relative flex items-center gap-3 ${className}`}>
      <AnimatePresence>
        {provider && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="absolute right-full mr-3 whitespace-nowrap bg-success/10 border border-success/20 px-3 py-1 rounded-full flex items-center gap-2"
          >
            <CheckCircle className="w-3 h-3 text-success" />
            <span className="text-[10px] font-bold text-success uppercase tracking-widest">
              Transcribed via {provider}
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="relative">
        <AnimatePresence>
          {isRecording && (
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1.2, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              className="absolute -inset-2 bg-danger/20 rounded-full blur-md z-0"
            />
          )}
        </AnimatePresence>
        
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isTranscribing}
          className={`relative z-10 p-2.5 rounded-xl transition-all flex items-center justify-center ${
            isRecording 
              ? 'bg-danger text-white animate-pulse shadow-lg shadow-danger/20' 
              : isTranscribing
              ? 'bg-primary/20 text-primary border border-primary/20'
              : 'bg-white/5 text-white/60 hover:bg-white/10 hover:text-white border border-white/10'
          }`}
          title={isRecording ? "Stop Recording" : "Dictate (ElevenLabs -> Groq)"}
        >
          {isTranscribing ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : isRecording ? (
            <Square className="w-5 h-5 fill-current" />
          ) : (
            <Mic className="w-5 h-5" />
          )}
        </button>
      </div>
    </div>
  );
};
