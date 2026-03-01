/**
 * Confirmation Modal Component
 * Displays booking confirmation details
 */

import React from 'react';

interface ConfirmationModalProps {
  isOpen: boolean;
  appointmentDate?: string;
  appointmentTime?: string;
  userEmail?: string;
  onClose: () => void;
}

export default function ConfirmationModal({
  isOpen,
  appointmentDate,
  appointmentTime,
  userEmail,
  onClose,
}: ConfirmationModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative z-10 bg-white rounded-lg shadow-2xl max-w-sm w-full mx-4 overflow-hidden animate-in fade-in zoom-in">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-500 to-green-600 px-6 py-8 text-white">
          <div className="flex items-center justify-center mb-3">
            <div className="bg-white/20 rounded-full p-3">
              <svg
                className="w-8 h-8"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-center">Booking Confirmed!</h2>
        </div>

        {/* Content */}
        <div className="px-6 py-6 space-y-4">
          <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded">
            <p className="text-sm text-gray-600 font-medium">Appointment Details</p>
          </div>

          {appointmentDate && (
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 mt-1">
                <svg
                  className="w-5 h-5 text-green-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-gray-600">Date</p>
                <p className="text-lg font-semibold text-gray-900">
                  {appointmentDate}
                </p>
              </div>
            </div>
          )}

          {appointmentTime && (
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 mt-1">
                <svg
                  className="w-5 h-5 text-green-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00-.293.707l-1.414 1.414a1 1 0 001.414 1.414L9 9.414V6z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div>
                <p className="text-sm text-gray-600">Time</p>
                <p className="text-lg font-semibold text-gray-900">
                  {appointmentTime}
                </p>
              </div>
            </div>
          )}

          {userEmail && (
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 mt-1">
                <svg
                  className="w-5 h-5 text-green-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                  <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                </svg>
              </div>
              <div>
                <p className="text-sm text-gray-600">Confirmation Sent To</p>
                <p className="text-lg font-semibold text-gray-900 break-all">
                  {userEmail}
                </p>
              </div>
            </div>
          )}

          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded mt-6">
            <p className="text-sm text-blue-900">
              Check your email for a detailed confirmation and booking reference number.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <button
            onClick={onClose}
            className="w-full bg-green-600 hover:bg-green-700 active:bg-green-800 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
