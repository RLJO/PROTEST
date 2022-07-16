# Copyright 2016 Savoir-faire Linux
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Onlogis 15",
    "version": "14.0.1.0.0",
    "author": "Medab",
    "website": "onlogis.com",
    "license": "AGPL-3",
    "category": "Web",
    "summary": "Remove the bubbles from the web interface and add the web window title management feature",
    "depends": ["web"],
    "data": [
        'data/demo.xml',
        'views/res_config.xml'
    ],
    'assets': {
        'web.assets_backend': {
            "/onlogis/static/src/css/web_no_bubble.scss"
        },
        'web.assets_frontend': {
            "/onlogis/static/src/css/web_no_bubble.scss"
        },
    },

    "installable": True,
    "application": False,
}
