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
    const availableSlots = slots.filter(slot => slot.is_available);
    
    const grouped = availableSlots.reduce(
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

  const availableSlots = slots.filter(s => s.is_available);
  const bookedSlots = slots.filter(s => !s.is_available);

  if (availableSlots.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500 mb-2">No available slots found.</p>
        {bookedSlots.length > 0 && (
          <p className="text-sm text-gray-400">All slots for this period are booked. Please try another month.</p>
        )}
      </div>
    );
  }

  const totalSlots = availableSlots.length;
  const allSlots = slots.length;
  const unAvailableSlots = allSlots - totalSlots;

  return (
    <div className="space-y-6">
      {/* Legend - Only show available count */}
      <div className="grid grid-cols-1 gap-4 pb-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <div className="px-4 py-2 bg-white border border-green-300 rounded text-xs font-medium text-green-900">
            ✓ Available
          </div>
          <span className="text-sm text-gray-600">{totalSlots} slots ready to book</span>
        </div>
      </div>

      {/* Calendar */}
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
                      ? 'bg-green-600 text-white ring-2 ring-green-400 shadow-lg'
                      : 'bg-white border border-green-300 text-gray-900 hover:bg-green-50 hover:border-green-500 hover:shadow'
                  }`}
                >
                  <span className="text-xs block mb-1">✓ Available</span>
                  {slot.slot_time}
                </button>
              ))}
            </div>
          </div>
        ))}
    </div>
  );
}
