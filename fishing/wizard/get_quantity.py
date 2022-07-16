from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
import math


class GetQuantity(models.TransientModel):
    _name = 'fishing.reception.getqty'

    quantity = fields.Float(string="Quantity", default=lambda self: self._context['qte'])

    remaining_quantity = fields.Float(string="Quantity", default=lambda self: self._context['remaining_quantity'])

    internal_packaging = fields.Boolean(string="Internal packaging", default=True)

    product_id = fields.Many2one("product.template", string="Product",
                                 domain="[('categ_id', '=', default_categ_id),('type','=','product')]")

    default_categ_id = fields.Many2one("product.category", string="Product Category")

    treatment_team_id = fields.Many2one(comodel_name='res.users', string='Treatment Team', domain="[('id','=','0')]")

    treatment_responsible_id = fields.Many2one(comodel_name='res.users', string='Treatment Responsible',
                                               default=lambda self: self.env.user.id)

    tunnel_id = fields.Many2one(comodel_name='fishing.tunnel', string='Tunnel')

    tunnel_capacity = fields.Float(string='Tunnel Capacity')

    ordered_temp = fields.Float(string='Temperature', required=False,
                                default=lambda self: self._context['ordered_temp'])

    tunnel_responsible_id = fields.Many2one(comodel_name='res.users', string='Freezing Responsible',
                                            default=lambda self: self.env.user.id)

    tunnel_team_id = fields.Many2one(comodel_name='res.users', string='Freezing Team', domain="[('id','=','0')]")

    new_status = fields.Char()

    product_ids = fields.One2many(
        comodel_name='fishing.session.product',
        inverse_name='session_id',
        string='Products',
        required=True)

    def truncate(self, number, decimals=0):
        """
        Returns a value truncated to a specific number of decimal places.
        """
        if decimals == 0:
            return math.trunc(number)
        if (number).is_integer():
            return int(number)

        factor = 10.0 ** decimals
        return math.trunc(number * factor) / factor

    @api.onchange("tunnel_id")
    def _onchange_tunnel_id(self):
        if self.tunnel_id:
            if self.tunnel_id.capacity < self.quantity:
                raise ValidationError(_("Selected Tunnel doesn't have enough capacity for this quantity"))
            else:
                self.update({'tunnel_capacity': self.tunnel_id.free_capacity})

    @api.onchange("quantity")
    def _onchange_quantity(self):
        if self.tunnel_id:
            if self.tunnel_id.capacity < self.quantity:
                self.update({'quantity': self.tunnel_id.free_capacity})
                raise ValidationError(_("Selected Tunnel doesn't have enough capacity for this quantity"))

    def start_treatment(self):

        act_id = self._context.get('active_id')
        act_model = self._context.get('active_model')
        fish_detail_obj = self.env['fishing.reception.detail']
        value = self.env[act_model]
        quantity_data = value.browse(act_id)

        # Treatment Code
        if self.quantity > quantity_data.qte:
            raise ValidationError(_("Can not enter quantity more than existing quantity!"))
        else:
            if quantity_data.qte == self.quantity:
                quantity_data.write({
                    'startdate': datetime.now(),
                    'status': '1',
                    'treatment_responsible_id': self.treatment_responsible_id,
                    'treatment_team_id': self.treatment_team_id
                })
            else:
                fish_detail_obj.create({'article': quantity_data.article.id,
                                        'reception_id': quantity_data.reception_id.id,
                                        'quality': quantity_data.quality.id,
                                        'qte': self.quantity,
                                        'customer_id': quantity_data.customer_id.id,
                                        'mareyeur': quantity_data.mareyeur.id,
                                        'status': '1',
                                        'treatment_ordered': quantity_data.treatment_ordered,
                                        'will_be_tunneled': quantity_data.will_be_tunneled,
                                        'packaging_ordered': quantity_data.packaging_ordered,
                                        'startdate': datetime.now()})
                quantity_data.write({'qte': quantity_data.qte - self.quantity})

    def start_tunnel(self):

        act_id = self._context.get('active_id')
        act_model = self._context.get('active_model')

        fish_detail_obj = self.env['fishing.reception.detail']
        value = self.env[act_model]

        quantity_data = value.browse(act_id)

        # Tunnels Code
        if self.tunnel_id:
            if self.tunnel_id.free_capacity < self.quantity:
                raise ValidationError(_("Selected Tunnel doesn't have enough capacity for this quantity"))

        if quantity_data.qte == self.quantity:
            quantity_data.write({'tunnel_start_date': datetime.now(), 'status': '3', 'tunnel_id': self.tunnel_id})
        elif self.quantity > quantity_data.qte:
            raise ValidationError(_("Can not enter quantity more than existing quantity!"))
        else:
            quantity_data.qte = quantity_data.qte - self.quantity
            fish_detail_obj.create({'article': quantity_data.article.id,
                                    'reception_id': quantity_data.reception_id.id,
                                    'quality': quantity_data.quality.id,
                                    'qte': self.quantity,
                                    'status': '3',
                                    'startdate': quantity_data.startdate,
                                    'tunnel_id': self.tunnel_id.id,
                                    'end_date': quantity_data.end_date,
                                    'treatment_ordered': quantity_data.treatment_ordered,
                                    'will_be_tunneled': quantity_data.will_be_tunneled,
                                    'packaging_ordered': quantity_data.packaging_ordered,
                                    'tunnel_start_date': datetime.now()})

    def read_from_balance(self):
        pass

    def add_product(self):
        act_id = self._context.get('active_id')
        act_model = self._context.get('active_model')
        value = self.env[act_model]
        quantity_data = value.browse(act_id)

        if self.quantity > self.remaining_quantity:
            raise ValidationError(
                _("Can not enter quantity more than existing quantity! available quantity is : " + str(
                    self.remaining_quantity) + " you entered : " + str(self.quantity)))

        new_prod = {
            'session_id': self.id,
            'product_id': self.product_id.id,
            'qte': self.quantity
        }
        self.env["fishing.session.product"].create(new_prod)
        self.update({"remaining_quantity": self.remaining_quantity - self.quantity})
        quantity_data.update({'qte': self.remaining_quantity, 'process_qty': quantity_data.process_qty + self.quantity})
        return {
            'name': _('Product creation'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': self._name,
            'domain': [],
            'context': dict(self._context, active_ids=self.ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }

    def cancel_products(self):
        act_id = self._context.get('active_id')
        act_model = self._context.get('active_model')
        value = self.env[act_model]
        quantity_data = value.browse(act_id)
        for p in self.product_ids:
            quantity_data.update({'qte': quantity_data.qte + p.qte})

            if self.internal_packaging and quantity_data.used_boxes > 0:
                quantity_data.update({'used_boxes': quantity_data.used_boxes - 1})

    def save_products(self):
        act_id = self._context.get('active_id')
        act_model = self._context.get('active_model')
        value = self.env[act_model]
        quantity_data = value.browse(act_id)
        stock_location = self.env['stock.location'].search([('name', 'ilike', 'Temporary')])
        quantity_attr_id = self.env['product.attribute'].search([('name', '=', 'Quantity')]).id
        get_inventory = self.env['stock.quant']
        packaging_pr1 = self.env.ref(
            'fishing.product_product_carton') if (
                quantity_data.will_be_tunneled and quantity_data.tunnel_end_date) else self.env.ref(
            'fishing.product_product_poly')
        if self.internal_packaging and packaging_pr1.qty_available < len(self.product_ids):
            raise ValidationError(
                _("Insufficient packaging boxes in stock\nStock of " + packaging_pr1.name + " is : " + str(
                    packaging_pr1.qty_available)))

        for p in self.product_ids:
            if quantity_data.type == 'service':
                if self.internal_packaging:
                    context = {'check_move_validity': False}
                    serv_inv = self.env["account.move"].search([('reception_id', '=', quantity_data.reception_id.id)])

                    if serv_inv:
                        line = self.with_context(context).env["account.move.line"].search(
                            [('move_id', '=', serv_inv[0].id), ('product_id', '=', packaging_pr1.id)])
                        if line:
                            line[0].write({'quantity': line[0].quantity + 1})
                        else:
                            pk_line_vals = {
                                'product_id': packaging_pr1.id,
                                'account_id': packaging_pr1.property_account_expense_id.id if packaging_pr1.property_account_expense_id else self.env.ref(
                                    'fishing.pcg_700000').id,
                                'quantity': 1,
                                'move_id': serv_inv[0].id,
                                'price_unit': packaging_pr1.list_price,
                                'price_subtotal': packaging_pr1.list_price,
                                'price_total': packaging_pr1.list_price,
                            }
                            self.with_context(context).env['account.move.line'].create(pk_line_vals)
                    quantity_data.update({'used_boxes': quantity_data.used_boxes + 1})
                    get_lines = get_inventory.sudo().search(
                        [('product_id', '=', packaging_pr1.id)])
                    if get_lines:
                        line = get_lines[0]
                        line.update({'inventory_quantity': line.quantity - 1})
                        line.action_apply_inventory()

                    else:
                        line_create = get_inventory.sudo().create(
                            {'inventory_quantity': packaging_pr1.qty_available - 1,
                             'product_id': packaging_pr1.id
                             })
                        line_create.action_apply_inventory()

                service_stock_obj = self.env["fish.service.stock"]

                line = service_stock_obj.search(
                    [('customer_id', '=', quantity_data.customer_id.id),
                     ('category_id', '=', quantity_data.article.id)])
                if line:
                    line[0].write({'qte': line.qte + p.qte})
                else:
                    line_vals = {
                        'customer_id': quantity_data.customer_id.id,
                        'category_id': quantity_data.article.id,
                        'product_id': False,
                        'qte': quantity_data.qte,
                        'receive_date': datetime.now(),
                    }
                    line_create = line = service_stock_obj.create(line_vals)



            else:
                product_template = p.product_id

                packaging_name = "Pack " + product_template.name + " - " + str(self.truncate(p.qte, 2)) + "Kg"

                package_type = self.env['stock.package.type'].search([('name', '=', 'Caisse')])

                if not package_type:
                    package_type = self.env['stock.package.type'].create({
                        'name': "Caisse",
                    })

                packs = self.env["product.packaging"].search(
                    [("name", "=", packaging_name), ('product_id', '=', product_template.id)])
                if not packs:
                    self.env["product.packaging"].create(
                        {'name': packaging_name, 'product_id': product_template.id, 'qty': p.qte})

                new_package = self.env['stock.quant.package'].create({
                    'package_type_id': package_type.id,
                    'location_id': stock_location.id
                })

                self.env["stock.quant"].create({
                    'product_id': product_template.id,
                    'location_id': stock_location.id,
                    'package_id': new_package.id,
                    'quantity': p.qte
                })
                if self.internal_packaging:
                    quantity_data.update({'used_boxes': quantity_data.used_boxes + 1})
            """
            get_lines = get_inventory.sudo().search(
                [('location_id', '=', stock_location.id), ('product_id', '=', product_template.id)])
            if get_lines:
                line = get_lines[0]
                line.update({'inventory_quantity': line.quantity + p.qte})
                line.action_apply_inventory()
            else:
                line_create = get_inventory.sudo().create({'inventory_quantity': p.qte,
                                                           'product_id': product_template.id,
                                                           'location_id': stock_location.id})
                line_create.action_apply_inventory()

          
            attribute_record = self.env['product.attribute'].search([('id', '=', quantity_attr_id)])

            # check if the attr 'Quantity' has value = to product qnty
            val_exists = False
            for val in attribute_record.value_ids:
                if val.name == str(self.truncate(self.quantity, 2)) + 'Kg':
                    # val exists in attr values
                    val_exists = True
                    break
            # Create value for the attr Quantity
            if not val_exists:
                value = [(0, 0, {'name': str(self.truncate(self.quantity, 2)) + 'Kg'})]
                attribute_record.write({'value_ids': value})

            # check if the product template has variant attr 'Quantity'
            product_template_has_qty_att = False
            if product_template.attribute_line_ids:
                for attr in product_template.attribute_line_ids:
                    if attr.attribute_id.id == quantity_attr_id:
                        # Product already has Quantity attr
                        product_template_has_qty_att = True
                        # Now we'll Check if attribute value is available  for this product
                        val_exists_product = False
                        for attr_val in attr.value_ids:
                            if attr_val.name == str(self.truncate(self.quantity, 2)) + 'Kg':
                                # Now we know value exists in the attr values for this product
                                val_exists_product = True

                                break
                        if not val_exists_product:
                            for val in attribute_record.value_ids:
                                if val.name == str(self.truncate(self.quantity, 2)) + 'Kg':
                                    attr.value_ids += val
                                    break

            if not product_template_has_qty_att:
                varient_value = ''
                for record in attribute_record.value_ids:
                    if record.name == str(self.truncate(self.quantity, 2)) + 'Kg':
                        varient_value = record

                create_attribut_line = [
                    (0, 0, {'attribute_id': quantity_attr_id, 'value_ids': varient_value})]
                product_template.write({'attribute_line_ids': create_attribut_line})

            product_with_attribute = self.env['product.product'].search(
                [('product_tmpl_id', '=', p.product_id.id)])

            for product in product_with_attribute:
                for attribute in product.product_template_attribute_value_ids:
                    if attribute.name == str(self.truncate(self.quantity, 2)) + 'Kg':
                        get_lines = get_inventory.sudo().search(
                            [('location_id', '=', stock_location.id), ('product_id', '=', product.id)])
                        if get_lines:
                            line = get_lines[0]
                            line.update({'inventory_quantity': line.quantity + p.qte})
                            line.action_apply_inventory()
                            break
                        else:
                            line_create = get_inventory.sudo().create({'inventory_quantity': p.qte,
                                                                       'product_id': product.id,
                                                                       'location_id': stock_location.id})
                            line_create.action_apply_inventory()

            """

        # updating record dates if not set
        if not quantity_data.paking_start_date:
            quantity_data.write({'status': '5', 'paking_start_date': datetime.now()})
        if quantity_data.qte == 0.0:
            quantity_data.write({'status': '6', "paking_end_date": datetime.now()})

        return True

    def save_products_to_packaging(self):
        act_id = self._context.get('active_id')
        act_model = self._context.get('active_model')
        value = self.env[act_model]
        quantity_data = value.browse(act_id)
        stock_location = self.env['stock.location'].search([('name', 'ilike', 'Temporary')])
        quantity_attr_id = self.env['product.attribute'].search([('name', '=', 'Quantity')]).id
        get_inventory = self.env['stock.quant']
        new_pallet = self.env['stock.pallet'].create({})
        packaging_pr1 = self.env.ref(
            'fishing.product_product_carton') if (
                quantity_data.will_be_tunneled and quantity_data.tunnel_end_date) else self.env.ref(
            'fishing.product_product_poly')
        if self.internal_packaging and packaging_pr1.qty_available < len(self.product_ids):
            raise ValidationError(
                _("Insufficient packaging boxes in stock\nStock of " + packaging_pr1.name + " is : " + str(
                    packaging_pr1.qty_available)))

        for p in self.product_ids:
            if quantity_data.type == 'service':
                service_stock_obj = self.env["fish.service.stock"]

                line = service_stock_obj.search(
                    [('customer_id', '=', quantity_data.customer_id.id),
                     ('category_id', '=', quantity_data.article.id)])
                if line:
                    line[0].write({'qte': line.qte + p.qte})
                else:
                    line_vals = {
                        'customer_id': quantity_data.customer_id.id,
                        'category_id': quantity_data.article.id,
                        'product_id': False,
                        'qte': quantity_data.qte,
                        'receive_date': datetime.now(),
                    }
                    line_create = line = service_stock_obj.create(line_vals)

                if self.internal_packaging:
                    context = {'check_move_validity': False}
                    serv_inv = self.env["account.move"].search([('reception_id', '=', quantity_data.reception_id.id)])

                    if serv_inv:
                        line = self.with_context(context).env["account.move.line"].search(
                            [('move_id', '=', serv_inv[0].id), ('product_id', '=', packaging_pr1.id)])
                        if line:
                            line[0].write({'quantity': line[0].quantity + 1})
                        else:
                            pk_line_vals = {
                                'product_id': packaging_pr1.id,
                                'account_id': packaging_pr1.property_account_expense_id.id if packaging_pr1.property_account_expense_id else self.env.ref(
                                    'fishing.pcg_700000').id,
                                'quantity': 1,
                                'move_id': serv_inv[0].id,
                                'price_unit': packaging_pr1.list_price,
                                'price_subtotal': packaging_pr1.list_price,
                                'price_total': packaging_pr1.list_price,
                            }
                            self.with_context(context).env['account.move.line'].create(pk_line_vals)
                    quantity_data.update({'used_boxes': quantity_data.used_boxes + 1})

                    line_create = get_inventory.sudo().create(
                        {'inventory_quantity': packaging_pr1.inventory_quantity - 1,
                         'product_id': packaging_pr1.id,
                         'location_id': stock_location.id})
                    line_create.action_apply_inventory()
            else:
                product_template = p.product_id

                packaging_name = "Pack " + product_template.name + str(self.truncate(p.qte, 2))
                package_type = self.env['stock.package.type'].search([('name', '=', 'Caisse')])

                if not package_type:
                    package_type = self.env['stock.package.type'].create({
                        'name': "Caisse",
                    })

                packs = self.env["product.packaging"].search(
                    [("name", "=", packaging_name), ('product_id', '=', product_template.id)])
                if not packs:
                    self.env["product.packaging"].create(
                        {'name': packaging_name, 'product_id': product_template.id, 'qty': p.qte})

                new_package = self.env['stock.quant.package'].create({
                    'package_type_id': package_type.id,
                    'location_id': stock_location.id,
                    'pallet_id': new_pallet.id
                })

                self.env["stock.quant"].create({
                    'product_id': product_template.id,
                    'location_id': stock_location.id,
                    'package_id': new_package.id,
                    'quantity': p.qte
                })
                if self.internal_packaging:
                    quantity_data.update({'used_boxes': quantity_data.used_boxes + 1})

        # updating record dates if not set
        if not quantity_data.paking_start_date:
            quantity_data.write({'status': '5', 'paking_start_date': datetime.now()})
        if quantity_data.qte == 0.0:
            quantity_data.write({'status': '6', "paking_end_date": datetime.now()})

        return True

    def _compute_remaining_quantity(self):
        """Calculate the total remaing quantity."""
        if self.product_ids:
            taken = 0
            for line in self.product_ids:
                taken += line.qte
            self.update({'remaining_quantity': self.remaining_quantity - taken})
        else:
            self.remaining_quantity = self.remaining_quantity


class ValidateTreatment(models.TransientModel):
    _name = 'fishing.reception.validateqty'

    treated_qty = fields.Float(string="Treated Quantity", default=lambda self: self._context['treated_qty'])
    treatment_scum_qty = fields.Float(string='Treatment Scum', required=False)
    treatment_films_qty = fields.Float(string='Used films', required=False)
    will_be_tunneled = fields.Boolean(default=lambda self: self._context['will_be_tunneled'], string="Frozen")
    ordered_temp = fields.Float(string='Temperature', required=False, default=0.0)

    def truncate(self, number, decimals=0):
        """
        Returns a value truncated to a specific number of decimal places.
        """
        if decimals == 0:
            return math.trunc(number)
        if (number).is_integer():
            return int(number)

        factor = 10.0 ** decimals
        return math.trunc(number * factor) / factor

    def approve_treatment(self):

        act_id = self._context.get('active_id')
        act_model = self._context.get('active_model')
        value = self.env[act_model]
        quantity_data = value.browse(act_id)
        packaging_pr1 = self.env.ref('fishing.product_product_films')
        get_inventory = self.env['stock.quant']

        if packaging_pr1.qty_available < self.treatment_films_qty:
            raise ValidationError(
                _("Insufficient treatment films in stock\nStock of " + packaging_pr1.name + " is : " + str(
                    packaging_pr1.qty_available)))

        # Treatment Code
        if self.treated_qty > quantity_data.qte:
            raise ValidationError(_("Can not enter quantity more than existing quantity!"))
        else:
            if quantity_data.qte == self.treated_qty:
                quantity_data.write({
                    'end_date': datetime.now(),
                    'status': '2',
                    'treatment_scum_qty': self.treatment_scum_qty,
                    'treatment_films_qty': self.treatment_films_qty,
                    'will_be_tunneled': self.will_be_tunneled,
                    'ordered_temp': self.ordered_temp
                })

                if quantity_data.type == 'service':
                    if self.treatment_films_qty > 0:
                        context = {'check_move_validity': False}
                        serv_inv = self.env["account.move"].search(
                            [('reception_id', '=', quantity_data.reception_id.id)])
                        if serv_inv:
                            line = self.with_context(context).env["account.move.line"].search(
                                [('move_id', '=', serv_inv[0].id), ('product_id', '=', packaging_pr1.id)])
                            if line:
                                line[0].write({'quantity': line[0].quantity + 1})
                            else:
                                pk_line_vals = {
                                    'product_id': packaging_pr1.id,
                                    'account_id': packaging_pr1.property_account_expense_id.id if packaging_pr1.property_account_expense_id else self.env.ref(
                                        'fishing.pcg_700000').id,
                                    'quantity': 1,
                                    'move_id': serv_inv[0].id,
                                    'price_unit': packaging_pr1.list_price,
                                    'price_subtotal': packaging_pr1.list_price,
                                    'price_total': packaging_pr1.list_price,
                                }
                                self.with_context(context).env['account.move.line'].create(pk_line_vals)
                        get_lines = get_inventory.sudo().search(
                            [('product_id', '=', packaging_pr1.id)])
                        if get_lines:
                            line = get_lines[0]
                            line.update({'inventory_quantity': line.quantity - 1})
                            line.action_apply_inventory()
                        else:
                            line_create = get_inventory.sudo().create(
                                {'inventory_quantity': packaging_pr1.qty_available - 1,
                                 'product_id': packaging_pr1.id
                                 })
                            line_create.action_apply_inventory()

                    if not quantity_data.will_be_tunneled and not quantity_data.packaging_ordered:
                        service_stock_obj = self.env["fish.service.stock"]

                        line = service_stock_obj.search(
                            [('customer_id', '=', quantity_data.customer_id.id),
                             ('category_id', '=', quantity_data.article.id)])
                        if line:
                            line[0].write({'qte': line.qte + quantity_data.qte})
                        else:
                            line_vals = {
                                'customer_id': quantity_data.customer_id.id,
                                'category_id': quantity_data.article.id,
                                'product_id': False,
                                'qte': quantity_data.qte,
                                'receive_date': datetime.now(),
                            }
                            line_create = line = service_stock_obj.create(line_vals)

            else:
                fish_detail_obj = self.env['fishing.reception.detail']

                fish_detail_obj.create({'article': quantity_data.article.id,
                                        'reception_id': quantity_data.reception_id.id,
                                        'customer_id': quantity_data.customer_id.id,
                                        'mareyeur': quantity_data.mareyeur.id,
                                        'quality': quantity_data.quality.id,
                                        'treatment_ordered': quantity_data.treatment_ordered,
                                        'will_be_tunneled': quantity_data.will_be_tunneled,
                                        'packaging_ordered': quantity_data.packaging_ordered,
                                        'qte': quantity_data.qte - (self.treated_qty + self.treatment_scum_qty),
                                        'status': '0',
                                        'startdate': False})

                quantity_data.write({
                    'end_date': datetime.now(),
                    'status': '2',
                    'qte': self.treated_qty,
                    'treatment_scum_qty': self.treatment_scum_qty,
                    'treatment_films_qty': self.treatment_films_qty,
                    'will_be_tunneled': self.will_be_tunneled,
                    'ordered_temp': self.ordered_temp
                })

                if quantity_data.type == 'service':
                    if not quantity_data.will_be_tunneled and not quantity_data.packaging_ordered:
                        service_stock_obj = self.env["fish.service.stock"]
                        line = service_stock_obj.search(
                            [('customer_id', '=', quantity_data.customer_id.id),
                             ('category_id', '=', quantity_data.article.id)])
                        if line:
                            line[0].write({'qte': line.qte + quantity_data.qte})
                        else:
                            line_vals = {
                                'customer_id': quantity_data.customer_id.id,
                                'category_id': quantity_data.article.id,
                                'product_id': False,
                                'qte': self.treated_qty,
                                'receive_date': datetime.now(),
                            }
                            line_create = line = service_stock_obj.create(line_vals)


class Product(models.TransientModel):
    _name = 'fishing.session.product'
    product_id = fields.Many2one("product.template", string="Product", domain="[('type','=','product')]")
    qte = fields.Float(default=0.0)
    session_id = fields.Many2one(comodel_name="fishing.reception.getqty")
