import hashlib
import hmac
import json
import urllib
import urllib.parse
import urllib.request
import random
import requests
from datetime import datetime
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
import urllib.parse
from django.utils import timezone
from datetime import timedelta
from hospital.forms import PaymentForm
from hospital.models import Appointment, Payment, PaymentDetail, Prescription
from hospital.vnpay import vnpay

from datetime import datetime, timedelta



def hmacsha512(key, data):
    byteKey = key.encode('utf-8')
    byteData = data.encode('utf-8')
    return hmac.new(byteKey, byteData, hashlib.sha512).hexdigest()

def payment(request, payment_id):
    payment = Payment.objects.get(pk=payment_id)
    if payment.payment_type == 'deposit':
        expired_time = payment.payment_timestamp + timedelta(minutes=30)
        if payment.payment_status == 'unpaid' and timezone.now() > expired_time:
            payment.payment_status = 'expired'
            payment.save()
            return render(request, "payment/payment_return.html", {
                "title": "Kết quả thanh toán",
                "result": "Hóa đơn đặt cọc đã hết hạn!",
                "order_id": payment.order_code,
                "amount": payment.total_amount,
                "order_desc": f"Thanh toan hoa don {payment.order_code}",
                "vnp_transaction_no": "",
                "vnp_response_code": "99",
                "payment": payment
            })
    vnp = vnpay()
    expire_date = (datetime.now() + timedelta(minutes=15)).strftime('%Y%m%d%H%M%S')  
    vnp.requestData = {
        'vnp_Version': '2.1.0',
        'vnp_Command': 'pay',
        'vnp_TmnCode': settings.VNPAY_TMN_CODE,
        'vnp_Amount': int(payment.total_amount * 100),
        'vnp_CurrCode': 'VND',
        'vnp_TxnRef': payment.order_code,
        'vnp_OrderInfo': f"Thanh toan hoa don {payment.order_code}",
        'vnp_OrderType': 'billpayment',
        'vnp_Locale': 'vn',
        'vnp_ReturnUrl': settings.VNPAY_RETURN_URL,
        'vnp_CreateDate': datetime.now().strftime('%Y%m%d%H%M%S'),
        'vnp_IpAddr': get_client_ip(request),
        'vnp_ExpireDate': expire_date,  
        
    }
    vnpay_payment_url = vnp.get_payment_url(settings.VNPAY_PAYMENT_URL, settings.VNPAY_HASH_SECRET_KEY)
    return redirect(vnpay_payment_url)


def payment_ipn(request):
    inputData = request.GET
    if inputData:
        vnp = vnpay()
        vnp.responseData = inputData.dict()
        order_code = inputData['vnp_TxnRef']
        amount = inputData['vnp_Amount']
        vnp_ResponseCode = inputData['vnp_ResponseCode']
        if vnp.validate_response(settings.VNPAY_HASH_SECRET_KEY):
            # Check & Update Order Status in your Database
            # Your code here
            firstTimeUpdate = True
            totalamount = True
            if totalamount:
                if firstTimeUpdate:
                    if vnp_ResponseCode == '00':
                        print('Payment Success. Your code implement here')
                    else:
                        print('Payment Error. Your code implement here')

                    # Return VNPAY: Merchant update success
                    result = JsonResponse({'RspCode': '00', 'Message': 'Confirm Success'})
                else:
                    # Already Update
                    result = JsonResponse({'RspCode': '02', 'Message': 'Order Already Update'})
            else:
                # invalid amount
                result = JsonResponse({'RspCode': '04', 'Message': 'invalid amount'})
        else:
            # Invalid Signature
            result = JsonResponse({'RspCode': '97', 'Message': 'Invalid Signature'})
    else:
        result = JsonResponse({'RspCode': '99', 'Message': 'Invalid request'})

    return result
