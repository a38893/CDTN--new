from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta

def generate_time_slots():
    slots = []
    # Buổi sáng
    start = datetime.strptime("08:00", "%H:%M")
    end = datetime.strptime("11:45", "%H:%M")
    while start <= end:
        slots.append(start.strftime("%H:%M"))
        start += timedelta(minutes=15)
    # Buổi chiều
    start = datetime.strptime("13:30", "%H:%M")
    end = datetime.strptime("16:45", "%H:%M")
    while start <= end:
        slots.append(start.strftime("%H:%M"))
        start += timedelta(minutes=15)
    return slots

def is_valid_appointment_time(appointment_time):
    # Chuyển về chuỗi HH:MM để so sánh
    if isinstance(appointment_time, str):
        try:
            time_str = datetime.strptime(appointment_time, "%H:%M").strftime("%H:%M")
        except Exception:
            return False
    else:
        time_str = appointment_time.strftime("%H:%M")
    valid_slots = generate_time_slots()
    return time_str in valid_slots
class TimeSlotAPI(APIView):
    def get(self, request):
        slots = generate_time_slots()
        return Response({"time_slots": slots}, status=status.HTTP_200_OK)