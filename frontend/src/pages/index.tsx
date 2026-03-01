/**
 * Home page: Book an appointment
 */

import React, { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import { useAvailableSlots, useBookAppointment, useApiHealth } from '@/hooks/api-hooks';
import AvailabilityCalendar from '@/components/AvailabilityCalendar';
import BookingForm from '@/components/BookingForm';

export default function Home() {
  const [selectedSlot, setSelectedSlot] = useState<{
    id: string;
    date: string;
    time: string;
  } | null>(null);

  const [successMessage, setSuccessMessage] = useState('');
  const [startDate] = useState(new Date());

  const { slots, loading: slotsLoading, error: slotsError, fetchSlots } = useAvailableSlots();
  const { loading: bookingLoading, error: bookingError, book } = useBookAppointment();
  const { isHealthy, loading: healthLoading } = useApiHealth();

  // Fetch slots on component mount
  useEffect(() => {
    fetchSlots(startDate, 7);
  }, []);

  const handleSelectSlot = (slotId: string, date: string, time: string) => {
    setSelectedSlot({ id: slotId, date, time });
    setSuccessMessage('');
  };

  const handleBooking = async (data: { name: string; email: string; notes: string }) => {
    if (!selectedSlot) return;

    const appointment = await book(
      selectedSlot.id,
      data.name,
      data.email,
      data.notes || undefined
    );

    if (appointment) {
      setSuccessMessage(
        `✅ Appointment Confirmed!\n${selectedSlot.date} at ${selectedSlot.time}\nConfirmation sent to ${data.email}`
      );
      setSelectedSlot(null);
      // Refresh slots
      fetchSlots(startDate, 7);
      // Reset form
      setTimeout(() => {
        setSuccessMessage('');
      }, 5000);
    }
  };

  if (healthLoading) {
    return (
      <Layout>
        <div className="text-center py-12">
          <p className="text-gray-500">Connecting to API...</p>
        </div>
      </Layout>
    );
  }

  if (!isHealthy) {
    return (
      <Layout>
        <div className="max-w-2xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-xl font-bold text-red-900 mb-2">Service Unavailable</h2>
            <p className="text-red-800">
              Could not connect to the booking API. Please ensure the backend is running.
            </p>
            <p className="text-red-600 text-sm mt-2">
              Start the backend with: <code>docker-compose up</code>
            </p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Schedule Your Appointment
          </h1>
          <p className="text-lg text-gray-600">
            Choose a time that works best for you. All slots are guaranteed available.
          </p>
        </div>

        {/* Success Message */}
        {successMessage && (
          <div className="mb-8 p-6 bg-green-50 border-2 border-green-300 rounded-lg shadow-md">
            <p className="text-green-900 font-semibold whitespace-pre-line text-lg">{successMessage}</p>
            <p className="text-green-700 text-sm mt-2">Your booking is now pending confirmation. Please check your email.</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Availability Calendar */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Available Slots</h2>
              {slotsError && (
                <div className="p-4 bg-red-50 border border-red-200 rounded mb-4">
                  <p className="text-red-900 text-sm">{slotsError}</p>
                </div>
              )}
              <AvailabilityCalendar
                slots={slots}
                selectedSlotId={selectedSlot?.id}
                onSelectSlot={handleSelectSlot}
                loading={slotsLoading}
              />
            </div>
          </div>

          {/* Booking Form */}
          <div>
            <BookingForm
              selectedSlotId={selectedSlot?.id}
              selectedDate={selectedSlot?.date}
              selectedTime={selectedSlot?.time}
              onSubmit={handleBooking}
              loading={bookingLoading}
              error={bookingError}
              successMessage={successMessage}
            />
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-blue-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">🔒 No Double-Bookings</h3>
            <p className="text-gray-600 text-sm">
              Database-level locking ensures timeslots are never overbooked, even under concurrent bookings.
            </p>
          </div>
          <div className="bg-green-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">♻️ Idempotent</h3>
            <p className="text-gray-600 text-sm">
              Retrying a booking with the same request ID always returns the same result. Safe to retry.
            </p>
          </div>
          <div className="bg-purple-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">📧 Notifications</h3>
            <p className="text-gray-600 text-sm">
              Automatic confirmation emails sent asynchronously. Reliable delivery with retry logic.
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
