from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)
class ArifpayPaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'
    provider = fields.Selection(selection_add=[('Arifpay', 'Arifpay')])
    api_key = fields.Char('Api-Key', required_if_provider='Chapa',
                                       groups='base.group_user')
    @api.model
    def _get_urls(self):
        """ Atom URLS """
        return {
            'chapa_form_url': '/begin'
        }
    def _get_form_action_url(self):
        return self._get_chapa_urls()['chapa_form_url']
    def _generate_form_values(self, values):
        _logger.info(
            'Arifpay : preparing all form values to send to the Gateway form url')
        product_list = self.get_products(values['reference'])
        request_string = self.validate_data(values)

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        request_string.update({
            'private_key': self.chapa_private_key,
            'public_key': self.chapa_public_key,
            'products': product_list,
            'return_url': urls.url_join(base_url, '/returnUrl')
        })
        return request_string