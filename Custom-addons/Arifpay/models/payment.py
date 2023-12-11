from odoo import api, fields, models
import uuid
import logging
_logger = logging.getLogger(__name__)
class PaymentAcquirerArifpay(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('arifpay', 'Arifpay')],ondelete={'arifpay': 'set default'})

    arifpay_api_key = fields.Char(string='Arifpay API Key', required_if_provider='arifpay')
    @api.onchange('provider')
    def _form_generate_values(self, values):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        arifpay_tx_values = dict(values)
        
        # Get the beneficiaries from the payment journal
        beneficiaries = []
        payment_journal = self.env['account.journal'].search([('type', '=', 'bank'), ('bank_account_id', '=', values.get('partner_id'))])
        for beneficiary in payment_journal.bank_account_id.beneficiaries:
            beneficiaries.append({
                'accountnumber': beneficiary.account_number,
                'bankcode': beneficiary.bank_id.bic,
                'totalamount': beneficiary.total_amount,
            })
        
        # Get the items from the cart
        items = []
        order = self.env['sale.order'].search([('partner_id', '=', values.get('partner_id')), ('state', '=', 'draft')])
        for line in order.order_line:
            items.append({
                'name': line.product_id.name,
                'quantity': line.product_uom_qty,
                'price': line.price_unit,
                'description': line.name,
                'imageurl': '/web/image/product.product/%s/image_1920' % line.product_id.id,
            })
        
        arifpay_tx_values.update({
            'x-arifpay-key':self.arifpay_api_key,
            'email': values.get('partner_email'),
            'phone': values.get('partner_phone'),
            'cancelurl': '%s/payment/arifpay/cancel' % base_url,
            'errorurl': '%s/payment/arifpay/error' % base_url,
            'successurl': '%s/payment/arifpay/success' % base_url,
            'nonce': str(uuid.uuid4()),  # generates a unique id
            'beneficiaries': beneficiaries,
            'items': items,
        })
        _logger.info("model:",arifpay_tx_values)
        file = open('C:\\Users\\user\\Documents\\odoo.txt', 'w')
        file.write("MODEL\n")
        file.close()
        return arifpay_tx_values

    def _get_form_action_url(self):
        # TODO: Return the URL of the Arifpay API here
        _logger.info("get form acttion")
        return '/payment/arifpay/feedback'
