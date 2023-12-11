import werkzeug
from odoo import http
from odoo.http import request
import requests
import logging
_logger = logging.getLogger(__name__)
class ArifpayController(http.Controller):
    @http.route(['/payment/arifpay/feedback'], type='http', auth='none', csrf=False)
    def arifpay_form_feedback(self, **post):
        # Retrieve the transaction
        tx = None
        if post.get('nonce'):
            tx = request.env['payment.transaction'].sudo().search([('reference', '=', post.get('nonce'))])

        # Validate the transaction
        if tx and tx.state == 'draft':
            # TODO: Check the response from Arifpay (e.g., post.get('status')) and update the transaction state accordingly
            if post.get('status') == 'success':
                tx._set_transaction_done()
                tx.write({'acquirer_reference': post.get('nonce')})
            elif post.get('status') == 'pending':
                tx._set_transaction_pending()
            else:
                tx._set_transaction_cancel()
        request_url="https://gateway.arifpay.org/api/sandbox/checkout/session"
        request_headers = {
                "Authorization" : "Bearer " + post["x-arifpay-key"],
                "Content-Type": "application/json",
        }
        post.pop('x-arifpay-key')
        req_data = {
            "email": post["email"],
            "phone": post["phone"],
            "cancelUrl": post["cancelUrl"],
            "nonce": "nonce",
            "paymentMethod": ["TELEBIRR"],
            "successurl" : post['successurl'],
            "beneficiaries" : post['beneficiaries'],
            "items" : post['items'],
        }
        response = requests.post(request_url, headers=request_headers, json=req_data)
        if response.status_code >= 200 and response.status_code <= 300:
            _logger.info(
                'Arifpay : Success in post request, set transaction to pending and redirect to new Transaction Url')
            response_json = response.json()
            post.update({
                'tx_ref': post['nonce']
            })
            _logger.info('tx_values: %s', tx)
            request.render('Arifpay.payment_form_arifpay_template', {'tx_values': tx})
            return werkzeug.utils.redirect(response_json["data"]["paymentUrl"])
        else :
            raise werkzeug.exceptions.BadRequest("Request not successful,Please check the keys or consult the admin.code-" + str(response.status_code))
        # Render the feedback page
       
