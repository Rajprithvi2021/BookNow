/**
 * Booking form component
 */

import React, { useState, useEffect } from 'react';

interface BookingFormProps {
  selectedSlotId?: string;
  selectedDate?: string;
  selectedTime?: string;
  onSubmit: (data: {
    name: string;
    email: string;
    notes: string;
  }) => Promise<void>;
  loading?: boolean;
  error?: string;
  successMessage?: string;
}

export default function BookingForm({
  selectedSlotId,
  selectedDate,
  selectedTime,
  onSubmit,
  loading = false,
  error,
  successMessage,
}: BookingFormProps) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    notes: '',
  });

  // Reset form when booking is successful
  useEffect(() => {
    if (successMessage) {
      setFormData({
        name: '',
        email: '',
        notes: '',
      });
    }
  }, [successMessage]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSlotId) {
      alert('Please select a time slot');
      return;
    }
    console.log('Submitting booking with data:', formData);
    await onSubmit(formData);
    console.log('Booking submission completed');
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Book Your Appointment</h2>

      {/* Success Message */}
      {successMessage && (
        <div className="mb-6 p-4 bg-green-50 border-2 border-green-300 rounded-lg">
          <p className="text-green-900 font-semibold whitespace-pre-line text-base">{successMessage}</p>
          <p className="text-green-700 text-sm mt-2">Your booking has been confirmed. You can check your email for details.</p>
        </div>
      )}

      {/* Show form only if no success message */}
      {!successMessage && (
        <>
          {/* Selected Slot Display */}
      {selectedDate && selectedTime && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-gray-600">Selected Time:</p>
          <p className="text-lg font-semibold text-blue-900">
            {new Date(selectedDate).toLocaleDateString('en-US', {
              weekday: 'long',
              month: 'long',
              day: 'numeric',
            })}{' '}
            at {selectedTime}
          </p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-900 text-sm">{error}</p>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="name"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Full Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="John Doe"
          />
        </div>

        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Email <span className="text-red-500">*</span>
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="john@example.com"
          />
        </div>

        <div>
          <label
            htmlFor="notes"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Notes (Optional)
          </label>
          <textarea
            id="notes"
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Any special requests or notes..."
            rows={4}
          />
        </div>

        <button
          type="submit"
          disabled={loading || !selectedSlotId}
          className={`w-full py-3 px-4 rounded-lg font-semibold transition ${
            loading || !selectedSlotId
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {loading ? 'Booking...' : 'Confirm Booking'}
        </button>
      </form>

      {!selectedSlotId && (
        <p className="mt-4 text-center text-sm text-gray-500">
          👆 Select a time slot above to enable booking
        </p>
      )}
        </>
      )}
