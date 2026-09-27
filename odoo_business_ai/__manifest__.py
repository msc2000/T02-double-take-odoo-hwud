{
    'name': 'OdooPulse',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'AI-powered business decision assistant for SMEs',
    'depends': ['base', 'product', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/business_ai_views.xml',
        'views/business_ai_menus.xml',
    ],
    'installable': True,
    'application': True,
}