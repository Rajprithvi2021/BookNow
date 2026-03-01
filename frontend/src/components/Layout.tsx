/**
 * Layout component with header and footer
 */

import React from 'react';
import Link from 'next/link';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <Link href="/">
              <div className="flex items-center cursor-pointer">
                <span className="text-2xl font-bold text-blue-600">
                  📅 BookNow
                </span>
              </div>
            </Link>
            <ul className="flex space-x-6">
              <li>
                <Link
                  href="/"
                  className="text-gray-700 hover:text-blue-600 transition"
                >
                  Book
                </Link>
              </li>
              <li>
                <Link
                  href="/appointments"
                  className="text-gray-700 hover:text-blue-600 transition"
                >
                  My Appointments
                </Link>
              </li>
            </ul>
          </div>
        </nav>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <p className="text-gray-600 text-sm">
            &copy; 2024 BookNow. Production-ready appointment booking system.
          </p>
          <p className="text-gray-500 text-xs mt-2">
            Features: Pessimistic locking • Idempotent mutations • No double-bookings
          </p>
        </div>
      </footer>
    </div>
  );
}
