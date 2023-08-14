{
    'name':'Price Analysis',
    'depends': ['stock', 'sale'],
    'description': """Price Analysis for products""",
    'author': 'Ziruma Labs',
    'category': 'Sales',
    'data': [
        #aqui la url de las vistas
        'security/ir.model.access.csv',
        'views/price_analysis.xml',
        # 'views/inherit_product_template_view.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': True,
    'license': 'Other proprietary',
}