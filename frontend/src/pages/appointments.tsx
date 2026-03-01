/**
 * Appointments page: View and manage user's appointments
 */

import React, { useState } from 'react';
import Layout from '@/components/Layout';
import { useAppointments, useCancelAppointment } from '@/hooks/api-hooks';
import AppointmentsList from '@/components/AppointmentsList';

export default function AppointmentsPage() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const { appointments, loading: fetchLoading, error: fetchError, fetch } = useAppointments();
  const { loading: cancelLoading, error: cancelError, cancel } = useCancelAppointment();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    await fetch(email, true);
    setSubmitted(true);
  };

  const handleCancel = async (appointmentId: string) => {
    const result = await cancel(appointmentId);
    if (result) {
      // Refresh appointments list
      if (email) {
        fetch(email, true);
      }
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">My Appointments</h1>
        <p className="text-lg text-gray-600 mb-8">
          View and manage all your scheduled appointments.
        </p>

        {/* Search Form */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-4">
            <input
              type="email"
              placeholder="Enter your email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={fetchLoading}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400"
            >
              {fetchLoading ? 'Loading...' : 'Search'}
            </button>
          </form>
        </div>

        {/* Error Messages */}
        {fetchError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-900 text-sm">{fetchError}</p>
          </div>
        )}

        {cancelError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-900 text-sm">Error: {cancelError}</p>
          </div>
        )}

        {/* Appointments List */}
        {submitted && (
          <div className="bg-white rounded-lg shadow-md p-6">
            {fetchLoading ? (
              <div className="text-center py-8">
                <p className="text-gray-500">Loading appointments...</p>
              </div>
            ) : appointments.length > 0 ? (
              <>
                <h2 className="text-2xl font-bold text-gray-900 mb-6">
                  {appointments.length} Appointment{appointments.length !== 1 ? 's' : ''} Found
                </h2>
                <AppointmentsList
                  appointments={appointments}
                  onCancel={handleCancel}
                  loading={cancelLoading}
                />
              </>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">
                  No appointments found for <strong>{email}</strong>
                </p>
              </div>
            )}
          </div>
        )}

        {/* Info Section */}
        {!submitted && (
          <div className="bg-blue-50 rounded-lg p-8 border border-blue-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              How to Check Your Appointments
            </h3>
            <ol className="list-decimal list-inside space-y-2 text-gray-700">
              <li>Enter the email address you used when booking</li>
              <li>Click "Search" to retrieve your appointments</li>
              <li>View all confirmed, pending, or cancelled appointments</li>
              <li>Cancel future appointments if needed</li>
            </ol>
          </div>
        )}
      </div>
    </Layout>
  );
}
