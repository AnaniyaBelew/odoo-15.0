# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

import requests
from werkzeug import urls

from odoo import _, api, fields, models, service
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)

class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(
        selection_add=[('arifpay', 'Arifpay')], ondelete={'arifpay': 'set default'}
    )
    arifpay_api_key = fields.Char(
        string="Arifpay API Key",
        help="Merchants Api Key",
        required_if_provider="arifpay", groups="base.group_system"
    )

    #=== BUSINESS METHODS ===#

    @api.model
    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != 'arifpay':
            return super()._get_default_payment_method_id()
        return self.env.ref('Arif.payment_method_arifpay').id

    def _arifpay_make_request(self, endpoint, data=None, method='POST'):
        """ Make a request at arifpay endpoint.

        Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request
        :param dict data: The payload of the request
        :param str method: The HTTP method of the request
        :return The JSON-formatted content of the response
        :rtype: dict
        :raise: ValidationError if an HTTP error occurs
        """
        self.ensure_one()
        headers = {
            "x-arifpay-key": self.arifpay_api_key,
            "Content-Type": "application/json",
        }
        try:
            response = requests.request(method, "https://gateway.arifpay.org/api/sandbox/checkout/session", json=data, headers=headers, timeout=60)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            _logger.exception("Unable to communicate with : %s", "https://gateway.arifpay.org/api/sandbox/checkout/session")
            raise ValidationError("arif: " + _("Could not establish the connection to the API."))
        return response.json()
