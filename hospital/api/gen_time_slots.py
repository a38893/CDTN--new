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

class TimeSlotAPI(APIView):
    def get(self, request):
        slots = generate_time_slots()
        return Response({"time_slots": slots}, status=status.HTTP_200_OK)