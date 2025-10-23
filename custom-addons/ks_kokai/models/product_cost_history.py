# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class ProductCostHistory(models.Model):
    _name = 'product.cost.history'
    _description = 'Product Cost History'
    _order = 'date desc, id desc'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Basic Fields
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True
    )
    
    date = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now,
        index=True,
        tracking=True
    )
    
    cost_price = fields.Float(
        string='Cost Price',
        required=True,
        digits='Product Price',
        tracking=True,
        help='Cost price at the time of purchase'
    )
    
    vendor_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        domain=[('supplier_rank', '>', 0)],
        tracking=True,
        help='Vendor from whom the product was purchased'
    )
    
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Purchase Order',
        ondelete='set null',
        tracking=True,
        help='Related purchase order'
    )
    
    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1.0,
        digits='Product Unit of Measure',
        tracking=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        tracking=True
    )
    
    # Computed Fields
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    total_cost = fields.Monetary(
        string='Total Cost',
        compute='_compute_total_cost',
        store=True,
        currency_field='currency_id'
    )
    
    cost_price_company_currency = fields.Monetary(
        string='Cost Price (Company Currency)',
        compute='_compute_cost_price_company_currency',
        store=True,
        currency_field='company_currency_id'
    )
    
    company_currency_id = fields.Many2one(
        'res.currency',
        string='Company Currency',
        related='company_id.currency_id',
        readonly=True
    )
    
    price_difference = fields.Float(
        string='Price Difference',
        compute='_compute_price_difference',
        store=True,
        help='Difference from previous cost'
    )
    
    price_difference_percent = fields.Float(
        string='Price Difference %',
        compute='_compute_price_difference',
        store=True,
        help='Percentage difference from previous cost'
    )
    
    # Related Fields
    product_name = fields.Char(
        related='product_id.name',
        string='Product Name',
        store=True,
        readonly=True
    )
    
    product_code = fields.Char(
        related='product_id.default_code',
        string='Product Code',
        store=True,
        readonly=True
    )
    
    vendor_name = fields.Char(
        related='vendor_id.name',
        string='Vendor Name',
        store=True,
        readonly=True
    )
    
    purchase_order_name = fields.Char(
        related='purchase_order_id.name',
        string='PO Number',
        store=True,
        readonly=True
    )
    
    # Additional Fields
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True
    )
    
    notes = fields.Text(
        string='Notes',
        tracking=True
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Analysis Fields
    is_lowest_price = fields.Boolean(
        string='Is Lowest Price',
        compute='_compute_price_analysis',
        help='Indicates if this is the lowest recorded price'
    )
    
    is_highest_price = fields.Boolean(
        string='Is Highest Price',
        compute='_compute_price_analysis',
        help='Indicates if this is the highest recorded price'
    )
    
    days_since_last_purchase = fields.Integer(
        string='Days Since Last Purchase',
        compute='_compute_days_since_last'
    )
    
    # Constraints
    _sql_constraints = [
        ('positive_cost_price', 'CHECK(cost_price >= 0)', 'Cost price must be positive!'),
        ('positive_quantity', 'CHECK(quantity > 0)', 'Quantity must be positive!'),
    ]
    
    @api.depends('product_id', 'vendor_id', 'date')
    def _compute_display_name(self):
        for record in self:
            date_str = fields.Datetime.to_string(record.date)[:10] if record.date else ''
            vendor_str = record.vendor_id.name if record.vendor_id else 'No Vendor'
            record.display_name = f"{record.product_id.name} - {vendor_str} - {date_str}"
    
    @api.depends('cost_price', 'quantity')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.cost_price * record.quantity
    
    @api.depends('cost_price', 'currency_id', 'date')
    def _compute_cost_price_company_currency(self):
        for record in self:
            if record.currency_id and record.currency_id != record.company_currency_id:
                record.cost_price_company_currency = record.currency_id._convert(
                    record.cost_price,
                    record.company_currency_id,
                    record.company_id,
                    record.date or fields.Date.today()
                )
            else:
                record.cost_price_company_currency = record.cost_price
    
    @api.depends('product_id', 'cost_price', 'date')
    def _compute_price_difference(self):
        for record in self:
            # Find previous cost entry
            previous = self.search([
                ('product_id', '=', record.product_id.id),
                ('date', '<', record.date),
                ('id', '!=', record.id)
            ], order='date desc', limit=1)
            
            if previous:
                record.price_difference = record.cost_price - previous.cost_price
                if previous.cost_price > 0:
                    record.price_difference_percent = (record.price_difference / previous.cost_price) * 100
                else:
                    record.price_difference_percent = 0
            else:
                record.price_difference = 0
                record.price_difference_percent = 0
    
    @api.depends('product_id', 'cost_price')
    def _compute_price_analysis(self):
        for record in self:
            if record.product_id:
                all_costs = self.search([
                    ('product_id', '=', record.product_id.id),
                    ('active', '=', True)
                ]).mapped('cost_price')
                
                if all_costs:
                    record.is_lowest_price = record.cost_price == min(all_costs)
                    record.is_highest_price = record.cost_price == max(all_costs)
                else:
                    record.is_lowest_price = False
                    record.is_highest_price = False
            else:
                record.is_lowest_price = False
                record.is_highest_price = False
    
    @api.depends('product_id', 'date')
    def _compute_days_since_last(self):
        for record in self:
            if record.product_id and record.date:
                last_purchase = self.search([
                    ('product_id', '=', record.product_id.id),
                    ('date', '<', record.date),
                    ('id', '!=', record.id)
                ], order='date desc', limit=1)
                
                if last_purchase:
                    delta = record.date - last_purchase.date
                    record.days_since_last_purchase = delta.days
                else:
                    record.days_since_last_purchase = 0
            else:
                record.days_since_last_purchase = 0
    
    @api.constrains('date')
    def _check_date(self):
        for record in self:
            if record.date and record.date > fields.Datetime.now():
                raise ValidationError(_('Cost history date cannot be in the future!'))
    
    @api.model
    def create(self, vals):
        """Override create to update product standard price if needed"""
        res = super(ProductCostHistory, self).create(vals)
        
        # Update product's standard price with latest cost
        if res.product_id and res.cost_price:
            latest_cost = self.search([
                ('product_id', '=', res.product_id.id),
                ('active', '=', True)
            ], order='date desc', limit=1)
            
            if latest_cost and latest_cost.id == res.id:
                res.product_id.standard_price = res.cost_price
        
        return res
    
    def write(self, vals):
        """Override write to handle cost price changes"""
        res = super(ProductCostHistory, self).write(vals)
        
        # If cost price is updated, check if need to update product standard price
        if 'cost_price' in vals or 'date' in vals:
            for record in self:
                latest_cost = self.search([
                    ('product_id', '=', record.product_id.id),
                    ('active', '=', True)
                ], order='date desc', limit=1)
                
                if latest_cost and latest_cost.id == record.id:
                    record.product_id.standard_price = record.cost_price
        
        return res
    
    @api.model
    def get_cost_trend(self, product_id, period='6months'):
        """Get cost trend data for charts"""
        domain = [('product_id', '=', product_id)]
        
        # Set date filter based on period
        if period == '1month':
            date_from = fields.Datetime.now() - timedelta(days=30)
        elif period == '3months':
            date_from = fields.Datetime.now() - timedelta(days=90)
        elif period == '6months':
            date_from = fields.Datetime.now() - timedelta(days=180)
        elif period == '1year':
            date_from = fields.Datetime.now() - timedelta(days=365)
        else:
            date_from = False
        
        if date_from:
            domain.append(('date', '>=', date_from))
        
        records = self.search(domain, order='date asc')
        
        return {
            'dates': [r.date.strftime('%Y-%m-%d') for r in records],
            'costs': [r.cost_price for r in records],
            'vendors': [r.vendor_id.name or 'N/A' for r in records],
            'quantities': [r.quantity for r in records]
        }
    
    @api.model
    def get_vendor_comparison(self, product_id):
        """Get vendor price comparison"""
        records = self.search([
            ('product_id', '=', product_id),
            ('vendor_id', '!=', False)
        ])
        
        vendor_data = {}
        for record in records:
            vendor_name = record.vendor_id.name
            if vendor_name not in vendor_data:
                vendor_data[vendor_name] = {
                    'costs': [],
                    'dates': [],
                    'avg_cost': 0,
                    'min_cost': 0,
                    'max_cost': 0,
                    'last_cost': 0,
                    'vendor_id': record.vendor_id.id
                }
            
            vendor_data[vendor_name]['costs'].append(record.cost_price)
            vendor_data[vendor_name]['dates'].append(record.date)
        
        # Calculate statistics
        for vendor, data in vendor_data.items():
            costs = data['costs']
            data['avg_cost'] = sum(costs) / len(costs)
            data['min_cost'] = min(costs)
            data['max_cost'] = max(costs)
            data['last_cost'] = costs[-1]  # Assuming ordered by date
        
        return vendor_data
    
    def action_create_purchase_order(self):
        """Create purchase order from this cost history"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Purchase Order'),
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'context': {
                'default_partner_id': self.vendor_id.id,
                'default_order_line': [(0, 0, {
                    'product_id': self.product_id.id,
                    'name': self.product_id.name,
                    'product_qty': self.quantity,
                    'price_unit': self.cost_price,
                    'date_planned': fields.Datetime.now(),
                })]
            },
            'target': 'current',
        }
    
    @api.model
    def create_from_purchase_order_line(self, po_line):
        """Create cost history from purchase order line"""
        return self.create({
            'product_id': po_line.product_id.id,
            'date': po_line.order_id.date_order,
            'cost_price': po_line.price_unit,
            'vendor_id': po_line.order_id.partner_id.id,
            'purchase_order_id': po_line.order_id.id,
            'quantity': po_line.product_qty,
            'currency_id': po_line.currency_id.id,
        })