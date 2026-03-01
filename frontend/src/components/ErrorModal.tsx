/**
 * Error Modal Component
 * Displays user-friendly error messages for booking failures
 */

import React from 'react';

interface ErrorModalProps {
  isOpen: boolean;
  title?: string;
  message: string;
  details?: string;
  onClose: () => void;
}

/**
 * Parse API error message and return user-friendly message
 */
function parseErrorMessage(apiMessage: string): { title: string; message: string } {

  if (apiMessage.includes('already booked')) {
    return {
      title: '❌ Slot Already Booked',
      message: 'Sorry, this time slot has been booked by another user. Please select a different slot.',
    };
  }


  if (apiMessage.includes('not found') || apiMessage.includes('not exist')) {
    return {
      title: '❌ Slot Not Found',
      message: 'The selected time slot is no longer available. Please refresh and select another slot.',
    };
  }


  if (apiMessage.includes('already has') || apiMessage.includes('existing appointment')) {
    return {
      title: '⚠️ Email Already Booked',
      message: 'This email already has an appointment. Please use a different email or cancel your existing appointment.',
    };
  }


  if (apiMessage.includes('invalid') || apiMessage.includes('Invalid')) {
    return {
      title: '❌ Invalid Slot',
      message: 'The selected time slot is invalid. Please select a different slot.',
    };
  }


  if (apiMessage.includes('Network') || apiMessage.includes('network')) {
    return {
      title: '🌐 Connection Error',
      message: 'Unable to connect to the server. Please check your internet connection and try again.',
    };
  }


  if (apiMessage.includes('Internal server error') || apiMessage.includes('internal')) {
    return {
      title: '⚠️ Server Error',
      message: 'The server encountered an unexpected error. Please try again later or contact support if the problem persists.',
    };
  }


  return {
    title: '❌ Booking Failed',
    message: apiMessage || 'An unexpected error occurred. Please try again.',
  };
}

export default function ErrorModal({
  isOpen,
  message,
  details,
  onClose,
}: ErrorModalProps) {
  console.log('ErrorModal rendered:', { isOpen, message });

  if (!isOpen) return null;

  const { title, message: friendlyMessage } = parseErrorMessage(message);

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-2xl max-w-md w-full overflow-hidden transform transition-all">
          {/* Header with error icon */}
          <div className="bg-gradient-to-r from-red-500 to-red-600 p-6 text-center">
            <div className="flex justify-center mb-4">
              <div className="bg-white rounded-full p-3 w-16 h-16 flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-red-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            </div>
            <h2 className="text-2xl font-bold text-white">{title}</h2>
          </div>

          {/* Content */}
          <div className="p-6">
            <div className="space-y-4 mb-6">
              <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                <p className="text-red-900 font-semibold leading-relaxed">
                  {friendlyMessage}
                </p>
              </div>

              {details && (
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <p className="text-xs text-gray-600 font-mono">
                    Technical Details: {details}
                  </p>
                </div>
              )}

              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <p className="text-sm text-blue-900">
                  💡 <span className="font-semibold">Tip:</span> Try selecting another time slot or contact support if the problem persists.
                </p>
              </div>
            </div>

            {/* Close Button */}
            <button
              onClick={onClose}
              className="w-full bg-red-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-red-700 transition-colors"
            >
              Try Another Slot
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
