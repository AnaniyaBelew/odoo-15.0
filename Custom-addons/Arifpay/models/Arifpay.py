from odoo.exceptions import ValidationError
from odoo import api, fields, models
from odoo.exceptions import UserError

import json
from werkzeug import urls
import pprint

import logging

_logger = logging.getLogger(__name__)


class PaymentAcquirerArifpay(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('Arifpay', 'Arifpay')],ondelete={'Arifpay': 'set default'})

    Arifpay_API_key = fields.Char('Api-Key', required_if_provider='Arifpay',
                                       groups='base.group_user')
    @api.model
    def _get_arifpay_urls(self):
        """ Atom URLS """
        return {
            'arifpay_form_url': '/begin'
        }

    def arifpay_get_form_action_url(self):
        return self._get_arifpay_urls()['arifpay_form_url']

    def arifpay_form_generate_values(self, values):
        _logger.info(
            'arifpay : preparing all form values to send to arifpay form url')
        product_list = self.get_products(values['reference'])
        request_string = self.validate_data(values)

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        request_string.update({
            'x-arifpay-key': self.Arifpay_API_key,
            'items': product_list,
            'successUrl': urls.url_join(base_url, '/success'),
            'errorUrl': urls.url_join(base_url, '/error'),
            'cancelUrl': urls.url_join(base_url, '/cancel'),
            'notifyUrl': urls.url_join(base_url, '/notify'),
            
            
        })
        return request_string

    def get_products(self, reference):
        txs = self.env['payment.transaction'].search([('reference', '=', reference)])
        txs[0].currency_id = self.company_id.currency_id
        sale_order = txs[0].sale_order_ids
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
            except:
                quantity = invoice_line[x].quantity
            product_list.append({"name": product.name,
                                 "quantity": quantity,
                                 "price":product.price_unit,
                                "description":product.name,
                                "image":""})
            x = x + 1
        product_list = json.dumps(product_list)
        print(product_list)
        return product_list

    def validate_data(self, values):
        _logger.info(
            'arifpay: Validating all form data')
        if not values['paymentMethods'] \
                or not values['expireDate'] \
                or not values['reference']:
            raise UserError(
                'Please Insert all available information about customer' + '\n Payment Method'
                                                                           '\n Expire Date''\n Phone number')
        request_string = {
            "paymentMethods": values['paymentMethods'],
            "expireDate": values['expireDate'],
            "email": values['email'],
            "phone": values['phone'],
            "nonce": values['reference'],
            "beneficiaries": values['beneficiaries'],
        }
        return request_string


class PaymentTransactionarifpay(models.Model):
    _inherit = 'payment.transaction'

    arifpay_txn_type = fields.Char('Transaction type')

    @api.model
    def _arifpay_form_get_tx_from_data(self, data):
        if data.get('tx_ref') :
            tx_ref = data.get('tx_ref')
        else :
            tx_ref = data.get('data').get('tx_ref')
        txs = self.search([('reference', '=', tx_ref)])
        return txs

    def _arifpay_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        return invalid_parameters

    def _arifpay_form_validate(self, data):
        _logger.info(
            'arifpay: Validate transaction pending or done')

        if data.get('status') == 'success' :
            tx_ref = data.get('data').get('tx_ref')
            res = {
                'acquirer_reference': tx_ref
            }
            self._set_transaction_done()
            self.write(res)
            _logger.info(
                'arifpay: Done when called transaction done from notify URL')
            return True
        else:
            self._set_transaction_pending()
            return True
