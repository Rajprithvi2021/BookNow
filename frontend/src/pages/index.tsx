/**
 * Home page: Book an appointment
 */

import React, { useEffect, useState, useRef } from 'react';
import Layout from '@/components/Layout';
import { useAvailableSlots, useBookAppointment, useApiHealth } from '@/hooks/api-hooks';
import AvailabilityCalendar from '@/components/AvailabilityCalendar';
import BookingForm from '@/components/BookingForm';
import ConfirmationModal from '@/components/ConfirmationModal';

export default function Home() {
  const [selectedSlot, setSelectedSlot] = useState<{
    id: string;
    date: string;
    time: string;
  } | null>(null);

  const [successMessage, setSuccessMessage] = useState('');
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [showConfirmationModal, setShowConfirmationModal] = useState(false);
  const [confirmationDetails, setConfirmationDetails] = useState<{
    date: string;
    time: string;
    email: string;
  } | null>(null);
  const formRef = useRef<HTMLDivElement>(null);

  const { slots, loading: slotsLoading, error: slotsError, fetchSlots } = useAvailableSlots();
  const { loading: bookingLoading, error: bookingError, book } = useBookAppointment();
  const { isHealthy, loading: healthLoading } = useApiHealth();

  // Fetch slots for current month
  useEffect(() => {
    fetchSlots(currentMonth, 30);
  }, [currentMonth]);

  const handleSelectSlot = (slotId: string, date: string, time: string) => {
    setSelectedSlot({ id: slotId, date, time });
    setSuccessMessage('');
    
    // Scroll to booking form with a small delay to ensure the DOM is updated
    setTimeout(() => {
      formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  };

  const handleBooking = async (data: { name: string; email: string; notes: string }) => {
    if (!selectedSlot) return;

    const appointment = await book(
      selectedSlot.id,
      data.name,
      data.email,
      data.notes || undefined
    );

    console.log('Booking response:', appointment);

    if (appointment) {
      console.log('Appointment booked successfully:', appointment.id);
      // Show confirmation modal with booking details
      setConfirmationDetails({
        date: selectedSlot.date,
        time: selectedSlot.time,
        email: data.email,
      });
      setShowConfirmationModal(true);
      setSelectedSlot(null);
      // Refresh slots
      fetchSlots(currentMonth, 30);
    } else {
      console.log('Booking failed - appointment is null/undefined');
      console.log('Error:', bookingError);
    }
  };

  const handleCloseModal = () => {
    setShowConfirmationModal(false);
    setConfirmationDetails(null);
    setSuccessMessage('');
  };

  const handleBookAnother = () => {
    setSuccessMessage('');
    setSelectedSlot(null);
  };

  const goToPreviousMonth = () => {
    const prev = new Date(currentMonth);
    prev.setMonth(prev.getMonth() - 1);
    setCurrentMonth(prev);
  };

  const goToNextMonth = () => {
    const next = new Date(currentMonth);
    next.setMonth(next.getMonth() + 1);
    setCurrentMonth(next);
  };

  const monthName = currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
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
            <button
              onClick={handleBookAnother}
              className="mt-4 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-semibold"
            >
              Book Another Appointment
            </button>
          </div>
        )}

        {/* Month Navigation */}
        <div className="mb-8 flex items-center justify-between bg-blue-50 p-4 rounded-lg border border-blue-200">
          <button
            onClick={goToPreviousMonth}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            ← Previous Month
          </button>
          <h2 className="text-2xl font-bold text-gray-900">{monthName}</h2>
          <button
            onClick={goToNextMonth}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Next Month →
          </button>
        </div>

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
              {slotsLoading && (
                <div className="p-4 bg-blue-50 border border-blue-200 rounded mb-4">
                  <p className="text-blue-900 text-sm">Loading available slots...</p>
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
          <div ref={formRef}>
            <div className={`bg-white rounded-lg shadow-md p-6 sticky top-4 ${selectedSlot ? 'ring-2 ring-blue-500' : ''}`}>
              {selectedSlot && (
                <div className="mb-4 p-3 bg-blue-50 border-l-4 border-blue-500 rounded">
                  <p className="text-sm text-blue-900 font-semibold">
                    ✓ Slot selected - Fill in your details below to complete booking
                  </p>
                </div>
              )}
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

      {/* Confirmation Modal */}
      {confirmationDetails && (
        <ConfirmationModal
          isOpen={showConfirmationModal}
          appointmentDate={confirmationDetails.date}
          appointmentTime={confirmationDetails.time}
          userEmail={confirmationDetails.email}
          onClose={handleCloseModal}
        />
      )}
    </Layout>
  );
}