def payment_return(request):
    inputData = request.GET
    if inputData:
        vnp = vnpay()
        vnp.responseData = inputData.dict()
        order_code = inputData['vnp_TxnRef']
        amount = int(inputData['vnp_Amount']) / 100
        vnp_response_code = inputData['vnp_ResponseCode']
        vnp_transaction_no = inputData.get('vnp_TransactionNo', 'N/A')

        try:
            payment = Payment.objects.get(order_code=order_code)
            if payment.payment_status == 'deposit':
            # đổi lại minutes nếu muốn thời gian hết hạn khác
                expired_time = payment.payment_timestamp + timedelta(minutes=30)
                if payment.payment_status == 'unpaid' and timezone.now() > expired_time:
                    payment.payment_status = 'expired'
                    payment.save()
                    return render(request, "payment/payment_return.html", {
                        "title": "Kết quả thanh toán",
                        "result": result,
                        "order_id": order_code,
                        "amount": amount,
                        "order_desc": order_desc,
                        "vnp_transaction_no": vnp_transaction_no,
                        "vnp_response_code": vnp_response_code,
                        "payment": payment,})

            order_desc = f"Thanh toan lich hen{payment.appointment.appointment_id}"
        except Payment.DoesNotExist:
            payment = None
            order_desc = "Không tìm thấy đơn hàng"

        if vnp.validate_response(settings.VNPAY_HASH_SECRET_KEY):
            if vnp_response_code == "00":
                result = "Thành công"
                if payment:
                    payment.payment_status = 'paid'
                    payment.payment_method = 'banking'
                    payment.vnp_create_date = inputData.get('vnp_PayDate', datetime.now().strftime('%Y%m%d%H%M%S'))
                    payment.save()
                    
                    # Cập nhật tất cả PaymentDetail liên quan
                    payment.details.update(detail_status='paid')
                    appointment = payment.appointment

                    if payment.payment_type == 'deposit':
                        appointment.appointment_status = 'pending'
                    elif payment.payment_type == 'exam':
                        appointment.appointment_status = 'full'
                    appointment.save()

                    if payment.payment_type == 'prescription':
                        Prescription.objects.filter(record__appointment=appointment).update(prescription_status='paid')
            else:
                result = "Thất bại"
        else:
            result = "Sai checksum"

        return render(request, "payment/payment_return.html", {
            "title": "Kết quả thanh toán",
            "result": result,
            "order_id": order_code,
            "amount": amount,
            "order_desc": order_desc,
            "vnp_transaction_no": vnp_transaction_no,
            "vnp_response_code": vnp_response_code,
            "payment": payment
        })
    else:
        return render(request, "payment/payment_return.html", {
            "title": "Kết quả thanh toán",
            "result": ""
        })
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

n = random.randint(10**11, 10**12 - 1)
n_str = str(n)
while len(n_str) < 12:
    n_str = '0' + n_str


def query(request):
    if request.method == 'GET':
        return render(request, "payment/query.html", {"title": "Kiểm tra kết quả giao dịch"})

    url = settings.VNPAY_API_URL
    secret_key = settings.VNPAY_HASH_SECRET_KEY
    vnp_TmnCode = settings.VNPAY_TMN_CODE
    vnp_Version = '2.1.0'

    vnp_RequestId = n_str
    vnp_Command = 'querydr'
    vnp_TxnRef = request.POST['order_id']
    vnp_OrderInfo = 'kiem tra gd'
    vnp_TransactionDate = request.POST['trans_date']
    vnp_CreateDate = datetime.now().strftime('%Y%m%d%H%M%S')
    vnp_IpAddr = get_client_ip(request)

    hash_data = "|".join([
        vnp_RequestId, vnp_Version, vnp_Command, vnp_TmnCode,
        vnp_TxnRef, vnp_TransactionDate, vnp_CreateDate,
        vnp_IpAddr, vnp_OrderInfo
    ])

    secure_hash = hmac.new(secret_key.encode(), hash_data.encode(), hashlib.sha512).hexdigest()

    data = {
        "vnp_RequestId": vnp_RequestId,
        "vnp_TmnCode": vnp_TmnCode,
        "vnp_Command": vnp_Command,
        "vnp_TxnRef": vnp_TxnRef,
        "vnp_OrderInfo": vnp_OrderInfo,
        "vnp_TransactionDate": vnp_TransactionDate,
        "vnp_CreateDate": vnp_CreateDate,
        "vnp_IpAddr": vnp_IpAddr,
        "vnp_Version": vnp_Version,
        "vnp_SecureHash": secure_hash
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_json = json.loads(response.text)
    else:
        response_json = {"error": f"Request failed with status code: {response.status_code}"}

    return render(request, "payment/query.html", {"title": "Kiểm tra kết quả giao dịch", "response_json": response_json})