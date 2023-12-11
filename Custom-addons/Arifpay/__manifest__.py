{
    'name': 'Arifpay Payment Acquirer',
    'version': '1.0',
    'category': 'Payment Acquirer',
    'summary': 'Payment Acquirer: Arifpay Implementation',
    'description': """Arifpay Payment Acquirer""",
    'depends': ['payment'],
    'sequence':"1",
    'data': [
        'views/payment_arifpay_templates.xml',
        'views/payment_form_arifpay.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
}