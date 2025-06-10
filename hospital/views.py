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

from hospital.forms import PaymentForm
from hospital.models import Appointment, Payment, PaymentDetail
from hospital.vnpay import vnpay




def hmacsha512(key, data):
    byteKey = key.encode('utf-8')
    byteData = data.encode('utf-8')
    return hmac.new(byteKey, byteData, hashlib.sha512).hexdigest()
def payment(request, payment_id=None):
    if request.method == 'GET':
        if not payment_id:
            return render(request, "payment/payment.html", {
                "title": "Thanh toán",
                "error": "Không tìm thấy hóa đơn cần thanh toán."
            })
        try:
            payment = Payment.objects.get(pk=payment_id, payment_status__in=['unpaid', 'pending'])
            appointment = payment.appointment

            # Nếu là đặt cọc và chưa có PaymentDetail thì tạo mới
            if payment.payment_type == 'deposit' and not payment.details.exists():
                PaymentDetail.objects.create(
                    payment=payment,
                    service_type='deposit',
                    service_id=0,
                    service_name='Đặt cọc lịch hẹn',
                    amount=30000,
                    detail_status='unpaid'
                )
        except Payment.DoesNotExist:
            return render(request, "payment/payment.html", {
                "title": "Thanh toán",
                "error": "Không có hóa đơn chưa thanh toán với mã này."
            })
        return render(request, "payment/payment.html", {
            "title": "Thanh toán",
            "appointment": appointment,
            "amount": payment.total_amount,
            "payment_type": payment.payment_type,
            "payment": payment
        })

    if request.method == 'POST':
        bank_code = request.POST.get('bank_code', '')
        language = request.POST.get('language', 'vn')
        ipaddr = get_client_ip(request)
        payment_id = request.POST.get('payment_id')

        try:
            payment = Payment.objects.get(pk=payment_id, payment_status__in=['unpaid', 'pending'])
            appointment = payment.appointment
            # Nếu là đặt cọc và chưa có PaymentDetail thì tạo mới
            if payment.payment_type == 'deposit' and not payment.details.exists():
                try:
                    PaymentDetail.objects.create(
                        payment=payment,
                        service_type='deposit',
                        service_id=0,
                        service_name='Đặt cọc lịch hẹn',
                        amount=30000,
                        detail_status='unpaid'
                    )
                    print("Đã tạo PaymentDetail cho đặt cọc")
                except Exception as e:
                    print("Lỗi tạo PaymentDetail:", e)
        except Payment.DoesNotExist:
            print("Lỗi tạo paymentdetail:", payment_id)
            return render(request, "payment/payment.html", {
                "title": "Thanh toán",
                "error": "Không có hóa đơn chưa thanh toán với mã này."
            })

        amount = payment.total_amount
        order_desc = f"Thanh toán {payment.get_payment_type_display()} cho lịch hẹn #{appointment.appointment_id}"
        order_type = "billpayment"

        vnp = vnpay()
        vnp.requestData['vnp_Version'] = '2.1.0'
        vnp.requestData['vnp_Command'] = 'pay'
        vnp.requestData['vnp_TmnCode'] = settings.VNPAY_TMN_CODE
        vnp.requestData['vnp_Amount'] = int(amount * 100)
        vnp.requestData['vnp_CurrCode'] = 'VND'
        vnp.requestData['vnp_TxnRef'] = payment.order_code
        vnp.requestData['vnp_OrderInfo'] = order_desc
        vnp.requestData['vnp_OrderType'] = order_type
        vnp.requestData['vnp_Locale'] = language if language else 'vn'
        if bank_code:
            vnp.requestData['vnp_BankCode'] = bank_code

        vnp_create_date = datetime.now().strftime('%Y%m%d%H%M%S')
        vnp.requestData['vnp_CreateDate'] = vnp_create_date
        vnp.requestData['vnp_IpAddr'] = ipaddr
        vnp.requestData['vnp_ReturnUrl'] = settings.VNPAY_RETURN_URL

        # Lưu lại vnp_create_date vào payment
        payment.vnp_create_date = vnp_create_date
        payment.save()

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
            # Lấy order_desc từ thông tin đã lưu khi tạo Payment
            order_desc = f"Thanh toán lịch hẹn #{payment.appointment.appointment_id}"
        except Payment.DoesNotExist:
            payment = None
            order_desc = "Không tìm thấy đơn hàng"

        if vnp.validate_response(settings.VNPAY_HASH_SECRET_KEY):
            if vnp_response_code == "00":
                result = "Thành công"
                if payment:
                    payment.payment_status = 'paid'
                    payment.payment_method = 'banking'
                    payment.save()
                    
                    # Cập nhật tất cả PaymentDetail liên quan
                    payment.details.update(detail_status='paid')
                    appointment = payment.appointment
                    appointment.appointment_status = 'confirmed'
                    appointment.save()
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
