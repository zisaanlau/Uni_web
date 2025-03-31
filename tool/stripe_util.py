import json

from flask import jsonify

from core.models import PaymentIntentDetails, PaymentDetails, PaymentWebhook, PaymentChargeDetails, User
import stripe

def validate_stripe_webhook(request):
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(
            # payload, sig_header, 'whsec_XKTIQguMAHMrVtdh65FP0hshYwefIHYh'
            # 上面是生产，下面是测试
            payload, sig_header, 'whsec_1293fb67ba5d8d21a167467b4fb23955ee49acec78025b0531826a4b945f35ca'
        )
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': str(e)}), 400

    return event

def create_webhook_record(event):

    payload = event['data']['object']

    if event.type == 'checkout.session.completed':
        amount = payload['amount_total']
    else:
        amount = payload['amount']

    new_webhook = PaymentWebhook(
        external_id = payload['id'],
        name = event.type,
        amount = amount,
        client_secret = payload["client_secret"] if "client_secret" in payload and payload["client_secret"] is not None else ""
    )
    return new_webhook

def create_payment_details(payload):
    user_id = User.query.filter_by(username = payload['user_id']).first().id
    new_payment_details = PaymentDetails(
        user_id = user_id,
        status = 0,
        type = 0,
        amount = payload['amount'],
        currency = payload['currency'],
        payment_email = payload['payment_email'],
        dispute = 0,
        disputed = 0,
    )
    return new_payment_details

def create_payment_intent(payload):
    payment_intent_details = PaymentIntentDetails(
        external_id = payload['id'],
        client_secret = payload["client_secret"] if "client_secret" in payload and payload["client_secret"] is not None else "",
        latest_charge = payload['latest_charge'],
        type = 0,
        status = 1 if "status" in payload and payload["status"] == 'succeeded' else 0,
        amount_received = payload["amount_received"] if "amount_received" in payload else 0,
        amount = payload['amount']
    )
    return payment_intent_details


def create_payment_charge_details(event):
    type = None
    payload = event['data']['object']
    payment_method_details = payload['payment_method_details']
    if (payment_method_details['type'] == 'card'):
        type = 0
    payment_charge_details = PaymentChargeDetails(
        external_id = payload['id'],
        payment_intent_id = payload['payment_intent'],
        type = type,
        status = 0,
        amount = payload['amount'],
        amount_captured = 0,
        amount_authorized = payment_method_details['card']['amount_authorized'],
        currency = payload['currency'],
        brand = payment_method_details['card']['brand'],
        last4 = payment_method_details['card']['last4'],
        exp_month = payment_method_details['card']['exp_month'],
        exp_year = payment_method_details['card']['exp_year'],
        country = payment_method_details['card']['country'],
    )
    return payment_charge_details