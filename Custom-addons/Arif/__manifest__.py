{
    'name': 'Arifpay Payment updated',
    'version': '1.0',
    'category': 'Payment Acquirer',
    'summary': 'Payment Acquirer: Arifpay Implementation',
    'description': """Arifpay Payment Acquirer""",
    'depends': ['payment'],
    'sequence': -50,
    'data': [
        'views/payment_mollie_templates.xml',
        'views/payment_views.xml',
        'data/payment_aquirer_data.xml',
    ],
    'aplication': True,
}