/**
 * Custom hooks for appointment management
 */

import { useCallback, useState, useEffect } from 'react';
import {
  getAvailableSlots,
  bookAppointment,
  listAppointments,
  cancelAppointment,
  healthCheck,
} from '@/lib/api-client';

interface Slot {
  id: string;
  slot_date: string;
  slot_time: string;
  duration_minutes: number;
  is_available: boolean;
  created_at: string;
}

interface Appointment {
  id: string;
  availability_slot_id: string;
  customer_name: string;
  customer_email: string;
  notes?: string;
  status: 'PENDING' | 'CONFIRMED' | 'CANCELLED';
  idempotency_key: string;
  created_at: string;
  confirmed_at?: string;
  cancelled_at?: string;
}

/**
 * Hook to fetch available slots
 */
export function useAvailableSlots() {
  const [slots, setSlots] = useState<Slot[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSlots = useCallback(async (startDate: Date, days: number = 7) => {
    setLoading(true);
    setError(null);

    try {
      const response = await getAvailableSlots(startDate, days);

      if (response.error) {
        setError(response.error.message);
        return;
      }

      setSlots(response.data?.slots || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  return { slots, loading, error, fetchSlots };
}

/**
 * Hook to book an appointment
 */
export function useBookAppointment() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const book = useCallback(
    async (
      slotId: string,
      customerName: string,
      customerEmail: string,
      notes?: string
    ) => {
      setLoading(true);
      setError(null);

      try {
        const response = await bookAppointment(
          slotId,
          customerName,
          customerEmail,
          notes
        );

        if (response.error) {
          // Handle different error response formats from backend
          let errorMessage = 'An error occurred while booking.';
          
          if (typeof response.error === 'string') {
            errorMessage = response.error;
          } else if (response.error.detail) {
            errorMessage = response.error.detail;
          } else if (response.error.message) {
            errorMessage = response.error.message;
          } else if (response.error.error) {
            errorMessage = response.error.error;
          }
          
          console.log('Setting error message:', errorMessage);
          setError(errorMessage);
          return null;
        }

        return response.data;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { loading, error, book };
}

/**
 * Hook to fetch appointments by email
 */
export function useAppointments() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(
    async (email: string, includeCancelled: boolean = true) => {
      setLoading(true);
      setError(null);

      try {
        const response = await listAppointments(email, includeCancelled);

        if (response.error) {
          setError(response.error.message);
          return;
        }

        setAppointments(response.data?.appointments || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { appointments, loading, error, fetch };
}

/**
 * Hook to cancel an appointment (idempotent)
 */
export function useCancelAppointment() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cancel = useCallback(async (appointmentId: string, reason?: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await cancelAppointment(appointmentId, reason);

      if (response.error) {
        setError(response.error.message);
        return null;
      }

      return response.data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, cancel };
}

/**
 * Hook to check API health
 */
export function useApiHealth() {
  const [isHealthy, setIsHealthy] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const healthy = await healthCheck();
        setIsHealthy(healthy);
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
  }, []);

  return { isHealthy, loading };
}
