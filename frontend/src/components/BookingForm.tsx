import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

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

  // Reset form when booking is successful or slot is deselected
  useEffect(() => {
    if (successMessage || !selectedSlotId) {
      setFormData({
        name: '',
        email: '',
        notes: '',
      });
    }
  }, [successMessage, selectedSlotId]);

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
      alert("Please select a time slot");
      return;
    }
    console.log("Submitting booking with data:", formData);
    await onSubmit(formData);
    console.log("Booking submission completed");
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Book Your Appointment</CardTitle>
        <CardDescription>Select a time slot and provide your details</CardDescription>
      </CardHeader>

      <CardContent>
        {!successMessage && (
          <>
            {/* Show form only if no success message */}
            {selectedDate && selectedTime && (
              <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-gray-600">Selected Time:</p>
                <p className="text-lg font-semibold text-blue-900">
                  {new Date(selectedDate).toLocaleDateString("en-US", {
                    weekday: "long",
                    month: "long",
                    day: "numeric",
                  })}{" "}
                  at {selectedTime}
                </p>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="name" className="text-sm font-medium text-gray-700 mb-1 block">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <Input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  placeholder="John Doe"
                />
              </div>

              <div>
                <label htmlFor="email" className="text-sm font-medium text-gray-700 mb-1 block">
                  Email <span className="text-red-500">*</span>
                </label>
                <Input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  placeholder="john@example.com"
                />
              </div>

              <div>
                <label htmlFor="notes" className="text-sm font-medium text-gray-700 mb-1 block">
                  Notes (Optional)
                </label>
                <Textarea
                  id="notes"
                  name="notes"
                  value={formData.notes}
                  onChange={handleChange}
                  placeholder="Any special requests or notes..."
                  rows={4}
                />
              </div>

              <Button
                type="submit"
                disabled={loading || !selectedSlotId}
                className="w-full"
              >
                {loading ? "Booking..." : "Confirm Booking"}
              </Button>
            </form>

            {!selectedSlotId && (
              <div className="p-4 bg-amber-50 border-l-4 border-amber-500 rounded mt-4">
                <p className="text-amber-900 text-sm font-medium">
                  👈 Select a time slot from the calendar to enable booking
                </p>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
