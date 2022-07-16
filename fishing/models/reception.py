from io import BytesIO

from odoo import fields, models, api, _
from datetime import datetime
import qrcode
import base64


class Da(models.Model):
    _name = 'fishing.reception'
    _rec_name = 'ref'

    type_choices = [('production', 'Production'), ('service', 'Service')]
    status_choices = [
        ('0', 'Waiting for treatment'),
        ('1', 'Treatment in progress'),
        ('2', 'Treated'),
        ('3', 'Tunnels in progress'),
        ('4', 'Tunneled'),
        ('5', 'Packaging in progress'),
        ('6', 'Packed'),
    ]
    ref = fields.Char(string='Reference', required=True, readonly=True, default=lambda self: _('New'))

    qr_code = fields.Binary("QR Code", attachment=True, readonly=True)

    type = fields.Selection(type_choices, string='Type', required=True, default='production', tracking=True)

    status = fields.Selection(status_choices, required=False, default='0', tracking=True)

    mareyeur = fields.Many2one(comodel_name='res.partner', string='Fish seller')

    customer_id = fields.Many2one(comodel_name='res.partner', string='Customer')

    responsible_id = fields.Many2one(comodel_name='res.users', string='Responsible',
                                     default=lambda self: self.env.user.id)

    team_id = fields.Many2one(comodel_name='res.users', string='Team', domain="[('id','=','0')]")

    bateau = fields.Many2one(comodel_name='maintenance.equipment', string='Boat', required=False,
                             domain="[('category_id.name','ilike','Bateau')]")

    date = fields.Datetime(string='Date', required=False, default=fields.Datetime.now)

    treatment_ordered = fields.Boolean(string='Treatment', required=False, default=False)

    tunnel_ordered = fields.Boolean(string='Tunnel', required=False, default=False)

    packaging_ordered = fields.Boolean(string='Packaging', required=False, default=False)

    ordered_temp = fields.Float(string='Temperature', required=False, default=0.0)
    exp_payment = fields.Float(string="Expected payment", compute="_compute_payment", default=0.0)
    act_payment = fields.Float(string="Actual payment", compute="_compute_payment", default=0.0)
    reception_ids = fields.One2many(
        comodel_name='reception.fish.detail',
        inverse_name='reception_id1',
        string='Details',
        required=True)

    reception_ids1 = fields.One2many(
        comodel_name='fishing.reception.detail',
        inverse_name='reception_id',
        string='Details',
        required=True)

    @api.model
    def create(self, vals):
        if vals.get('ref', _('New')) == _('New'):
            vals['ref'] = self.env['ir.sequence'].next_by_code('fish.reception') or _('New')

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(vals.get('ref'))
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_image = base64.b64encode(temp.getvalue())
        vals['qr_code'] = qr_image

        result = super(Da, self).create(vals)
        self.env.user.notify_success(message="danger")
        details = self.env["fishing.reception.detail"].search([('reception_id', '=', result.id)])
        for line in details:
            line.update({'type': result.type})
            line.update({'treatment_ordered': result.treatment_ordered if result.type == 'service' else True})
            line.update({'will_be_tunneled': result.tunnel_ordered if result.type == 'service' else True})
            line.update({'ordered_temp': result.ordered_temp})
            line.update({'packaging_ordered': result.packaging_ordered if result.type == 'service' else True})

        if vals.get('type') == 'production':
            vals1 = {
                'origin': result.ref,
                'date_order': datetime.today(),
                'partner_id': result.mareyeur.id,
                'partner_ref': result.ref,
                'state': 'purchase',
                'invoice_status': 'to invoice',
            }
            res = self.env['purchase.order'].create(vals1)
            if res:
                # product = self.env['product.product'].search([('name', '=', 'Fish')])
                product = self.env.ref('fishing.product_product_2_product_template')

                qte = 0
                for rec in result.reception_ids:
                    qte += (rec.qte1 + rec.scum_qty1)
                vals2 = {
                    'name': result.ref,
                    'product_qty': qte,
                    'product_id': product.id,
                    'product_uom': product.uom_id.id,
                    'price_unit': product.standard_price,
                    'price_subtotal': product.standard_price,
                    'price_total': product.standard_price,
                    'price_tax': 0,
                    'order_id': res.id,
                    'partner_id': self.mareyeur,
                    'qty_received': qte,
                    'qty_received_manual': qte
                }
                res2 = self.env['purchase.order.line'].create(vals2)
        if vals.get('type') == 'service':
            inv_vals = {
                'reception_id': result.id,
                'partner_id': result.customer_id.id,
                'payment_reference': result.ref,
                'invoice_date': datetime.today(),
                'move_type': 'out_invoice',
                'state': 'draft',
            }
            inv = self.env['account.move'].create(inv_vals)
            context = {'check_move_validity': False}
            for line in details:
                if result.treatment_ordered:
                    tr_ser = self.env.ref('fishing.product_service_treatment')
                    tr_line_vals = {
                        'product_id': tr_ser.id,
                        'account_id': tr_ser.property_account_expense_id.id if tr_ser.property_account_expense_id else self.env.ref(
                            'fishing.pcg_700000').id,
                        'quantity': line.qte,
                        'name': line.article.display_name,
                        'move_id': inv.id,
                        'price_unit': tr_ser.list_price,
                        'price_subtotal': tr_ser.list_price * line.qte,
                        'price_total': tr_ser.list_price * line.qte,
                    }
                    self.with_context(context).env['account.move.line'].create(tr_line_vals)
                if result.tunnel_ordered:
                    # if not result.treatment_ordered:
                    # line.write({'status': '2'})
                    tn_serv = self.env.ref('fishing.product_service_tunnel')
                    tn_line_vals = {
                        'product_id': tn_serv.id,
                        'account_id': tn_serv.property_account_expense_id.id if tn_serv.property_account_expense_id else self.env.ref(
                            'fishing.pcg_700000').id,
                        'quantity': line.qte,
                        'name': line.article.display_name,
                        'move_id': inv.id,
                        'price_unit': tn_serv.list_price,
                        'price_subtotal': tn_serv.list_price * line.qte,
                        'price_total': tn_serv.list_price * line.qte,
                    }
                    self.with_context(context).env['account.move.line'].create(tn_line_vals)
                if result.packaging_ordered:
                    # if not result.treatment_ordered and not result.tunnel_ordered:
                    # line.write({'status': '4'})
                    pk_serv = self.env.ref('fishing.product_service_packaging')
                    pk_line_vals = {
                        'product_id': pk_serv.id,
                        'account_id': pk_serv.property_account_expense_id.id if pk_serv.property_account_expense_id else self.env.ref(
                            'fishing.pcg_700000').id,
                        'quantity': line.qte,
                        'name': line.article.display_name,
                        'move_id': inv.id,
                        'price_unit': pk_serv.list_price,
                        'price_subtotal': pk_serv.list_price * line.qte,
                        'price_total': pk_serv.list_price * line.qte,
                    }
                    self.with_context(context).env['account.move.line'].create(pk_line_vals)
        self.action_print_sheet(result.id)
        return result

    def action_print_sheet(self, rec_id):
        # result = self.env["fishing.reception"].browse(rec_id)
        return self.env.ref("fishing.reception_report").report_action(self, data={})

    @api.onchange("type", "treatment_ordered", "tunnel_ordered", "packaging_ordered", "ordered_temp")
    def _onchange_fields(self):
        if self.reception_ids:
            for line in self.reception_ids:
                line.type1 = self.type
                line.treatment_ordered1 = self.treatment_ordered
                line.tunnel_ordered1 = self.tunnel_ordered
                line.ordered_temp1 = self.ordered_temp
                line.packaging_ordered1 = self.packaging_ordered

    def _compute_payment(self):
        for recep in self:
            if recep.type == 'service':
                total_exp = 0
                total_act = 0
                for line in recep.reception_ids1:
                    if recep.treatment_ordered:
                        total_exp = total_exp + (
                                line.qte * self.env.ref('fishing.product_service_treatment').list_price)
                    if recep.tunnel_ordered:
                        total_exp = total_exp + (
                                line.qte * self.env.ref('fishing.product_service_tunnel').list_price)
                    if recep.packaging_ordered:
                        total_exp = total_exp + (
                                line.qte * self.env.ref('fishing.product_service_packaging').list_price)

                recep.exp_payment = total_exp

                invs = self.env["account.move"].search(
                    [
                        ("reception_id", "=", recep.id),
                        ("move_type", "=", "out_invoice"),
                        ("state", "in", ["posted"]),
                    ]
                )
                recep.act_payment = sum(invs.mapped("amount_total")) or 0.0


            else:
                recep.exp_payment = 0
                recep.act_payment = 0
