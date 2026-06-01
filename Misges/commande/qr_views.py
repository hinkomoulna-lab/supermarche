import io, os, qrcode
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings


def qr_display(request):
    host = request.get_host()
    order_url = f'http://{host}/commande/'
    img = qrcode.make(order_url, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    import base64
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    return render(request, 'commande/qr_display.html', {
        'qr_data': qr_b64,
        'order_url': order_url,
    })


def qr_download(request):
    host = request.get_host()
    order_url = f'http://{host}/commande/'
    img = qrcode.make(order_url, box_size=20, border=4)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    resp = HttpResponse(buf.getvalue(), content_type='image/png')
    resp['Content-Disposition'] = 'attachment; filename="qr_commande.png"'
    return resp
