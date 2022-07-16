{
    'name': 'Odoo Web Login Screen',
    'summary': 'The new configurable Odoo Web Login Screen',
    'version': '15.0',
    'category': 'Website',
    'summary': """
The new configurable Odoo Web Login Screen
""",
    'author': "Xao Xao Digital CO.,LTD",
    'website': "https://www.xaoxao.vn",
    'license': 'AGPL-3',
    'depends': [
    ],
    'data': [
        'data/ir_config_parameter.xml',
        'templates/website_templates.xml',
        'templates/webclient_templates.xml',
    ],
    'assets': {
        'web.assets_backend': {

        },
        'web.assets_frontend': {
            '/odoo_web_login/static/src/css/web_login_style.css',
        },
        'web.login_layout': {

        },
        'web.assets_qweb': {

        },
    },
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'images': ['static/description/banner.png'],
}
