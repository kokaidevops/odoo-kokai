# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class ks_kokai_rab(models.Model):
    _name = 'kokai.rab'
    # _description = 'ks_indonusa.ks_indonusa'
    _description = 'Project RAB (Rencana Anggaran Biaya)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'date desc, id desc'

    # Basic Information
    purchase_request_ids = fields.One2many(
        'purchase.request',
        'rab_id',
        string='Purchase Requests'
    )
    purchase_request_count = fields.Integer(
        string='Purchase Request Count',
        compute='_compute_purchase_request_count'
    )
    
    @api.depends('purchase_request_ids')
    def _compute_purchase_request_count(self):
        for rab in self:
            rab.purchase_request_count = len(rab.purchase_request_ids)
    
    def action_view_purchase_requests(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "purchase_request.purchase_request_form_action"
        )
        if len(self.purchase_request_ids) > 1:
            action['domain'] = [('id', 'in', self.purchase_request_ids.ids)]
        elif self.purchase_request_ids:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.purchase_request_ids.id
        else:
            action['domain'] = [('id', '=', False)]
        return action
    
    def _check_and_create_purchase_request(self):
        """Create single purchase request for out of stock items after RAB approval"""
        self.ensure_one()
        
        # Get department from current user's employee
        department_id = False
        if self.env.user.employee_ids:
            employee = self.env.user.employee_ids[0]
            department_id = employee.department_id.id if employee.department_id else False
        
        # Check if automatic PR creation is needed
        need_purchase = False
        purchase_lines = []
        
        for line in self.rab_line_ids:
            if line.stock_status in ['out_of_stock', 'partial'] and line.product_id:
                needed_qty = line.quantity - line.stock_available
                if needed_qty > 0:
                    need_purchase = True
                    purchase_lines.append({
                        'line': line,
                        'needed_qty': needed_qty
                    })
        
        if not need_purchase:
            return
        
        # Create single purchase request
        pr_vals = {
            'origin': self.name,
            'requested_by': self.env.user.id,
            'date_start': fields.Date.today(),
            'description': _('Auto-generated from RAB %s - %s') % (self.name, self.project or ''),
        }
        
        # Add department if available
        if department_id and 'department_id' in self.env['purchase.request']._fields:
            pr_vals['department_id'] = department_id
        
        # Add RAB reference if the field exists
        if 'rab_id' in self.env['purchase.request']._fields:
            pr_vals['rab_id'] = self.id
        
        purchase_request = self.env['purchase.request'].create(pr_vals)
        
        # Create lines for all items that need purchase
        for item in purchase_lines:
            line = item['line']
            line_vals = {
                'request_id': purchase_request.id,
                'product_id': line.product_id.id,
                'product_uom_id': line.unit_id.id or line.product_id.uom_id.id,
                'product_qty': item['needed_qty'],
                'date_required': fields.Date.today() + timedelta(days=line.lead_time or 7),
                'estimated_cost': line.cost_price * item['needed_qty'],
            }
            
            # Add specifications/description
            if line.description:
                line_vals['specifications'] = line.description
            
            # Add supplier info if available
            if line.supplier_id:
                line_vals['supplier_id'] = line.supplier_id.id
            
            # Add RAB line reference if the field exists
            if 'rab_line_id' in self.env['purchase.request.line']._fields:
                line_vals['rab_line_id'] = line.id
            
            self.env['purchase.request.line'].create(line_vals)
            
            # Update RAB line reason
            line.write({'reason': 'pr_draft'})
        
        # Post message on RAB
        message = _('Purchase Request %s has been created') % purchase_request.name
        self.message_post(body=message, subtype_xmlid='mail.mt_note')
        
        # Post message on PR
        purchase_request.message_post(
            body=_('Created from RAB: %s') % self.name,
            subtype_xmlid='mail.mt_note'
        )

    def action_create_purchase_request(self):
        """Create single purchase request from RAB lines"""
        print('----masuk')
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('Only approved RAB can create purchase request.'))
        
        # Get department from current user's employee
        department_id = False
        if self.env.user.employee_ids:
            employee = self.env.user.employee_ids[0]
            department_id = employee.department_id.id if employee.department_id else False
        
        # Collect all lines that need purchase
        lines_to_purchase = []
        for line in self.rab_line_ids:
            if line.stock_status in ['out_of_stock', 'partial'] and line.product_id:
                needed_qty = line.quantity - line.stock_available
                if needed_qty > 0:
                    lines_to_purchase.append((line, needed_qty))
        
        if not lines_to_purchase:
            raise UserError(_('No items need to be purchased.'))
        
        # Create single purchase request
        pr_vals = {
            'origin': self.name,
            'requested_by': self.env.user.id,
            'description': _('Purchase Request from RAB %s for project %s') % (self.name, self.project),
        }
        
        # Add department if available
        if department_id and 'department_id' in self.env['purchase.request']._fields:
            pr_vals['department_id'] = department_id
        
        # Add RAB reference
        if 'rab_id' in self.env['purchase.request']._fields:
            pr_vals['rab_id'] = self.id
        
        purchase_request = self.env['purchase.request'].create(pr_vals)
        
        # Create lines
        for line, needed_qty in lines_to_purchase:
            pr_line_vals = {
                'request_id': purchase_request.id,
                'product_id': line.product_id.id,
                'product_uom_id': line.unit_id.id or line.product_id.uom_id.id,
                'product_qty': needed_qty,
                'estimated_cost': line.cost_price * needed_qty,
                'date_required': fields.Date.today() + timedelta(days=line.lead_time or 7),
                'specifications': line.description,
            }
            
            # Add supplier if available (for reference only)
            if line.supplier_id:
                pr_line_vals['supplier_id'] = line.supplier_id.id
            
            # Add RAB line reference
            if 'rab_line_id' in self.env['purchase.request.line']._fields:
                pr_line_vals['rab_line_id'] = line.id
            
            self.env['purchase.request.line'].create(pr_line_vals)
            
            # Update RAB line status
            line.write({'reason': 'pr_draft'})
        
        # Post messages
        self.message_post(
            body=_('Purchase Request %s has been created') % purchase_request.name,
            subtype_xmlid='mail.mt_note'
        )
        
        # Show created purchase request
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.request',
            'res_id': purchase_request.id,
            'view_mode': 'form',
            'target': 'current',
        }

    name = fields.Char(
        string='RAB Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    # project_id = fields.Many2one(
    #     'project.project',
    #     string='Project',
    #     required=True,
    #     tracking=True
    # )
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
        domain=[('is_company', '=', True)]
    )
    
    # From Sale Order Model (sale_order.py)
    user_id = fields.Many2one(
        comodel_name='res.users',
        string="Salesperson",
        # compute='_compute_user_id',
        store=True, readonly=False, precompute=True, index=True,
        tracking=2,
        # domain=lambda self: "[('groups_id', '=', {}), ('share', '=', False), ('company_ids', '=', company_id)]".format(
        #     self.env.ref("sales_team.group_sale_salesman").id
        # )
        )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        # required=True, 
        change_default=True, index=True,
        tracking=1,
        check_company=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        # required=True, index=True,
        default=lambda self: self.env.company,
        index=True,
    )
    so_number = fields.Char(
        string="Sales Order Number",
        readonly=True,
    )

    # Tambahkan field line_count
    line_count = fields.Integer(
        string='Line Count',
        compute='_compute_line_count',
        store=True
    )
    
    @api.depends('rab_line_ids')
    def _compute_line_count(self):
        for rab in self:
            rab.line_count = len(rab.rab_line_ids)

    total_cost_price = fields.Monetary(
        string='Total Cost Price',
        compute='_compute_total_cost_and_qty',
        store=True,
        currency_field='currency_id'
    )
    total_quantity = fields.Float(
        string='Total Quantity',
        compute='_compute_total_cost_and_qty',
        store=True
    )
    total_cost_percentage = fields.Float(
        string='Cost %',
        compute='_compute_total_cost_percentage',
        store=True
    )
    
    @api.depends('purchase_request_ids')
    def _compute_purchase_request_count(self):
        for rab in self:
            rab.purchase_request_count = len(rab.purchase_request_ids)
    
    @api.depends('rab_line_ids')
    def _compute_line_count(self):
        for rab in self:
            rab.line_count = len(rab.rab_line_ids)
    
    @api.depends('rab_line_ids.cost_price', 'rab_line_ids.quantity')
    def _compute_total_cost_and_qty(self):
        for rab in self:
            total_cost = 0.0
            total_qty = 0.0
            
            for line in rab.rab_line_ids:
                total_cost += line.cost_price * line.quantity
                total_qty += line.quantity
            
            rab.total_cost_price = total_cost
            rab.total_quantity = total_qty
    
    @api.depends('total_cost_price', 'subtotal_amount')
    def _compute_total_cost_percentage(self):
        for rab in self:
            if rab.subtotal_amount > 0:
                rab.total_cost_percentage = (rab.total_cost_price / rab.subtotal_amount) * 100
            else:
                rab.total_cost_percentage = 0.0

    # team_id = fields.Many2one(
    #     comodel_name='crm.team',
    #     string="Sales Team",
    #     compute='_compute_team_id',
    #     store=True, readonly=False, precompute=True, ondelete="set null",
    #     change_default=True, check_company=True,  # Unrequired company
    #     tracking=True,
    #     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    # require_signature = fields.Boolean(
    #     string="Online signature",
    #     compute='_compute_require_signature',
    #     store=True, readonly=False, precompute=True,
    #     help="Request a online signature from the customer to confirm the order.")
    # prepayment_percent = fields.Float(
    #     string="Prepayment percentage",
    #     compute='_compute_prepayment_percent',
    #     store=True, readonly=False, precompute=True,
    #     help="The percentage of the amount needed that must be paid by the customer to confirm the order.")
    # reference = fields.Char(
    #     string="Payment Ref.",
    #     help="The payment communication of this sale order.",
    #     copy=False)
    # client_order_ref = fields.Char(string="Customer Reference", copy=False)
    # Followup ?
    # tag_ids = fields.Many2many(
    #     comodel_name='crm.tag',
    #     relation='sale_order_tag_rel', column1='order_id', column2='tag_id',
    #     string="Tags")
    # require_payment = fields.Boolean(
    #     string="Online payment",
    #     compute='_compute_require_payment',
    #     store=True, readonly=False, precompute=True,
    #     help="Request a online payment from the customer to confirm the order.")
    
    # Dates
    date = fields.Date(
        string='RAB Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    # Quotation Lines Product
    product_id = fields.Many2one(
        'product.template',
        string='Finished Goods',
        # required=True,
        domain=[('purchase_ok', '=', True)],
        ondelete='cascade',
        index=True,
        tracking=True,
        store=True
    )
    
    # Quotation Lines UoM
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='UoM',
        # required=True,
        domain="[('category_id', '=', product_uom_category_id)]",
        help='UoM untuk produk ini. Hanya UoM dengan kategori yang sama yang dapat digunakan.'
    )

    # Quotation Lines Unit Price
    unit_price = fields.Float(
        string='Unit Price',
        # required=True
    )

    valid_until = fields.Date(
        string='Valid Until',
        required=True,
        default=lambda self: fields.Date.today() + timedelta(days=30),
        tracking=True
    )
    
    project = fields.Char(
        string="Project"
    )
    
    finished_goods = fields.Many2one(
        'product.template',
        string='Finished Goods'
    )
    
    quantity = fields.Integer(
        string="Quantity"
    )
    
    product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string="UoM",
        compute='_compute_product_uom',
        store=True, readonly=False, precompute=True, ondelete='restrict',
        # domain="[('category_id', '=', product_uom_category_id)]"
    )
    
    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('revised', 'Revised'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired')
    ], string='Status RAB', default='draft', tracking=True, copy=False)
    
    # Lines
    rab_line_ids = fields.One2many(
        'kokai.rab.line',
        'rab_id',
        string='RAB Lines',
        copy=True
    )
    


    # Financial
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    subtotal_amount = fields.Monetary(
        string='Subtotal',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    margin_percentage = fields.Float(
        string='Margin %',
        default=20.0,
        tracking=True
    )
    margin_amount = fields.Monetary(
        string='Margin Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    tax_amount = fields.Monetary(
        string='Tax Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    total_amount = fields.Monetary(
        string='Total Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
        tracking=True
    )
    tax_id = fields.Char(
    #     'account.tax',
        string='Taxes',
    #     related='product_id.taxes_id',
        store=True,
        readonly=False,
    #     domain="[('type_tax_use', '=', 'sale')]"  # atau 'purchase'
    )
    price_subtotal = fields.Monetary(
        string='Amount',
        # compute='_compute_totals',
        store=True,
        # currency_field='currency_id',
    )
    discount_nominal = fields.Monetary(
        string='Discount Nominal',
        currency_field='currency_id',
        help='Diskon dalam bentuk nilai uang (bukan persen).'
    )
    
    # Additional Info
    notes = fields.Text(string='Notes')
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'rab_attachment_rel',
        'rab_id',
        'attachment_id',
        string='Attachments'
    )
    opportunity_id = fields.Many2one(
        'crm.lead',
        string='Opportunity',
        tracking=True,
        domain=[('type', '=', 'opportunity')]
    )
    opportunity_stage_id = fields.Many2one(
        related='opportunity_id.stage_id',
        string='Opportunity Stage',
        readonly=True,
        store=True
    )
    opportunity_probability = fields.Float(
        related='opportunity_id.probability',
        string='Probability',
        readonly=True
    )    
    # Stock Check
    # stock_check_ids = fields.One2many(
    #     'project.rab.stock.check',
    #     'rab_id',
    #     string='Stock Checks'
    # )
    # last_stock_check = fields.Datetime(
    #     string='Last Stock Check',
    #     compute='_compute_last_stock_check'
    # )
    stock_status = fields.Selection([
        ('all_available', 'All Available'),
        ('partial_available', 'Partial Available'),
        ('need_purchase', 'Need Purchase'),
        ('not_checked', 'Not Checked')
    ], string='Stock Status', compute='_compute_stock_status', store=True)
    
    # Tracking
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_date = fields.Datetime(string='Approved Date', readonly=True)
    

    # Tambahkan field baru untuk total cost dan quantity
    total_cost_price = fields.Monetary(
        string='Total Cost Price',
        compute='_compute_total_cost_and_qty',
        store=True,
        currency_field='currency_id',
        help='Total cost price of all items'
    )
    total_quantity = fields.Float(
        string='Total Quantity',
        compute='_compute_total_cost_and_qty',
        store=True,
        help='Total quantity of all items'
    )
    
    @api.depends('rab_line_ids.cost_price', 'rab_line_ids.quantity')
    def _compute_total_cost_and_qty(self):
        """Compute total cost price and quantity from all RAB lines"""
        for rab in self:
            total_cost = 0.0
            total_qty = 0.0
            
            for line in rab.rab_line_ids:
                # Calculate total cost (cost price * quantity)
                total_cost += line.cost_price * line.quantity
                # Sum up quantities
                total_qty += line.quantity
            
            rab.total_cost_price = total_cost
            rab.total_quantity = total_qty


    def action_view_rab_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'kokai.rab',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    @api.model
    def create(self, vals):
        """Override create to handle RAB creation from Sale Order"""
        # Auto-generate sequence if not provided
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('kokai.rab') or _('New')
        
        # If created from Sale Order, link opportunity
        if vals.get('so_number') and not vals.get('opportunity_id'):
            sale_order = self.env['sale.order'].search([('name', '=', vals['so_number'])], limit=1)
            if sale_order and sale_order.opportunity_id:
                vals['opportunity_id'] = sale_order.opportunity_id.id
                if not vals.get('project'):
                    vals['project'] = sale_order.opportunity_id.name
        
        # Create RAB
        rab = super(ks_kokai_rab, self).create(vals)
        
        # Post message if created from Sale Order
        if rab.so_number:
            sale_order = self.env['sale.order'].search([('name', '=', rab.so_number)], limit=1)
            if sale_order:
                sale_order.message_post(
                    body=_('RAB %s has been created') % rab.name,
                    subtype_xmlid='mail.mt_note'
                )
        
        return rab
    
    @api.depends('rab_line_ids.subtotal', 'margin_percentage')
    def _compute_amounts(self):
        """Compute financial amounts including margin and tax"""
        for rab in self:
            subtotal = sum(rab.rab_line_ids.mapped('subtotal'))
            rab.subtotal_amount = subtotal
            rab.margin_amount = subtotal * (rab.margin_percentage / 100)
            # Assuming 11% PPN (VAT)
            rab.tax_amount = (subtotal + rab.margin_amount) * 0.11
            rab.total_amount = subtotal + rab.margin_amount + rab.tax_amount




    def action_add_line(self):
        self.ensure_one()
        self.write({
            'rab_line_ids': [(0, 0, {
                'product_id': False,
                'quantity': 1.0,
                'unit_price': 0.0,
            })]
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'kokai.rab',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.onchange('finished_goods')
    def onchange_finished_good(self):
        
        
        print('ceheckkkk')



    @api.onchange('opportunity_id')
    def _onchange_opportunity_id(self):
        if self.opportunity_id:
            if self.opportunity_id.partner_id:
                self.customer_id = self.opportunity_id.partner_id
            # Set project name from opportunity
            # if not self.project_id:
            #     self.project_name = self.opportunity_id.name
    
    def action_approve(self):
        """Override to update opportunity when RAB approved"""
        res = super(ks_kokai_rab, self).action_approve()
        
        # Update opportunity expected revenue
        if self.opportunity_id:
            self.opportunity_id._compute_rab_amount()
            
            # Send notification to opportunity
            self.opportunity_id.message_post(
                body=_('RAB %s has been approved with total amount %s') % (
                    self.name,
                    self.total_amount
                ),
                subtype_xmlid='mail.mt_note'
            )
        
        return res

    # @api.model
    # def create(self, vals):
    #     return super(ProjectRAB, self).create(vals)
    
    @api.depends('rab_line_ids.subtotal', 'margin_percentage')
    def _compute_amounts(self):
        pass
        for rab in self:
            subtotal = sum(rab.rab_line_ids.mapped('subtotal'))
            rab.subtotal_amount = subtotal
            rab.margin_amount = subtotal * (rab.margin_percentage / 100)
            # Assuming 11% PPN
            rab.tax_amount = (subtotal + rab.margin_amount) * 0.11
            rab.total_amount = subtotal + rab.margin_amount + rab.tax_amount
    
    # @api.depends('stock_check_ids')
    # def _compute_last_stock_check(self):
    #     for rab in self:
    #         if rab.stock_check_ids:
    #             rab.last_stock_check = max(rab.stock_check_ids.mapped('check_date'))
    #         else:
    #             rab.last_stock_check = False
    
    @api.depends('rab_line_ids.stock_status')
    def _compute_stock_status(self):
        for rab in self:
            if not rab.rab_line_ids:
                rab.stock_status = 'not_checked'
            else:
                statuses = rab.rab_line_ids.mapped('stock_status')
                if 'out_of_stock' in statuses:
                    rab.stock_status = 'need_purchase'
                elif 'partial' in statuses:
                    rab.stock_status = 'partial_available'
                elif all(s == 'available' for s in statuses if s):
                    rab.stock_status = 'all_available'
                else:
                    rab.stock_status = 'not_checked'
    
    def action_submit(self):
        self.ensure_one()
        if not self.rab_line_ids:
            raise UserError(_('Please add at least one RAB line.'))
        self.state = 'submitted'
    
    def action_approve(self):
        self.ensure_one()
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id,
            'approved_date': fields.Datetime.now()
        })
        # Check if need to create purchase request
        # self._check_and_create_purchase_request()
    
    def action_reject(self):
        self.ensure_one()
        self.state = 'rejected'
    
    def action_set_to_draft(self):
        self.ensure_one()
        self.state = 'draft'
    
    def action_revise(self):
        self.ensure_one()
        self.state = 'revised'
        
    # def action_calculate(self):
    #     """Calculate and update stock status for all RAB lines across all locations"""
    #     self.ensure_one()
        
    #     # Force recompute stock info for all lines
    #     for line in self.rab_line_ids:
    #         line._compute_stock_info_all_locations()
            
    #     # Recompute RAB stock status
    #     self._compute_stock_status()
        
    #     # Show notification
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': _('Stock Calculation Complete'),
    #             'message': _('Stock availability has been updated for all products across all locations.'),
    #             'type': 'success',
    #             'sticky': False,
    #         }
    #     }    

    def action_view_rab_lines(self):
        """Show RAB lines in a popup"""
        self.ensure_one()
        return {
            'name': _('RAB Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'kokai.rab.line',
            'view_mode': 'tree,form',
            'domain': [('rab_id', '=', self.id)],
            'context': {
                'default_rab_id': self.id,
            },
            'target': 'current',
        }

    def action_calculate(self):
        """Calculate stock, costs, and totals"""
        self.ensure_one()
        
        # Force recompute stock info for all lines
        for line in self.rab_line_ids:
            line._compute_stock_info_all_locations()
            # Also recompute cost info to get latest prices
            line._compute_cost_info()
            # Recompute subtotal
            line._compute_subtotal()
            # Recompute margin
            line._compute_margin()
        
        # Recompute all totals
        self._compute_amounts()  # This will recalculate subtotal_amount, tax_amount, total_amount
        self._compute_total_cost_and_qty()  # This will calculate total_cost_price and total_quantity
        self._compute_stock_status()
        
        # Show notification with summary
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Calculation Complete'),
                'message': _(
                    'Calculation Summary:\n'
                    'Total Items: %d\n'
                    'Total Quantity: %.2f\n'
                    'Total Cost: %s %.2f\n'
                    'Total Amount: %s %.2f'
                ) % (
                    len(self.rab_line_ids),
                    self.total_quantity,
                    self.currency_id.symbol,
                    self.total_cost_price,
                    self.currency_id.symbol,
                    self.total_amount
                ),
                'type': 'success',
                'sticky': True,
            }
        }



        def action_show_wizard_generate_product(self):
            return {
                'name': 'Create Product',
                'type': 'ir.actions.act_window',
                'res_model': 'product.template.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_name': self.name or '',
                    'default_source_id': self.id,
                    'default_source_model': self._name,
                    # Tambahkan default values lain sesuai kebutuhan
                }
            }    
    # def action_check_stock(self):
    #     """Check stock availability for all lines"""
    #     self.ensure_one()
    #     # Create stock check record
    #     check_vals = {
    #         'rab_id': self.id,
    #         'check_date': fields.Datetime.now(),
    #     }
    #     stock_check = self.env['project.rab.stock.check'].create(check_vals)
        
    #     # Check each line
    #     for line in self.rab_line_ids:
    #         line._compute_stock_info()
        
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': _('Stock Check Complete'),
    #             'message': _('Stock availability has been updated.'),
    #             'type': 'success',
    #             'sticky': False,
    #         }
    #     }
    
    # def _check_and_create_purchase_request(self):
    #     """Create purchase request for out of stock items"""
    #     purchase_lines = []
    #     for line in self.rab_line_ids:
    #         if line.stock_status in ['out_of_stock', 'partial'] and line.product_id:
    #             needed_qty = line.quantity - line.stock_available
    #             if needed_qty > 0:
    #                 purchase_lines.append({
    #                     'product_id': line.product_id.id,
    #                     'quantity': needed_qty,
    #                     'price_unit': line.cost_price,
    #                     'partner_id': line.supplier_id.id if line.supplier_id else False,
    #                 })
        
    #     if purchase_lines:
    #         # Create purchase request (implement based on your purchase workflow)
    #         pass
    
    @api.model
    def _check_expired_rab(self):
        """Cron job to check expired RAB"""
        expired_rabs = self.search([
            ('state', 'in', ['draft', 'submitted']),
            ('valid_until', '<', fields.Date.today())
        ])
        expired_rabs.write({'state': 'expired'})



    @api.depends('partner_id')
    def _compute_user_id(self):
        for order in self:
            if order.partner_id and not (order._origin.id and order.user_id):
                # Recompute the salesman on partner change
                #   * if partner is set (is required anyway, so it will be set sooner or later)
                #   * if the order is not saved or has no salesman already
                order.user_id = (
                    order.partner_id.user_id
                    or order.partner_id.commercial_partner_id.user_id
                    or (self.env.user.has_group('sales_team.group_sale_salesman') and self.env.user)
                )
                
    @api.depends('partner_id', 'user_id')
    def _compute_team_id(self):
        cached_teams = {}
        for order in self:
            default_team_id = self.env.context.get('default_team_id', False) or order.team_id.id
            user_id = order.user_id.id
            company_id = order.company_id.id
            key = (default_team_id, user_id, company_id)
            if key not in cached_teams:
                cached_teams[key] = self.env['crm.team'].with_context(
                    default_team_id=default_team_id,
                )._get_default_team_id(
                    user_id=user_id,
                    domain=self.env['crm.team']._check_company_domain(company_id),
                )
            order.team_id = cached_teams[key]
            
    @api.depends('company_id')
    def _compute_require_signature(self):
        for order in self:
            order.require_signature = order.company_id.portal_confirmation_sign
            
    @api.depends('require_payment')
    def _compute_prepayment_percent(self):
        for order in self:
            order.prepayment_percent = order.company_id.prepayment_percent
            
    @api.depends('company_id')
    def _compute_require_payment(self):
        for order in self:
            order.require_payment = order.company_id.portal_confirmation_pay
    
    @api.depends('finished_goods')
    def _compute_product_uom(self):
        for rec in self:
            rec.product_uom = rec.finished_goods.uom_id
            




    # def action_show_wizard_generate_product(self):
    #     self.ensure_one()
    #     ctx = dict(self.env.context)
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'generate.product.wizard',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'view_id': self.env.ref('ks_kokai.generate_product_wizard_view_form').id,
    #         'context': ctx,
    #     }        
        # return {
        #     'name': 'Generate Product Template',
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'generate.product.wizard',
        #     'views': [(False, 'form')],
        #     'target': 'new',
        #     'context': dict(active_ids=self.ids),
        # }