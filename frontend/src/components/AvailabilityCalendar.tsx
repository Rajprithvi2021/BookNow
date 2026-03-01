/**
 * Available slots calendar component
 */

import React, { useEffect, useState } from 'react';

interface Slot {
  id: string;
  slot_date: string;
  slot_time: string;
  duration_minutes: number;
  is_available: boolean;
  created_at: string;
}

interface AvailabilityCalendarProps {
  slots: Slot[];
  selectedSlotId?: string;
  onSelectSlot: (slotId: string, date: string, time: string) => void;
  loading?: boolean;
}

export default function AvailabilityCalendar({
  slots,
  selectedSlotId,
  onSelectSlot,
  loading = false,
}: AvailabilityCalendarProps) {
  const [groupedByDate, setGroupedByDate] = useState<
    Record<string, Slot[]>
  >({});

  useEffect(() => {
    const grouped = slots.reduce(
      (acc, slot) => {
        if (!acc[slot.slot_date]) {
          acc[slot.slot_date] = [];
        }
        acc[slot.slot_date].push(slot);
        return acc;
      },
      {} as Record<string, Slot[]>
    );

    setGroupedByDate(grouped);
  }, [slots]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-10 bg-gray-200 rounded animate-pulse" />
        <div className="h-10 bg-gray-200 rounded animate-pulse" />
      </div>
    );
  }

  if (slots.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">No available slots found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {Object.entries(groupedByDate)
        .sort(([dateA], [dateB]) => dateA.localeCompare(dateB))
        .map(([date, daySlots]) => (
          <div key={date}>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              {new Date(date).toLocaleDateString('en-US', {
                weekday: 'long',
                month: 'long',
                day: 'numeric',
              })}
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              {daySlots.map((slot) => (
                <button
                  key={slot.id}
                  onClick={() => {
                    if (slot.is_available) {
                      onSelectSlot(slot.id, slot.slot_date, slot.slot_time);
                    }
                  }}
                  disabled={!slot.is_available}
                  className={`px-4 py-3 rounded-lg text-sm font-medium transition ${
                    !slot.is_available
                      ? 'bg-gray-200 text-gray-400 cursor-not-allowed opacity-60 line-through'
                      : selectedSlotId === slot.id
                      ? 'bg-green-600 text-white ring-2 ring-green-400'
                      : 'bg-white border border-green-300 text-gray-900 hover:bg-green-50 hover:border-green-500'
                  }`}
                >
                  {slot.is_available ? (
                    <>
                      <span className="text-xs block mb-1">✓ Available</span>
                      {slot.slot_time}
                    </>
                  ) : (
                    <>
                      <span className="text-xs block mb-1">✗ Booked</span>
                      {slot.slot_time}
                    </>
                  )}
                </button>
              ))}
            </div>
          </div>
        ))}
    </div>
  );
}
