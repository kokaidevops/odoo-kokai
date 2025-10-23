# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProjectRABLine(models.Model):
    _name = 'kokai.rab.line'
    _description = 'Project RAB Line'
    _order = 'sequence, id'

    # Basic Information
    rab_id = fields.Many2one(
        'kokai.rab',
        string='RAB',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequence', default=10)
    category_id = fields.Many2one(
        'kokai.rab.category',
        string='Category',
        # required=True
    )
    
    # Product Information
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        domain=[('purchase_ok', '=', True)]
    )
    description = fields.Text(
        string='Description',
        # required=True
    )
    is_stockable = fields.Boolean(
        string='Is Stockable',
        compute='_compute_is_stockable',
        store=True
    )
    # reason = fields.Char(
    #     string = "Reason",
    #     store = True
    # )
    reason = fields.Selection([
        ('pr_draft', 'PR Draft'),
        ('pr_approved', 'PR Approved'),
        ('po_done', 'PO Done = GR done'),
    ], string='Reason', tracking=True)
    
    # Quantity and Price
    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1.0
    )
    unit_id = fields.Many2one(
        'uom.uom',
        string='Unit',
        # required=True
    )
    unit_price = fields.Float(
        string='Unit Price',
        # required=True
    )
    subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True
    )
    
    # Cost Information
    cost_price = fields.Float(
        string='Cost Price',
        compute='_compute_cost_info',
        store=True
    )
    vendor_price = fields.Float(string='Vendor Price')
    last_purchase_price = fields.Float(
        string='Last Purchase Price',
        compute='_compute_cost_info'
    )
    average_price = fields.Float(
        string='Average Price',
        compute='_compute_cost_info'
    )
    margin_amount = fields.Float(
        string='Margin Amount',
        compute='_compute_margin',
        store=True
    )
    margin_percentage = fields.Float(
        string='Margin %',
        compute='_compute_margin',
        store=True
    )
    
    # Stock Information
    stock_available = fields.Float(
        string='Stock Available',
        compute='_compute_stock_info'
    )
    stock_forecast = fields.Float(
        string='Stock Forecast',
        compute='_compute_stock_info'
    )
    stock_status = fields.Selection([
        ('available', 'Available'),
        ('partial', 'Partial'),
        ('out_of_stock', 'Out of Stock'),
        ('na', 'N/A')
    ], string='Stock Status', compute='_compute_stock_status_info', store=True)
    
    # Supplier Information
    supplier_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        domain=[('supplier_rank', '>', 0)]
    )
    lead_time = fields.Integer(string='Lead Time (days)')
    min_qty = fields.Float(string='Minimum Quantity')
    
    # Additional
    notes = fields.Text(string='Notes')
    currency_id = fields.Many2one(
        related='rab_id.currency_id',
        string='Currency'
    )
    

    purchase_request_line_ids = fields.One2many(
        'purchase.request.line',
        'rab_line_id',
        string='Purchase Request Lines'
    )
    purchase_state = fields.Selection([
        ('none', 'Not Requested'),
        ('requested', 'PR Created'),
        ('approved', 'PR Approved'),
        ('partial', 'Partially Purchased'),
        ('done', 'Fully Purchased')
    ], string='Purchase Status', compute='_compute_purchase_state', store=True)
    
    stock_available_all_locations = fields.Float(
        string='Stock Available (All Locations)',
        compute='_compute_stock_info_all_locations',
        store=True
    )
    stock_by_location = fields.Text(
        string='Stock by Location',
        compute='_compute_stock_info_all_locations',
        store=True
    )
    
    @api.depends('product_id', 'quantity')
    def _compute_stock_info_all_locations(self):
        """Compute stock info across all locations"""
        for line in self:
            if line.product_id and line.is_stockable:
                # Get all stock locations
                locations = self.env['stock.location'].search([
                    ('usage', '=', 'internal'),
                    ('active', '=', True)
                ])
                
                total_qty = 0.0
                location_details = []
                
                # Calculate quantity for each location
                for location in locations:
                    qty = line.product_id.with_context(location=location.id).qty_available
                    if qty > 0:
                        total_qty += qty
                        location_details.append(f"{location.complete_name}: {qty:.2f} {line.unit_id.name if line.unit_id else ''}")
                
                line.stock_available_all_locations = total_qty
                line.stock_by_location = '\n'.join(location_details) if location_details else 'No stock in any location'
                
                # Update regular stock_available to use all locations total
                line.stock_available = total_qty
                
                # Update stock status based on all locations
                if line.quantity <= total_qty:
                    line.stock_status = 'available'
                elif total_qty > 0:
                    line.stock_status = 'partial'
                else:
                    line.stock_status = 'out_of_stock'
            else:
                line.stock_available_all_locations = 0
                line.stock_by_location = 'N/A'
                line.stock_available = 0
                line.stock_status = 'na'
    
    def action_view_stock_details(self):
        """Open detailed stock view by location"""
        self.ensure_one()
        
        if not self.product_id:
            raise ValidationError(_('Please select a product first.'))
        
        # Create a tree view for stock by location
        return {
            'name': _('Stock Details: %s') % self.product_id.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'stock.quant',
            'view_mode': 'tree,form',
            'domain': [('product_id', '=', self.product_id.id)],
            'context': {
                'search_default_internal_loc': 1,
                'group_by': ['location_id']
            },
            'target': 'new',
        }
    
    @api.model
    def create(self, vals):
        """Auto-fill sequence and trigger stock calculation"""
        if 'sequence' not in vals:
            max_sequence = self.search([
                ('rab_id', '=', vals.get('rab_id'))
            ], order='sequence desc', limit=1)
            vals['sequence'] = max_sequence.sequence + 10 if max_sequence else 10
        
        line = super(ProjectRABLine, self).create(vals)
        # Trigger stock calculation for new line
        line._compute_stock_info_all_locations()
        return line
    
    def write(self, vals):
        """Trigger stock recalculation on relevant changes"""
        res = super(ProjectRABLine, self).write(vals)
        if 'product_id' in vals or 'quantity' in vals:
            self._compute_stock_info_all_locations()
        return res


    @api.depends('purchase_request_line_ids', 'purchase_request_line_ids.request_id.state')
    def _compute_purchase_state(self):
        for line in self:
            if not line.purchase_request_line_ids:
                line.purchase_state = 'none'
            else:
                states = line.purchase_request_line_ids.mapped('request_id.state')
                if all(state == 'done' for state in states):
                    line.purchase_state = 'done'
                elif all(state == 'approved' for state in states):
                    line.purchase_state = 'approved'
                elif any(state in ['approved', 'done'] for state in states):
                    line.purchase_state = 'partial'
                else:
                    line.purchase_state = 'requested'
                    
                # Update reason based on state
                if 'approved' in states:
                    line.reason = 'pr_approved'
                elif 'done' in states:
                    line.reason = 'po_done'

    def action_view_purchase_request_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "purchase_request.purchase_request_line_form_action"
        )
        if len(self.purchase_request_line_ids) > 1:
            action['domain'] = [('id', 'in', self.purchase_request_line_ids.ids)]
        elif self.purchase_request_line_ids:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.purchase_request_line_ids.id
        return action

    
    @api.depends('product_id')
    def _compute_is_stockable(self):
        for line in self:
            if line.product_id:
                line.is_stockable = line.product_id.type in ['product', 'consu']
            else:
                line.is_stockable = False
    
    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price
    
    @api.depends('product_id')
    def _compute_cost_info(self):
        for line in self:
            if line.product_id:
                line.cost_price = line.product_id.standard_price
                
                # Get last purchase price
                last_purchase = self.env['purchase.order.line'].search([
                    ('product_id', '=', line.product_id.id),
                    ('state', 'in', ['purchase', 'done'])
                ], order='create_date desc', limit=1)
                line.last_purchase_price = last_purchase.price_unit if last_purchase else 0
                
                # Calculate average price from cost history
                history = self.env['product.cost.history'].search([
                    ('product_id', '=', line.product_id.id)
                ], limit=10)
                if history:
                    line.average_price = sum(history.mapped('cost_price')) / len(history)
                else:
                    line.average_price = line.cost_price
            else:
                line.cost_price = 0
                line.last_purchase_price = 0
                line.average_price = 0
    
    @api.depends('cost_price', 'unit_price', 'quantity')
    def _compute_margin(self):
        for line in self:
            if line.cost_price > 0:
                line.margin_amount = (line.unit_price - line.cost_price) * line.quantity
                line.margin_percentage = ((line.unit_price - line.cost_price) / line.cost_price) * 100
            else:
                line.margin_amount = 0
                line.margin_percentage = 0
    
    @api.depends('product_id', 'quantity')
    def _compute_stock_info(self):
        for line in self:
            if line.product_id and line.is_stockable:
                line.stock_available = line.product_id.qty_available
                line.stock_forecast = line.product_id.virtual_available
                
                # if line.quantity <= line.stock_available:
                #     line.stock_status = 'available'
                # elif line.stock_available > 0:
                #     line.stock_status = 'partial'
                # else:
                #     line.stock_status = 'out_of_stock'
            else:
                line.stock_available = 0
                line.stock_forecast = 0
                # line.stock_status = 'na'
                
    @api.depends('product_id', 'quantity')
    def _compute_stock_status_info(self):
        for line in self:
            if line.product_id and line.is_stockable:
                # line.stock_available = line.product_id.qty_available
                # line.stock_forecast = line.product_id.virtual_available
                
                if line.quantity <= line.stock_available:
                    line.stock_status = 'available'
                elif line.stock_available > 0:
                    line.stock_status = 'partial'
                else:
                    line.stock_status = 'out_of_stock'
            else:
                # line.stock_available = 0
                # line.stock_forecast = 0
                line.stock_status = 'na'
                
                
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name
            self.unit_id = self.product_id.uom_id
            self.unit_price = self.product_id.list_price
            
            # Get default supplier
            if self.product_id.seller_ids:
                seller = self.product_id.seller_ids[0]
                self.supplier_id = seller.partner_id
                self.vendor_price = seller.price
                self.lead_time = seller.delay
                self.min_qty = seller.min_qty
    
    @api.constrains('quantity')
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_('Quantity must be greater than zero.'))
            
            
    @api.depends('purchase_request_line_ids.product_qty')
    def _compute_requested_qty(self):
        for line in self:
            line.requested_qty = sum(line.purchase_request_line_ids.mapped('product_qty'))
    
    @api.depends('quantity', 'requested_qty')
    def _compute_remaining_qty(self):
        for line in self:
            line.remaining_qty = max(0, line.quantity - line.requested_qty)
    
    def action_create_purchase_request(self):
        """Create PR for this specific line"""
        self.ensure_one()
        
        if self.remaining_qty <= 0:
            raise ValidationError(_('All quantity has been requested.'))
        
        # Prepare PR values
        pr_vals = {
            'requested_by': self.env.user.id,
            'date_start': fields.Date.today(),
            'description': f"PR from RAB: {self.rab_id.name}",
        }
        
        # Create PR
        pr = self.env['purchase.request'].create(pr_vals)
        
        # Create PR line
        pr_line_vals = {
            'request_id': pr.id,
            'product_id': self.product_id.id,
            'name': self.description or self.product_id.name,
            'product_qty': self.remaining_qty,
            'product_uom_id': self.unit_id.id,
            'rab_line_id': self.id,
            'estimated_cost': self.unit_price,
        }
        self.env['purchase.request.line'].create(pr_line_vals)
        
        # Update reason
        self.reason = 'pr_draft'
        
        # Open created PR
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.request',
            'res_id': pr.id,
            'view_mode': 'form',
            'target': 'current',
        }