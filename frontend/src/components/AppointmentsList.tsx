/**
 * Appointments list component
 */

import React from 'react';

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

interface AppointmentsListProps {
  appointments: Appointment[];
  onCancel?: (appointmentId: string) => Promise<void>;
  loading?: boolean;
}

const statusColor: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-800',
  CONFIRMED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-red-100 text-red-800',
};

export default function AppointmentsList({
  appointments,
  onCancel,
  loading = false,
}: AppointmentsListProps) {
  if (appointments.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-lg">No appointments found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {appointments.map((appointment) => (
        <div
          key={appointment.id}
          className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500"
        >
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {appointment.customer_name}
              </h3>
              <p className="text-sm text-gray-600">{appointment.customer_email}</p>
            </div>
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold ${
                statusColor[appointment.status]
              }`}
            >
              {appointment.status}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
            <div>
              <p className="text-gray-600">Booked on</p>
              <p className="font-medium text-gray-900">
                {new Date(appointment.created_at).toLocaleDateString()}
              </p>
            </div>
            {appointment.confirmed_at && (
              <div>
                <p className="text-gray-600">Confirmed on</p>
                <p className="font-medium text-gray-900">
                  {new Date(appointment.confirmed_at).toLocaleDateString()}
                </p>
              </div>
            )}
          </div>

          {appointment.notes && (
            <div className="mb-4 p-3 bg-gray-50 rounded text-sm">
              <p className="text-gray-600">Notes:</p>
              <p className="text-gray-900">{appointment.notes}</p>
            </div>
          )}

          {appointment.status !== 'CANCELLED' && onCancel && (
            <button
              onClick={() => onCancel(appointment.id)}
              disabled={loading}
              className="text-red-600 hover:text-red-900 text-sm font-medium transition"
            >
              {loading ? 'Cancelling...' : 'Cancel Appointment'}
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
