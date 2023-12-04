import json
import logging
import requests
import werkzeug
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
from werkzeug import urls

import pprint


_logger = logging.getLogger(__name__)


class ArifpayReturnControler(http.Controller):
    global private
    global tx_ref
    @http.route('/begin', type='http', auth='public', csrf=False, methods=['POST'])
    def begin_transaction(self, **post):
        _logger.info(
            'arifpay : Begining to parse data and post to request URL')
        request_url = 'https://gateway.arifpay.org/api/sandbox/checkout/session'
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        self.private = post["x-arifpay-key"]
        self.tx_ref = post['nonce']
        request_headers = {
                "x-arifpay-key" : post["x-arifpay-key"],
                "Content-Type": "application/json",
        }
        post.pop('x-arifpay-key')
        print(post['items'])
        print(json.dumps(post['items']))
        req_data = {
            "phone": post["phone"],
            "email": post["email"],
            "nonce": post["nonce"],
            "beneficiaries": post["beneficiaries"],
            "paymentMethods" : post['paymentMethods'],
            "errorUrl" : str(urls.url_join(base_url, "/error")),
            "successUrl": str(urls.url_join(base_url, "/success")),
            "notifyUrl": str(urls.url_join(base_url, "/notify")),
        }

        try :
            response = requests.post(request_url, headers=request_headers, json=req_data)
        except Exception as e:
            print(e)
        if response.status_code >= 200 and response.status_code <= 300:
            _logger.info(
                'arifpay : Success in post request, set transaction to pending and redirect to new Transaction Url')
            response_json = response.json()
            request.env['payment.transaction'].sudo().form_feedback(post, 'arifpay')
            return werkzeug.utils.redirect(response_json["data"]["paymentUrl"])
        else :
            raise werkzeug.exceptions.BadRequest("Request not successful,Please check the keys or consult the admin.code-" + str(response.status_code))
            # return response.status_code
