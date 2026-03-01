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
                  onClick={() => onSelectSlot(slot.id, slot.slot_date, slot.slot_time)}
                  className={`px-4 py-3 rounded-lg text-sm font-medium transition ${
                    selectedSlotId === slot.id
                      ? 'bg-blue-600 text-white ring-2 ring-blue-400'
                      : 'bg-white border border-gray-300 text-gray-900 hover:border-blue-500'
                  }`}
                >
                  {slot.slot_time}
                </button>
              ))}
            </div>
          </div>
        ))}
    </div>
  );
}
