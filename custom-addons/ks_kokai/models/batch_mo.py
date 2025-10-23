# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class BatchManufacturingOrder(models.Model):
    _name = 'batch.manufacturing.order'
    _description = 'Batch Manufacturing Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'name'

    name = fields.Char(
        string='BMO Number',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: 'New',
        tracking=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)
    
    date_created = fields.Datetime(
        string='Created Date',
        default=fields.Datetime.now,
        readonly=True,
        tracking=True
    )
    
    date_processed = fields.Datetime(
        string='Processed Date',
        readonly=True,
        tracking=True
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Responsible',
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )
    
    storage_location_id = fields.Many2one(
        'stock.location',
        string='Storage Location',
        domain=[('usage', '=', 'internal')],
        required=True,
        tracking=True,
        help='Location where raw materials are checked for availability'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        tracking=True
    )
    
    # Fix Many2many fields - remove explicit column names
    mo_ids = fields.Many2many(
        'mrp.production',
        relation='batch_mo_available_rel',
        string='Available Manufacturing Orders',
        help='Manufacturing Orders that can be processed based on material availability'
    )
    
    selected_mo_ids = fields.Many2many(
        'mrp.production',
        relation='batch_mo_selected_rel',
        string='Selected Manufacturing Orders',
        help='Select MOs to process in batch'
    )
    
    processed_mo_ids = fields.Many2many(
        'mrp.production',
        relation='batch_mo_processed_rel',
        string='Processed Manufacturing Orders',
        readonly=True,
        help='MOs that have been successfully processed'
    )
    
    check_result = fields.Text(
        string='Availability Check Result',
        readonly=True
    )
    
    auto_reserve = fields.Boolean(
        string='Auto Reserve Materials',
        default=True,
        help='Automatically reserve materials for selected MOs'
    )
    
    priority_order = fields.Selection([
        ('date', 'By Scheduled Date'),
        ('priority', 'By Priority'),
        ('qty', 'By Quantity (Ascending)'),
        ('product', 'By Product Name')
    ], string='Priority Order', default='date',
    help='Order in which MOs should be prioritized')
    
    # Statistics fields
    total_mo_count = fields.Integer(
        string='Total MOs Found',
        compute='_compute_mo_statistics',
        store=True
    )
    
    selected_mo_count = fields.Integer(
        string='Selected MOs',
        compute='_compute_mo_statistics',
        store=True
    )
    
    processed_mo_count = fields.Integer(
        string='Processed MOs',
        compute='_compute_mo_statistics',
        store=True
    )
    
    success_rate = fields.Float(
        string='Success Rate (%)',
        compute='_compute_mo_statistics',
        store=True
    )
    
    notes = fields.Text(string='Notes')

    mo_selection_ids = fields.One2many(
        'batch.mo.selection',
        'batch_id',
        string='MO Selection Helper',
        readonly=True
    )

    selection_state = fields.Text(
        string='Selection State',
        help='JSON storage for selection state'
    )
    
    def _get_selection_state(self):
        """Get current selection state as dict"""
        if self.selection_state:
            import json
            try:
                return json.loads(self.selection_state)
            except:
                return {}
        return {}
    
    def _set_selection_state(self, state_dict):
        """Set selection state from dict"""
        import json
        self.selection_state = json.dumps(state_dict)
    
    # @api.onchange('mo_selection_lines', 'mo_selection_lines.is_selected')
    # def _onchange_mo_selection_lines(self):
    #     """Update selected_mo_ids and state when selection changes"""
    #     if self.mo_selection_lines:
    #         selected_mo_ids = []
    #         selection_state = {}
            
    #         for line in self.mo_selection_lines:
    #             if line.is_selected and line.mo_id:
    #                 selected_mo_ids.append(line.mo_id.id)
    #             if line.mo_id:
    #                 selection_state[line.mo_id.id] = line.is_selected
            
    #         self.selected_mo_ids = [(6, 0, selected_mo_ids)]
    #         self._set_selection_state(selection_state)

    
    def action_refresh_selection(self):
        """Refresh the selection helper lines"""
        self.ensure_one()
        # Clear existing lines
        self.mo_selection_ids.unlink()
        
        # Create new lines for each available MO
        for mo in self.mo_ids:
            self.env['batch.mo.selection'].create({
                'batch_id': self.id,
                'mo_id': mo.id,
                'is_selected': mo.id in self.selected_mo_ids.ids
            })

    mo_selection_ids = fields.One2many(
        'batch.mo.selection',
        'batch_id',
        string='MO Selection Helper',
        readonly=True
    )
    
    def action_refresh_selection(self):
        """Refresh the selection helper lines"""
        self.ensure_one()
        # Clear existing lines
        self.mo_selection_ids.unlink()
        
        # Create new lines for each available MO
        for mo in self.mo_ids:
            self.env['batch.mo.selection'].create({
                'batch_id': self.id,
                'mo_id': mo.id,
                'is_selected': mo.id in self.selected_mo_ids.ids
            })


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('batch.manufacturing.order') or 'New'
        res = super(BatchManufacturingOrder, self).create(vals)
        res._sync_selection_from_lines()
        return res

    # def write(self, vals):
    #     """Override write to maintain selection sync"""
    #     # Store current selection state before write
    #     selection_states = {}
    #     for record in self:
    #         if record.mo_selection_lines:
    #             selection_states[record.id] = {
    #                 line.mo_id.id: line.is_selected 
    #                 for line in record.mo_selection_lines
    #             }
        
    #     res = super(BatchManufacturingOrder, self).write(vals)
        
    #     # Restore selection state after write
    #     for record in self:
    #         if record.id in selection_states and record.mo_selection_lines:
    #             for line in record.mo_selection_lines:
    #                 if line.mo_id.id in selection_states[record.id]:
    #                     line.is_selected = selection_states[record.id][line.mo_id.id]
            
    #         # Sync selected_mo_ids from lines
    #         record._sync_selection_from_lines()
        
    #     return res
    
    def write(self, vals):
        """Override write without recursion"""
        # Skip sync if we're already in sync process
        if self._context.get('syncing'):
            return super(BatchManufacturingOrder, self).write(vals)
        
        res = super(BatchManufacturingOrder, self).write(vals)
        
        # Sync after write if needed
        if 'mo_selection_lines' not in vals and not self._context.get('skip_sync'):
            self.with_context(syncing=True)._sync_selection_count()
        
        return res

    def _sync_selection_count(self):
        """Sync selection count without triggering recursion"""
        for record in self:
            if record.mo_selection_lines:
                count = len(record.mo_selection_lines.filtered('is_selected'))
                if count != record.selected_mo_count:
                    # Direct SQL update to avoid recursion
                    self.env.cr.execute("""
                        UPDATE batch_manufacturing_order 
                        SET selected_mo_count = %s 
                        WHERE id = %s
                    """, (count, record.id))

    
    def _sync_selection_from_lines(self):
        """Sync selected_mo_ids from mo_selection_lines"""
        for record in self:
            if record.mo_selection_lines:
                selected_mo_ids = record.mo_selection_lines.filtered('is_selected').mapped('mo_id').ids
                record.selected_mo_ids = [(6, 0, selected_mo_ids)]    
    
    @api.depends('mo_ids', 'selected_mo_ids', 'processed_mo_ids', 'mo_selection_lines', 'mo_selection_lines.is_selected')
    def _compute_mo_statistics(self):
        for record in self:
            # Sync from lines first if available
            if record.mo_selection_lines and not self._context.get('skip_sync'):
                selected_from_lines = record.mo_selection_lines.filtered('is_selected').mapped('mo_id').ids
                if set(selected_from_lines) != set(record.selected_mo_ids.ids):
                    record.with_context(skip_sync=True).selected_mo_ids = [(6, 0, selected_from_lines)]
            
            record.total_mo_count = len(record.mo_ids)
            record.selected_mo_count = len(record.selected_mo_ids)
            record.processed_mo_count = len(record.processed_mo_ids)
            
            if record.selected_mo_count > 0:
                record.success_rate = (record.processed_mo_count / record.selected_mo_count) * 100
            else:
                record.success_rate = 0
    
    # @api.onchange('mo_selection_lines', 'mo_selection_lines.is_selected')
    # def _onchange_mo_selection_lines(self):
    #     """Update selected_mo_ids based on checkbox selection"""
    #     if self.mo_selection_lines:
    #         selected_mo_ids = self.mo_selection_lines.filtered('is_selected').mapped('mo_id').ids
    #         self.selected_mo_ids = [(6, 0, selected_mo_ids)]
            
    def action_confirm(self):
        """Confirm the BMO"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError("Only draft BMO can be confirmed.")
        self.state = 'confirmed'
        self.message_post(body="BMO confirmed.")

    def action_cancel(self):
        """Cancel the BMO"""
        self.ensure_one()
        if self.state in ['done']:
            raise UserError("Cannot cancel completed BMO.")
        self.state = 'cancel'
        self.message_post(body="BMO cancelled.")

    def action_reset_to_draft(self):
        """Reset BMO to draft"""
        self.ensure_one()
        self.state = 'draft'
        # Clear all many2many fields
        self.mo_ids = [(5, 0, 0)]
        self.selected_mo_ids = [(5, 0, 0)]
        self.processed_mo_ids = [(5, 0, 0)]
        self.check_result = False
        self.date_processed = False
        self.message_post(body="BMO reset to draft.")

    # def action_find_available_mos(self):
    #     """Find Manufacturing Orders that can be processed based on raw material availability"""
    #     self.ensure_one()
        
    #     if self.state not in ['draft', 'confirmed']:
    #         raise UserError("Cannot find MOs in current state.")
        
    #     if not self.storage_location_id:
    #         raise UserError("Please select a storage location first.")
        
    #     # Find all confirmed MOs that are not started yet
    #     domain = [
    #         ('state', 'in', ['confirmed', 'planned', 'progress','draft']),
    #         ('company_id', '=', self.company_id.id),
    #     ]
        
    #     all_mos = self.env['mrp.production'].search(domain)
        
    #     if not all_mos:
    #         self.check_result = "No active Manufacturing Orders found."
    #         return
        
    #     available_mos = []
    #     check_results = []
        
    #     for mo in all_mos:
    #         availability_result = self._check_mo_availability(mo)
    #         if availability_result['available']:
    #             available_mos.append(mo.id)
    #             check_results.append(f"✓ {mo.name} - {mo.product_id.name} - All materials available")
    #         else:
    #             missing_materials = ', '.join(availability_result['missing_materials'])
    #             check_results.append(f"✗ {mo.name} - {mo.product_id.name} - Missing: {missing_materials}")
        
    #     # Sort available MOs based on priority order
    #     if available_mos:
    #         available_mo_records = self.env['mrp.production'].browse(available_mos)
    #         available_mo_records = self._sort_mos_by_priority(available_mo_records)
    #         available_mos = available_mo_records.ids
        
    #     self.mo_ids = [(6, 0, available_mos)]
    #     self.selected_mo_ids = [(6, 0, available_mos)]  # Auto-select all available
    #     self.check_result = '\n'.join(check_results)
        
    #     # if self.state == 'draft':
    #     #     self.action_confirm()
        
    #     self.message_post(body=f"Found {len(available_mos)} available Manufacturing Orders.")

    def action_process_selected(self):
        """Process all selected Manufacturing Orders"""
        self.ensure_one()
        
        if self.state != 'confirmed':
            raise UserError(_("BMO must be confirmed before processing."))
        
        if not self.selected_mo_ids:
            raise UserError(_("No Manufacturing Orders selected. Please select at least one MO to process."))
        
        # Change state to in_progress
        self.state = 'in_progress'
        
        # Process results tracking
        results = {
            'success': [],
            'failed': [],
            'warnings': []
        }
        
        # Process each selected MO
        total_mos = len(self.selected_mo_ids)
        processed = 0
        
        for mo in self.selected_mo_ids:
            try:
                # Re-check availability before processing
                availability = self._check_mo_availability(mo)
                
                if not availability['available']:
                    results['failed'].append({
                        'mo': mo.name,
                        'reason': f"Materials no longer available: {', '.join(availability['missing_materials'])}"
                    })
                    continue
                
                # Process based on MO state
                if mo.state == 'draft':
                    # Confirm the MO first
                    mo.action_confirm()
                
                # Reserve materials if auto_reserve is enabled
                if self.auto_reserve and mo.state in ['confirmed', 'planned']:
                    mo.action_assign()
                
                # Check reservation state
                if mo.reservation_state != 'assigned':
                    # Try to reserve
                    mo.action_assign()
                    
                    if mo.reservation_state != 'assigned':
                        results['warnings'].append({
                            'mo': mo.name,
                            'reason': 'Partial reservation only'
                        })
                
                # Mark MO as ready if all materials are reserved
                if mo.state == 'confirmed' and mo.reservation_state == 'assigned':
                    # MO is ready to start
                    results['success'].append({
                        'mo': mo.name,
                        'product': mo.product_id.name,
                        'qty': mo.product_qty,
                        'state': 'Ready to produce'
                    })
                    processed += 1
                else:
                    results['warnings'].append({
                        'mo': mo.name,
                        'reason': f'MO in state {mo.state}, reservation: {mo.reservation_state}'
                    })
                
            except Exception as e:
                results['failed'].append({
                    'mo': mo.name,
                    'reason': str(e)
                })
        
        # Update processed MOs
        successful_mo_ids = self.selected_mo_ids.filtered(
            lambda m: any(s['mo'] == m.name for s in results['success'])
        ).ids
        self.processed_mo_ids = [(6, 0, successful_mo_ids)]
        
        # Generate result message
        result_message = self._generate_process_result_message(results, total_mos)
        self.check_result = result_message
        self.selected_mo_count = len(self.selected_mo_ids)        
        # Update state
        if results['success']:
            self.state = 'done'
            self.date_processed = fields.Datetime.now()
        else:
            self.state = 'confirmed'  # Back to confirmed if all failed
        
        # Post message
        self.message_post(body=result_message)
        
        # Show notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Batch Processing Result'),
                'message': f"Processed {len(results['success'])} of {total_mos} Manufacturing Orders",
                'type': 'success' if results['success'] else 'warning',
                'sticky': True,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }
    
    def _generate_process_result_message(self, results, total):
        """Generate detailed result message"""
        lines = [f"<h4>Batch Processing Completed</h4>"]
        lines.append(f"<p>Total MOs processed: {total}</p>")
        
        if results['success']:
            lines.append(f"<p><strong>✅ Successfully Processed ({len(results['success'])}):</strong></p>")
            lines.append("<ul>")
            for item in results['success']:
                lines.append(f"<li>{item['mo']} - {item['product']} (Qty: {item['qty']}) - {item['state']}</li>")
            lines.append("</ul>")
        
        if results['warnings']:
            lines.append(f"<p><strong>⚠️ Warnings ({len(results['warnings'])}):</strong></p>")
            lines.append("<ul>")
            for item in results['warnings']:
                lines.append(f"<li>{item['mo']} - {item['reason']}</li>")
            lines.append("</ul>")
        
        if results['failed']:
            lines.append(f"<p><strong>❌ Failed ({len(results['failed'])}):</strong></p>")
            lines.append("<ul>")
            for item in results['failed']:
                lines.append(f"<li>{item['mo']} - {item['reason']}</li>")
            lines.append("</ul>")
        
        return '\n'.join(lines)
    
    def action_view_processing_result(self):
        """Show detailed processing result"""
        self.ensure_one()
        
        # Create wizard to show results
        return {
            'name': _('Batch Processing Results'),
            'type': 'ir.actions.act_window',
            'res_model': 'batch.mo.result.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_batch_id': self.id,
                'default_result_html': self.check_result or 'No results available'
            }
        }


    def action_find_available_mos(self):
        """Find Manufacturing Orders that can be processed based on raw material availability"""
        self.ensure_one()
        
        previously_selected = self.selected_mo_ids.ids
        if self.state not in ['draft', 'confirmed']:
            raise UserError("Cannot find MOs in current state.")
        
        if not self.storage_location_id:
            raise UserError("Please select a storage location first.")
        
        # Find all confirmed MOs that are not started yet
        domain = [
            ('state', 'in', ['confirmed', 'planned', 'progress','draft']),
            ('company_id', '=', self.company_id.id),
        ]
        
        all_mos = self.env['mrp.production'].search(domain)
        
        if not all_mos:
            self.check_result = "No active Manufacturing Orders found."
            return
        
        available_mos = []
        check_results = []
        
        for mo in all_mos:
            availability_result = self._check_mo_availability(mo)
            if availability_result['available']:
                available_mos.append(mo.id)
                check_results.append(f"✓ {mo.name} - {mo.product_id.name} - All materials available")
            else:
                missing_materials = ', '.join(availability_result['missing_materials'])
                check_results.append(f"✗ {mo.name} - {mo.product_id.name} - Missing: {missing_materials}")
        
        # Sort available MOs based on priority order
        if available_mos:
            available_mo_records = self.env['mrp.production'].browse(available_mos)
            available_mo_records = self._sort_mos_by_priority(available_mo_records)
            available_mos = available_mo_records.ids
        
        self.mo_ids = [(6, 0, available_mos)]
        self.selected_mo_ids = [(5, 0, 0)]  # Clear previous selection
        self.check_result = '\n'.join(check_results)
        
        # Create/Update selection lines
        self.mo_selection_lines = [(5, 0, 0)]  # Clear existing lines
        
        selection_lines = []
        for mo_id in available_mos:
            # Check if was previously selected
            is_selected = mo_id in previously_selected
            selection_lines.append((0, 0, {
                'mo_id': mo_id,
                'is_selected': is_selected
            }))
        
        self.mo_selection_lines = selection_lines
        
        # Sync selected_mo_ids
        self._sync_selection_from_lines()

        
        self.message_post(body=f"Found {len(available_mos)} available Manufacturing Orders. Please select the ones to process.")
        
    def action_select_all(self):
        """Select all available MOs"""
        self.ensure_one()
        for line in self.mo_selection_lines:
            line.is_selected = True
        self._onchange_mo_selection_lines()
        
    def action_deselect_all(self):
        """Deselect all MOs"""
        self.ensure_one()
        for line in self.mo_selection_lines:
            line.is_selected = False
        self._onchange_mo_selection_lines()    
    
    def action_process_batch(self):
        """Process selected Manufacturing Orders in batch"""
        self.ensure_one()
        
        if self.state != 'confirmed':
            raise UserError("Please confirm BMO before processing.")
        
        if not self.selected_mo_ids:
            raise UserError("Please select at least one Manufacturing Order to process.")
        
        self.state = 'in_progress'
        processed_mos = []
        failed_mos = []
        
        for mo in self.selected_mo_ids:
            try:
                # Re-check availability before processing
                availability = self._check_mo_availability(mo)
                if not availability['available']:
                    failed_mos.append(f"{mo.name} - Materials no longer available")
                    continue
                
                # Reserve materials if auto_reserve is enabled
                if self.auto_reserve:
                    mo.action_assign()
                
                # Check if MO can be started
                if mo.state == 'confirmed':
                    mo.action_confirm()
                
                if mo.reservation_state == 'assigned':
                    processed_mos.append(mo.id)
                else:
                    failed_mos.append(f"{mo.name} - Could not reserve all materials")
                    
            except Exception as e:
                failed_mos.append(f"{mo.name} - Error: {str(e)}")
        
        # Update processed MOs
        self.processed_mo_ids = [(6, 0, processed_mos)]
        self.date_processed = fields.Datetime.now()
        self.state = 'done'
        
        # Prepare result message
        result_message = f"Batch processing completed!\n\n"
        
        if processed_mos:
            result_message += f"Successfully processed ({len(processed_mos)}):\n"
            mo_names = self.env['mrp.production'].browse(processed_mos).mapped('name')
            result_message += "\n".join(f"✓ {mo}" for mo in mo_names)
        
        if failed_mos:
            result_message += f"\n\nFailed to process ({len(failed_mos)}):\n"
            result_message += "\n".join(f"✗ {mo}" for mo in failed_mos)
        
        self.check_result = result_message
        self.message_post(body=result_message)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Batch Processing Result',
                'message': result_message,
                'type': 'success' if processed_mos and not failed_mos else 'warning',
                'sticky': True,
            }
        }

    def _check_mo_availability(self, mo):
        """Check if all raw materials for MO are available in specified location"""
        missing_materials = []
        available = True
        
        for move in mo.move_raw_ids.filtered(lambda m: m.state not in ['done', 'cancel']):
            product = move.product_id
            required_qty = move.product_uom_qty
            
            # Get available quantity in the specified location
            available_qty = self._get_available_qty(product, self.storage_location_id)
            
            if available_qty < required_qty:
                available = False
                missing_materials.append(f"{product.name} (Need: {required_qty}, Available: {available_qty})")
        
        return {
            'available': available,
            'missing_materials': missing_materials
        }

    def _get_available_qty(self, product, location):
        """Get available quantity for product in specific location"""
        quants = self.env['stock.quant'].search([
            ('product_id', '=', product.id),
            ('location_id', 'child_of', location.id),
            ('quantity', '>', 0)
        ])
        
        return sum(quants.mapped('quantity')) - sum(quants.mapped('reserved_quantity'))

    def _sort_mos_by_priority(self, mos):
        """Sort MOs based on selected priority order"""
        if self.priority_order == 'date':
            return mos.sorted('date_planned_start')
        elif self.priority_order == 'priority':
            return mos.sorted('priority', reverse=True)
        elif self.priority_order == 'qty':
            return mos.sorted('product_qty')
        elif self.priority_order == 'product':
            return mos.sorted(lambda mo: mo.product_id.name)
        else:
            return mos

    mo_selection_lines = fields.One2many(
        'batch.mo.selection.line',
        'batch_id',
        string='MO Selection Lines'
    )

    def _onchange_mo_selection_lines(self):
        """Update selected_mo_ids when selection changes"""
        # Prevent recursion with context flag
        if self._context.get('skip_onchange'):
            return
        
        selected_mo_ids = []
        for line in self.mo_selection_lines:
            if line.is_selected and line.mo_id:
                selected_mo_ids.append(line.mo_id.id)
        
        self.with_context(skip_onchange=True).selected_mo_ids = [(6, 0, selected_mo_ids)]
    
    # @api.onchange('mo_selection_lines')
    # def _onchange_mo_selection_lines(self):
    #     """Update selected_mo_ids based on checkbox selection"""
    #     selected_mo_ids = []
    #     for line in self.mo_selection_lines:
    #         if line.is_selected and line.mo_id:
    #             selected_mo_ids.append(line.mo_id.id)
        
    #     self.selected_mo_ids = [(6, 0, selected_mo_ids)]


    def action_view_selected_mos(self):
        """View selected Manufacturing Orders in list view"""
        self.ensure_one()
        if not self.selected_mo_ids:
            raise UserError("No Manufacturing Orders selected.")
        
        return {
            'name': 'Selected Manufacturing Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.selected_mo_ids.ids)],
            'context': {'default_state': 'confirmed'},
        }

    def action_view_processed_mos(self):
        """View processed Manufacturing Orders"""
        self.ensure_one()
        if not self.processed_mo_ids:
            raise UserError("No Manufacturing Orders have been processed yet.")
        
        return {
            'name': 'Processed Manufacturing Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.processed_mo_ids.ids)],
        }

    def action_detailed_availability_report(self):
        """Generate detailed availability report"""
        self.ensure_one()
        if not self.mo_ids:
            raise UserError("Please find available MOs first.")
        
        report_lines = []
        
        for mo in self.mo_ids:
            report_lines.append(f"\n=== {mo.name} - {mo.product_id.name} ===")
            report_lines.append(f"Scheduled Date: {mo.date_planned_start}")
            report_lines.append(f"Quantity to Produce: {mo.product_qty} {mo.product_uom_id.name}")
            report_lines.append(f"Status: {mo.state}")
            report_lines.append("\nRaw Materials:")
            
            for move in mo.move_raw_ids:
                available_qty = self._get_available_qty(move.product_id, self.storage_location_id)
                required_qty = move.product_uom_qty
                status = "✓ Available" if available_qty >= required_qty else f"✗ Short by {required_qty - available_qty}"
                
                report_lines.append(
                    f"  • {move.product_id.name}: Required {required_qty} {move.product_uom.name}, "
                    f"Available {available_qty} - {status}"
                )
        
        self.check_result = '\n'.join(report_lines)
        self.message_post(body="Generated detailed availability report.")
        
        
class BatchMOSelection(models.TransientModel):
    _name = 'batch.mo.selection'
    _description = 'MO Selection Helper'
    
    batch_id = fields.Many2one('batch.manufacturing.order', required=True, ondelete='cascade')
    mo_id = fields.Many2one('mrp.production', string='Manufacturing Order', required=True)
    is_selected = fields.Boolean('Selected', default=False)
    
    # Related fields for display
    name = fields.Char(related='mo_id.name', string='Reference')
    product_id = fields.Many2one(related='mo_id.product_id', string='Product')
    product_qty = fields.Float(related='mo_id.product_qty', string='Quantity')
    product_uom_id = fields.Many2one(related='mo_id.product_uom_id', string='UoM')
    date_planned_start = fields.Datetime(related='mo_id.date_planned_start', string='Scheduled Date')
    priority = fields.Selection(related='mo_id.priority')
    state = fields.Selection(related='mo_id.state')
    
    def action_toggle_selection(self):
        """Toggle selection of this MO"""
        self.ensure_one()
        if self.is_selected:
            # Remove from selected
            self.batch_id.selected_mo_ids = [(3, self.mo_id.id)]
            self.is_selected = False
        else:
            # Add to selected
            self.batch_id.selected_mo_ids = [(4, self.mo_id.id)]
            self.is_selected = True
            
            
class BatchMOSelectionLine(models.TransientModel):
    _name = 'batch.mo.selection.line'
    _description = 'Batch MO Selection Line'
    
    batch_id = fields.Many2one('batch.manufacturing.order', required=True, ondelete='cascade')
    mo_id = fields.Many2one('mrp.production', string='Manufacturing Order', required=True)
    is_selected = fields.Boolean('Select', default=False)
    
    # Related fields untuk display
    name = fields.Char(related='mo_id.name', string='Reference', readonly=True)
    product_id = fields.Many2one(related='mo_id.product_id', string='Product', readonly=True)
    product_qty = fields.Float(related='mo_id.product_qty', string='Quantity', readonly=True)
    product_uom_id = fields.Many2one(related='mo_id.product_uom_id', string='UoM', readonly=True)
    date_planned_start = fields.Datetime(related='mo_id.date_planned_start', string='Scheduled Date', readonly=True)
    priority = fields.Selection(related='mo_id.priority', string='Priority', readonly=True)
    state = fields.Selection(related='mo_id.state', string='Status', readonly=True)
    reservation_state = fields.Selection(related='mo_id.reservation_state', string='Material Availability', readonly=True)


    @api.model
    def create(self, vals_list):
        res = super(BatchMOSelectionLine, self).create(vals_list)
        
        # Handle both single record and recordset
        for record in res:
            if record.mo_id and record.batch_id and record.mo_id.id in record.batch_id.selected_mo_ids.ids:
                record.is_selected = True
        
        return res

    # def create(self, vals):
    #     """Override create to check if MO was previously selected"""
    #     res = super(BatchMOSelectionLine, self).create(vals)
        
    #     # Check if this MO is in selected_mo_ids
    #     if res.batch_id and res.mo_id:
    #         if res.mo_id.id in res.batch_id.selected_mo_ids.ids:
    #             res.is_selected = True
        
    #     return res