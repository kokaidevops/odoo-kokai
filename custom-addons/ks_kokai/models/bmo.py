# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class BatchManufacturingOrder(models.TransientModel):
    _name = 'batch.manufacturing.order'
    _description = 'Batch Manufacturing Order - Smart MO Finder'

    storage_location_id = fields.Many2one(
        'stock.location',
        string='Storage Location',
        domain=[('usage', '=', 'internal')],
        required=True,
        help='Location where raw materials are checked for availability'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    
    mo_ids = fields.Many2many(
        'mrp.production',
        string='Available Manufacturing Orders',
        help='Manufacturing Orders that can be processed based on material availability'
    )
    
    selected_mo_ids = fields.Many2many(
        'mrp.production',
        'batch_mo_selected_rel',
        string='Selected Manufacturing Orders',
        help='Select MOs to process in batch'
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

    @api.onchange('storage_location_id')
    def _onchange_storage_location(self):
        """Reset MO selection when location changes"""
        if self.storage_location_id:
            self.mo_ids = False
            self.selected_mo_ids = False
            self.check_result = False

    def action_find_available_mos(self):
        """Find Manufacturing Orders that can be processed based on raw material availability"""
        if not self.storage_location_id:
            raise UserError("Please select a storage location first.")
        
        # Find all confirmed MOs that are not started yet
        domain = [
            ('state', 'in', ['confirmed', 'planned', 'progress']),
            ('company_id', '=', self.company_id.id),
            ('reservation_state', 'in', ['confirmed', 'partially_available', 'assigned'])
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
        self.selected_mo_ids = [(6, 0, available_mos)]  # Auto-select all available
        
        self.check_result = '\n'.join(check_results)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'batch.manufacturing.order',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context
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

    def action_process_batch(self):
        """Process selected Manufacturing Orders in batch"""
        if not self.selected_mo_ids:
            raise UserError("Please select at least one Manufacturing Order to process.")
        
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
                    processed_mos.append(mo.name)
                else:
                    failed_mos.append(f"{mo.name} - Could not reserve all materials")
                    
            except Exception as e:
                failed_mos.append(f"{mo.name} - Error: {str(e)}")
        
        # Prepare result message
        result_message = f"Batch processing completed!\n\n"
        
        if processed_mos:
            result_message += f"Successfully processed ({len(processed_mos)}):\n"
            result_message += "\n".join(f"✓ {mo}" for mo in processed_mos)
        
        if failed_mos:
            result_message += f"\n\nFailed to process ({len(failed_mos)}):\n"
            result_message += "\n".join(f"✗ {mo}" for mo in failed_mos)
        
        # Show result in a message dialog
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

    def action_view_selected_mos(self):
        """View selected Manufacturing Orders in list view"""
        if not self.selected_mo_ids:
            raise UserError("No Manufacturing Orders selected.")
        
        return {
            'name': 'Selected Manufacturing Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.selected_mo_ids.ids)],
            'context': {'default_state': 'confirmed'},
            'target': 'current',
        }

    def action_detailed_availability_report(self):
        """Generate detailed availability report"""
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
        
        detailed_report = '\n'.join(report_lines)
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Detailed Availability Report',
            'res_model': 'batch.manufacturing.order',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_check_result': detailed_report}
        }