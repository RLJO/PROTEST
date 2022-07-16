from odoo import http
from odoo.http import request

class PartnerController(http.Controller):

    @http.route('/partners/create', auth='public', type='json', methods=["POST"])
    def create_partner(self):
        vals = http.request.params
        """ Create a partner account """
        state_obj = request.env['res.country.state']
        country_obj = request.env['res.country']

        partner_vals = {
            'name': vals.get('name'),
            'street': vals.get('street') or '',
            'street2': vals.get('street2') or '',
            'city': vals.get('city') or '',
            'phone': vals.get('phone') or '',
            'mobile': vals.get('mobile') or '',
            'email': vals.get('email') or '',
            'company_type': vals.get('ctype'),
            'website': vals.get('website') or '',
            'zip': vals.get('zip') or '',
        }
        state = state_obj.sudo().search(
            [('name', '=', vals.get('state'))])
        country = country_obj.sudo().search(
            [('name', '=', vals.get('country'))])

        partner_vals['state_id'] = state.id or ''
        partner_vals['country_id'] = country.id or ''

        res = request.env['res.partner'].sudo().create(partner_vals)
        if res:
            return {
                'status': 200, 'message': 'Success',
                'account': {"id": res.id, "name": res.name, "email": res.email, "phone": res.phone}
            }
        return {
            'status': 400, 'message': 'Bad Request'
        }
