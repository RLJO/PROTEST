import datetime

from odoo import http
from odoo.http import request


class SubscriptionController(http.Controller):

    @http.route('/subscriptions', auth='public', type='json', methods=["GET", "POST"])
    def get_subscriptions_list(self):
        """ Returns an array of all subscriptions"""

        subs = request.env['subscription.subscription'].sudo().search_read([], [])
        return {
            'status': 200, 'message': 'Success', 'subscriptions': subs
        }

    @http.route('/subscriptions/<email>', auth='public', type='json', methods=["GET", "POST"])
    def get_user_subscriptions(self, email):
        """ Returns an array of all specified user subscriptions"""

        subs = request.env['subscription.subscription'].sudo().search_read(
            [('customer_name.email', '=', email)], [])
        return {
            'status': 200, 'message': 'Success', 'subscriptions': subs
        }

    @http.route('/subscriptions/create/<email>', auth='public', type='json', methods=["GET", "POST"])
    def create_subscriptions(self, email):
        """ Create subscription for a given client account"""
        vals = http.request.params

        """ check if there is a customer with the given email address """
        customer = request.env['res.partner'].sudo().search([('email', '=', email)])
        if not customer:
            return {
                'status': 404, 'message': 'Customer not found'
            }
        customer = customer[0]
        if not customer:
            return {
                'status': 404, 'message': 'Customer not found'
            }
        product = request.env['product.product'].sudo().search([('name', '=', "Instance tracking")])
        if not product:
            return {
                'status': 404, 'message': 'Customer not found'
            }
        product = product[0]
        if not product:
            return {
                'status': 404, 'message': 'Instance not available'
            }
        """ Create a subscription for this customer account """
        so_vals = {
            'partner_id': customer.id,
            'state': 'sale'
        }
        res_so = request.env['sale.order'].sudo().create(so_vals)
        so_line_vals = {
            'order_id': res_so.id,
            'product_id': product.id,
            'product_uom_qty': vals.get('quantity')
        }
        res_so_line = request.env['sale.order.line'].sudo().create(so_line_vals)
        sub_vals = {
            'customer_name': customer.id,
            'source': vals.get('source') or 'manual',
            'so_origin': res_so.id,
            'product_id': product.id,
            'quantity': vals.get('quantity'),
            'price': vals.get('price'),
            'sub_plan_id': vals.get('sub_plan_id') or 1,
            'start_date': datetime.date.today(),
            'duration': vals.get('duration'),
            'end_date': datetime.date.today() + datetime.timedelta(days=vals.get('duration') * 30),
            'unit': 'month',  # vals.get('unit')
            'num_billing_cycle': 1,
            'state': vals.get('state') or 'draft',
        }
        sub = request.env['subscription.subscription'].sudo().create(sub_vals)

        return {
            'status': 200,
            'message': 'Success',
            'subscription': {
                "id": sub.id,
                "name": sub.name,
                "customer": sub.customer_name.email,
                "start_date": sub.start_date,
                "end_date": sub.end_date
            }
        }
