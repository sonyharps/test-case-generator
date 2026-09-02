import { useEffect, useRef } from 'react';
import { useAuth } from '@/store/auth.store';
import { toast } from 'sonner';

interface DocumentEvent {
  type: string;
  document_id?: number;
  status?: string;
  filename?: string;
  title?: string;
  chunk_count?: number;
  requirement_count?: number;
  error?: string;
  user_id?: number;
}

interface UseDocumentEventsOptions {
  onDocumentUpdate?: (event: DocumentEvent) => void;
}

export function useDocumentEvents(options?: UseDocumentEventsOptions) {
  const accessToken = useAuth((state) => state.accessToken);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const callbackRef = useRef(options?.onDocumentUpdate);

  // Update callback ref when it changes
  useEffect(() => {
    callbackRef.current = options?.onDocumentUpdate;
  }, [options?.onDocumentUpdate]);

  useEffect(() => {
    if (!accessToken) {
      return;
    }

    const connectToEventStream = () => {
      // Close existing connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      // Create new EventSource connection with token in query param
      const eventSource = new EventSource(
        `${import.meta.env.VITE_API_BASE ?? ""}/v1/documents/events/stream?token=${encodeURIComponent(accessToken)}`,
        {
          withCredentials: false,
        }
      );

      eventSource.onopen = () => {
        console.log('✅ Connected to document events stream');
      };

      eventSource.onmessage = (event) => {
        try {
          const data: DocumentEvent = JSON.parse(event.data);

          // Handle connection event
          if (data.type === 'connected') {
            console.log('📡 Document events stream initialized');
            return;
          }

          // Handle document update events
          if (data.type === 'document_update' && data.status) {
            handleDocumentUpdate(data);

            // Call custom callback if provided
            if (callbackRef.current) {
              callbackRef.current(data);
            }
          }
        } catch (error) {
          console.error('Failed to parse event data:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('❌ EventSource error:', error);
        eventSource.close();

        // Attempt to reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('🔄 Reconnecting to event stream...');
          connectToEventStream();
        }, 5000);
      };

      eventSourceRef.current = eventSource;
    };

    const handleDocumentUpdate = (event: DocumentEvent) => {
      const { status, filename, chunk_count, requirement_count, error } = event;

      switch (status) {
        case 'processing':
          toast.info(`Processing ${filename}`, {
            description: 'Extracting text and generating embeddings...',
            duration: 3000,
          });
          break;

        case 'completed':
          toast.success(`${filename} processed successfully!`, {
            description: `Found ${chunk_count || 0} chunks and ${requirement_count || 0} requirements`,
            duration: 5000,
          });
          break;

        case 'failed':
          toast.error(`Failed to process ${filename}`, {
            description: error || 'An error occurred during processing',
            duration: 7000,
          });
          break;

        default:
          console.log('Unknown document status:', status);
      }
    };

    connectToEventStream();

    // Cleanup on unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [accessToken]); // Removed options dependency to prevent re-connection on every render

  return {
    isConnected: eventSourceRef.current?.readyState === EventSource.OPEN,
  };
}
