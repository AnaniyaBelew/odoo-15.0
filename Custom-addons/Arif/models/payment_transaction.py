import logging
from odoo.exceptions import UserError
import json
import uuid
import pprint
from werkzeug import urls,utils
from odoo import _, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != 'arifpay':
            return res
        payload = self._arifpay_prepare_payment_request_payload()
        prod=self.get_products(processing_values['reference'])
        items={'items':prod}
        benf=self.get_beneficeries(processing_values)
        _logger.info(benf)
        payload.update(items)
        _logger.info("sending '/payments' request for link creation:\n%s", pprint.pformat(payload))
        payment_data = self.acquirer_id._arifpay_make_request('/payments', data=payload)
        self.acquirer_reference = payment_data.get('nonce')
        checkout_url = payment_data["data"]["paymentUrl"]
        parsed_url = urls.url_parse(checkout_url)
        url_params = urls.url_decode(parsed_url.query)
        _logger.info("redirecting to checkout")
        utils.redirect(checkout_url)
        _logger.info("redirected")
        return {'api_url': checkout_url, 'url_params': url_params}

    def _arifpay_prepare_payment_request_payload(self):
        return {
                "cancelUrl": "https://example.com",
                "phone":"251944294981",
                "email":"natnael@arifpay.net",
                "nonce":str(uuid.uuid4()),
                "errorUrl": "http://error.com",
                "notifyUrl": "https://gateway.arifpay.net/test/callback",
                "successUrl": "http://example.com",
                "paymentMethods": [
                    "TELEBIRR"
                ],
                "expireDate": "2025-02-01T03:45:27",
                "beneficiaries": [
                    {
                        "accountNumber": "01320811436100",
                        "bank": "AWINETAA",
                        "amount": 2.0
                    }
                ],
                "lang": "EN"
        }
    def get_beneficeries(self,values):
        beneficiaries = []
        payment_journal = self.env['account.journal'].search([('type', '=', 'bank'), ('company_partner_id', '=', values.get('partner_id'))])
        _logger.info("journal",payment_journal)
        beneficiaries.append({
            'accountnumber': payment_journal.bank_acc_number,  
            'bank': payment_journal.display_name
            })
        return beneficiaries
    def get_total_price(self,items):
        total=0
        for item in items:
            total+=item['price']*item['quantity']
            
        return total
    def get_products(self, reference):
        txs = self.env['payment.transaction'].search([('reference', '=', reference)])
        txs[0].currency_id = self.company_id.currency_id
        sale_order = txs[0].sale_order_ids
        invoice_line = None
        image_url = None# Define invoice_line here
        if sale_order:
            products = sale_order[0].website_order_line
            if not products:
                raise UserError('Please Add Products')
        else:
            invoice_orders = txs[0].invoice_ids
            invoice_line = invoice_orders.invoice_line_ids
            products = invoice_line.product_id
        product_list = []
        x = 0
        for product in products:
            print(product.name)
            try:
                quantity = product.product_uom_qty
                price = product.price_unit
                image_url = product.product_id.image_url
            except:
                if invoice_line and image_url:  # Check if invoice_line is not None
                    quantity = invoice_line[x].quantity
                    price = invoice_line[x].price_unit
                    image_url = invoice_line[x].product_id.image_url
            product_list.append({"name": product.name,
                                "quantity": quantity,
                                "description": product.name,
                                "price": price,
                                "image": image_url})
            x = x + 1
        return product_list



    def _get_tx_from_feedback_data(self, provider, data):
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'arifpay':
            return tx

        tx = self.search([('reference', '=', data.get('nonce')), ('provider', '=', 'arifpay')])
        if not tx:
            raise ValidationError(
                "arifpay: " + _("No transaction found matching reference %s.", data.get('ref'))
            )
        return tx

    def _process_feedback_data(self, data):
        super()._process_feedback_data(data)
        if self.provider != 'arifpay':
            return
        payment_data = self.acquirer_id._arifpay_make_request(f'/payments/{self.acquirer_reference}', data)
        if payment_data['msg']=="No Errors":
            self._set_done()
            _logger.info("transaction")
            _logger.info(payment_data["data"]["paymentUrl"])
        else:
            self._set_canceled("arifpay: " + _("Failed payment"))
