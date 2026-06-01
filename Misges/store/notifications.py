import json
import logging
from urllib import request as urllib_request
from urllib.error import URLError

from django.template.defaultfilters import urlencode

from .models import StoreSettings

logger = logging.getLogger(__name__)


def send_sms(to: str, message: str) -> bool:
    settings = StoreSettings.load()
    if not settings.sms_api_key or not settings.sms_api_url:
        logger.warning('SMS non envoyé : clé API ou URL non configurée.')
        return False
    payload = json.dumps({
        'to': to,
        'message': message,
        'from': settings.sms_from or None,
    }).encode()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {settings.sms_api_key}',
        'Accept': 'application/json',
    }
    try:
        req = urllib_request.Request(settings.sms_api_url, data=payload, headers=headers, method='POST')
        with urllib_request.urlopen(req, timeout=15) as resp:
            if resp.status == 201 or resp.status == 200:
                logger.info(f'SMS envoyé à {to}')
                return True
            logger.warning(f'SMS échec HTTP {resp.status} : {resp.read().decode()}')
            return False
    except URLError as e:
        logger.error(f'Erreur envoi SMS vers {to} : {e}')
        return False


def send_sms_debt_reminder(debt) -> bool:
    message = (
        f'Rappel de dette - {debt.person}\n'
        f'Montant : {debt.amount} FCFA\n'
        f'Échéance : {debt.due_date}\n'
        f'Merci de régulariser votre situation.'
    )
    phone = _extract_phone(debt.person)
    if not phone:
        return False
    return send_sms(phone, message)


def send_sms_order_delivered(order) -> bool:
    message = (
        f'Bonjour {order.customer_name},\n'
        f'Votre commande #{order.id} a été livrée.\n'
        f'Total : {order.total} FCFA\n'
        f'Merci de votre confiance !'
    )
    phone = _extract_phone(order.customer_phone)
    if not phone:
        return False
    return send_sms(phone, message)


def send_whatsapp(to: str, message: str) -> bool:
    settings = StoreSettings.load()
    if not settings.whatsapp_api_key or not settings.whatsapp_phone_number_id:
        logger.warning('WhatsApp non envoyé : clé API ou ID téléphone non configuré.')
        return False
    url = f'https://graph.facebook.com/v18.0/{settings.whatsapp_phone_number_id}/messages'
    payload = json.dumps({
        'messaging_product': 'whatsapp',
        'to': to,
        'type': 'text',
        'text': {'body': message},
    }).encode()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {settings.whatsapp_api_key}',
    }
    try:
        req = urllib_request.Request(url, data=payload, headers=headers, method='POST')
        with urllib_request.urlopen(req, timeout=15) as resp:
            if resp.status in (200, 201):
                logger.info(f'WhatsApp envoyé à {to}')
                return True
            logger.warning(f'WhatsApp échec HTTP {resp.status}')
            return False
    except URLError as e:
        logger.error(f'Erreur envoi WhatsApp vers {to} : {e}')
        return False


def _extract_phone(text: str) -> str | None:
    import re
    if not text:
        return None
    digits = re.sub(r'\D', '', text)
    if len(digits) >= 8:
        return digits
    return None
