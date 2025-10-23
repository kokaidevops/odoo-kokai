from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    rab_ids = fields.One2many(
        'kokai.rab',
        'so_number',
        string='Related RABs',
        compute='_compute_rab_ids',
        store=False
    )
    rab_count = fields.Integer(
        string='RAB Count',
        compute='_compute_rab_count',
        store=False
    )
    

    mo_ids = fields.One2many(
        'mrp.production',
        'sale_order_id',
        string='Manufacturing Orders'
    )
    mo_count = fields.Integer(
        string='MO Count',
        compute='_compute_mo_count'
    )
    mo_generation_state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed')
    ], string='MO Generation Status', default='draft')
    
    @api.depends('mo_ids')
    def _compute_mo_count(self):
        for order in self:
            order.mo_count = len(order.mo_ids)

    def _generate_mo_by_levels(self, sale_line):
        """Generate MOs for a sale line based on BOM levels - return created MOs"""
        product = sale_line.product_id
        if not product.bom_ids:
            return self.env['mrp.production']
        
        bom = product.bom_ids[0]
        
        # Get template info if product was created from template
        template_id = product.product_tmpl_id.category_template_id
        
        if template_id:
            # Template-based generation
            return self._generate_template_based_mos(sale_line, bom, template_id)
        else:
            # Standard MO generation with multi-level BOM
            return self._generate_standard_mos(sale_line, bom)
    
    def action_open_generate_mo_wizard(self):
        """Open wizard to generate MOs"""
        self.ensure_one()
        
        # Check if SO is confirmed
        if self.state not in ['sale', 'done']:
            raise UserError(_('Sales Order must be confirmed first.'))
        
        # Check if there are products with BOM
        has_bom = any(line.product_id.bom_ids for line in self.order_line)
        print('=====')
        print(has_bom)
        if not has_bom:
            raise UserError(_('No products with BOM found in this order.'))
        
        return {
            'name': _('Generate Manufacturing Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'generate.mo.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'active_model': 'sale.order',
            }
        }

    def _generate_template_based_mos(self, sale_line, bom, template_id):
        """Generate MOs based on template structure"""
        created_mos = self.env['mrp.production']
        
        # Collect all components by level
        components_by_level = self._get_components_by_level(bom, template_id)
        
        # Create MOs from highest level to lowest (finished goods last)
        created_mo_by_template_line = {}
        
        for level in sorted(components_by_level.keys(), reverse=True):
            for component_data in components_by_level[level]:
                mo = self._create_mo_for_component(
                    component_data, 
                    sale_line, 
                    created_mo_by_template_line
                )
                if mo:
                    created_mos |= mo
                    template_line_id = component_data.get('template_line_id')
                    if template_line_id:
                        created_mo_by_template_line[template_line_id] = mo
        
        # Create MO for finished goods (level 0)
        finished_mo_vals = {
            'product_id': sale_line.product_id.id,
            'product_qty': sale_line.product_uom_qty,
            'product_uom_id': sale_line.product_uom.id,
            'bom_id': bom.id,
            'origin': sale_line.order_id.name,
            'sale_order_id': sale_line.order_id.id,
            'sale_line_id': sale_line.id,
            'state': 'draft',
            'level': 0,
        }
        
        # Link to component MOs
        component_mo_ids = [mo.id for mo in created_mos if mo.level == 1]
        if component_mo_ids:
            finished_mo_vals['child_mo_ids'] = [(6, 0, component_mo_ids)]
        
        finished_mo = self.env['mrp.production'].create(finished_mo_vals)
        created_mos |= finished_mo
        
        return created_mos
    
    def _generate_standard_mos(self, sale_line, bom):
        """Generate MOs for standard multi-level BOM"""
        created_mos = self.env['mrp.production']
        
        # Recursive function to create MOs for all levels
        def create_mo_recursive(product, qty_needed, parent_mo=None, level=0):
            if not product.bom_ids:
                return
            
            bom = product.bom_ids[0]
            
            # Create MO for this product
            mo_vals = {
                'product_id': product.id,
                'product_qty': qty_needed,
                'product_uom_id': product.uom_id.id,
                'bom_id': bom.id,
                'origin': sale_line.order_id.name,
                'sale_order_id': sale_line.order_id.id,
                'state': 'draft',
                'level': level,
            }
            
            if level == 0:  # Main product
                mo_vals['sale_line_id'] = sale_line.id
            
            if parent_mo:
                mo_vals['parent_mo_ids'] = [(4, parent_mo.id)]
            
            mo = self.env['mrp.production'].create(mo_vals)
            created_mos |= mo
            
            # Create MOs for components
            for bom_line in bom.bom_line_ids:
                if bom_line.product_id.bom_ids:
                    component_qty = bom_line.product_qty * qty_needed / bom.product_qty
                    create_mo_recursive(
                        bom_line.product_id, 
                        component_qty, 
                        mo, 
                        level + 1
                    )
            
            return mo
        
        # Start recursive creation
        create_mo_recursive(sale_line.product_id, sale_line.product_uom_qty)
        
        return created_mos


    def action_open_generate_mo_wizard(self):
        """Open wizard to generate MOs"""
        self.ensure_one()
        return {
            'name': _('Generate Manufacturing Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'generate.mo.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
            }
        }

    # def action_generate_manufacturing_orders(self):
    #     """Generate MOs based on product template levels"""
    #     self.ensure_one()
        
    #     if self.state not in ['sale', 'done']:
    #         raise UserError(_('Sales Order must be confirmed first.'))
        
    #     # Process each sale order line
    #     for line in self.order_line:
    #         if line.product_id.bom_ids:
    #             self._generate_mo_by_levels(line)
        
    #     self.mo_generation_state = 'done'
        
    #     # Show created MOs
    #     return self.action_view_manufacturing_orders()
    

    def action_generate_manufacturing_orders(self):
        """Main action to create MOs from sale order"""
        self.ensure_one()
        
        if self.state not in ['sale', 'done']:
            raise UserError(_('You can only create Manufacturing Orders for confirmed sales orders.'))
        
        all_mos = []
        
        for line in self.order_line:
            if not line.product_id or line.product_id.type != 'product':
                continue
                
            # Check if product has BOM
            bom = self.env['mrp.bom']._bom_find(products=line.product_id)[line.product_id]
            if not bom:
                continue
            
            print(f'\n=== Processing Sale Line: {line.product_id.name} ===')
            mos = self._generate_mo_by_levels(line)
            all_mos.extend(mos)
        
        if not all_mos:
            raise UserError(_('No manufacturing orders could be created. Please check if products have BOMs.'))
        
        # Return action to view created MOs
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        if len(all_mos) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': all_mos[0].id,
            })
        else:
            action.update({
                'domain': [('id', 'in', [mo.id for mo in all_mos])],
                'view_mode': 'tree,form',
            })
        
        return action

    # def _generate_mo_by_levels(self, sale_line):
    #     """Generate MOs for a sale line based on BOM series levels"""
    #     product = sale_line.product_id
    #     product_template = product.product_tmpl_id
        
    #     print(f'---Generating MOs for product: {product.name}')
    #     print(f'---Product template: {product_template.name}')
        
    #     # Check if product template has BOM series
    #     if not product_template.bom_series_ids:
    #         print('---No BOM series found, trying to generate...')
    #         try:
    #             product_template.generate_bom_series()
    #         except Exception as e:
    #             print(f'---Failed to generate BOM series: {e}')
    #             # Fallback to standard MO creation
    #             return self._create_standard_mo(sale_line)
        
    #     # Get BOM series ordered by level (highest to lowest)
    #     bom_series = product_template.bom_series_ids.sorted('level', reverse=True)
    #     print(f'---Found {len(bom_series)} BOM series entries')
        
    #     if not bom_series:
    #         print('---No BOM series available, creating standard MO')
    #         return self._create_standard_mo(sale_line)
        
    #     # Group BOM series by level
    #     series_by_level = {}
    #     for series in bom_series:
    #         level = series.level
    #         if level not in series_by_level:
    #             series_by_level[level] = []
    #         series_by_level[level].append(series)
        
    #     print(f'---BOM series grouped by levels: {list(series_by_level.keys())}')
        
    #     # Create MOs from highest level to lowest (reverse manufacturing order)
    #     created_mos = {}
    #     mo_sequence = 1
        
    #     for level in sorted(series_by_level.keys(), reverse=True):
    #         print(f'---Processing level {level} with {len(series_by_level[level])} series')
            
    #         for series in series_by_level[level]:
    #             print(f'---Creating MO for series: {series.bom_product_name} (BOM: {series.bom_reference})')
                
    #             mo = self._create_mo_for_bom_series(
    #                 series, 
    #                 sale_line, 
    #                 created_mos,
    #                 mo_sequence
    #             )
                
    #             if mo:
    #                 created_mos[series.id] = mo
    #                 mo_sequence += 1
    #                 print(f'---Created MO: {mo.name} for level {level}')
    #             else:
    #                 print(f'---Failed to create MO for series {series.id}')
        
    #     print(f'---Total MOs created: {len(created_mos)}')
    #     return list(created_mos.values())
    






    # def _create_mo_for_bom_series(self, bom_series, sale_line, created_mos, sequence):
    #     """Create Manufacturing Order for a specific BOM series entry"""
        
    #     try:
    #         # Determine the product to manufacture
    #         if bom_series.product_variant_id:
    #             product_to_manufacture = bom_series.product_variant_id
    #         else:
    #             # Use the BOM's product
    #             bom = bom_series.bom_id
    #             product_to_manufacture = bom.product_id or bom.product_tmpl_id.product_variant_id
            
    #         print(f'---Manufacturing product: {product_to_manufacture.name}')
            
    #         # Calculate quantity needed
    #         if bom_series.level == 1:
    #             # Level 1 is the final product - use sale line quantity
    #             qty_to_produce = sale_line.product_uom_qty
    #         else:
    #             # For sub-assemblies, calculate based on parent BOM requirements
    #             qty_to_produce = self._calculate_subassembly_quantity(
    #                 bom_series, 
    #                 sale_line, 
    #                 created_mos
    #             )
            
    #         print(f'---Quantity to produce: {qty_to_produce}')
            
    #         # Prepare MO values
    #         mo_vals = {
    #             'product_id': product_to_manufacture.id,
    #             'product_qty': qty_to_produce,
    #             'product_uom_id': product_to_manufacture.uom_id.id,
    #             'bom_id': bom_series.bom_id.id,
    #             'origin': sale_line.order_id.name,
    #             'date_planned_start': fields.Datetime.now(),
    #             'sale_line_id': sale_line.id,
    #             'production_level': bom_series.level,
    #             'production_sequence': sequence,
    #         }
            
    #         # Add custom fields if they exist
    #         if hasattr(self.env['mrp.production'], 'bom_series_id'):
    #             mo_vals['bom_series_id'] = bom_series.id
            
    #         # Create the Manufacturing Order
    #         mo = self.env['mrp.production'].create(mo_vals)
            
    #         print(f'---Created MO {mo.name} for {product_to_manufacture.name}')
    #         return mo
            
    #     except Exception as e:
    #         print(f'---Error creating MO for BOM series {bom_series.id}: {e}')
    #         return False

    # def _calculate_subassembly_quantity(self, bom_series, sale_line, created_mos):
    #     """Calculate quantity needed for sub-assembly based on parent requirements"""
        
    #     # Find parent BOM series
    #     parent_series = bom_series.parent_series_id
    #     if not parent_series:
    #         # If no parent, assume it's a top-level component
    #         return sale_line.product_uom_qty
        
    #     # Get the BOM line that requires this component
    #     parent_bom = parent_series.bom_id
    #     component_product = bom_series.bom_id.product_id or bom_series.bom_id.product_tmpl_id.product_variant_id
        
    #     # Find BOM line for this component in parent BOM
    #     bom_line = parent_bom.bom_line_ids.filtered(
    #         lambda line: line.product_id.product_tmpl_id.id == component_product.product_tmpl_id.id
    #     )
        
    #     if bom_line:
    #         # Calculate based on BOM line quantity and parent quantity
    #         parent_qty = sale_line.product_uom_qty  # Base quantity from sale
    #         required_qty = bom_line[0].product_qty * parent_qty
    #         print(f'---Calculated qty for {component_product.name}: {required_qty} (parent: {parent_qty}, bom ratio: {bom_line[0].product_qty})')
    #         return required_qty
    #     else:
    #         print(f'---BOM line not found for {component_product.name}, using sale qty')
    #         return sale_line.product_uom_qty

    def action_create_manufacturing_orders(self):
        """Main action to create MOs from sale order"""
        self.ensure_one()
        
        if self.state not in ['sale', 'done']:
            raise UserError(_('You can only create Manufacturing Orders for confirmed sales orders.'))
        
        all_mos = []
        
        for line in self.order_line:
            if not line.product_id or line.product_id.type != 'product':
                continue
                
            # Check if product has BOM
            bom = self.env['mrp.bom']._bom_find(products=line.product_id)[line.product_id]
            if not bom:
                continue
            
            print(f'\n=== Processing Sale Line: {line.product_id.name} ===')
            mos = self._generate_mo_by_levels(line)
            all_mos.extend(mos)
        
        if not all_mos:
            raise UserError(_('No manufacturing orders could be created. Please check if products have BOMs.'))
        
        # Return action to view created MOs
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        if len(all_mos) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': all_mos[0].id,
            })
        else:
            action.update({
                'domain': [('id', 'in', [mo.id for mo in all_mos])],
                'view_mode': 'tree,form',
            })
        
        return action


    def _generate_mo_by_levels(self, sale_line):
        """Generate MOs for a sale line based on BOM series levels"""
        product = sale_line.product_id
        product_template = product.product_tmpl_id
        
        print(f'---Generating MOs for product: {product.name}')
        print(f'---Product template: {product_template.name}')
        print(f'---Product tracking: {product.tracking}')
        print(f'---Requested quantity: {sale_line.product_uom_qty}')
        
        # Check if product template has BOM series
        if not product_template.bom_series_ids:
            print('---No BOM series found, trying to generate...')
            try:
                product_template.generate_bom_series()
            except Exception as e:
                print(f'---Failed to generate BOM series: {e}')
                # Fallback to standard MO creation
                return self._create_standard_mo_with_serial_split(sale_line)
        
        # Get BOM series ordered by level (highest to lowest)
        bom_series = product_template.bom_series_ids.sorted('level', reverse=True)
        print(f'---Found {len(bom_series)} BOM series entries')
        
        if not bom_series:
            print('---No BOM series available, creating standard MO')
            return self._create_standard_mo_with_serial_split(sale_line)
        
        # Check if main product has serial tracking
        has_serial_tracking = product.tracking == 'serial'
        mo_count = int(sale_line.product_uom_qty) if has_serial_tracking else 1
        qty_per_mo = 1.0 if has_serial_tracking else sale_line.product_uom_qty
        
        print(f'---Serial tracking: {has_serial_tracking}, Creating {mo_count} MO(s) with qty {qty_per_mo} each')
        
        all_created_mos = []
        
        # Create MOs for each unit if serial tracking is enabled
        for mo_index in range(mo_count):
            print(f'\n---Creating MO set #{mo_index + 1} of {mo_count}')
            
            # Group BOM series by level
            series_by_level = {}
            for series in bom_series:
                level = series.level
                if level not in series_by_level:
                    series_by_level[level] = []
                series_by_level[level].append(series)
            
            print(f'---BOM series grouped by levels: {list(series_by_level.keys())}')
            
            # Create MOs from highest level to lowest (reverse manufacturing order)
            created_mos_for_unit = {}
            mo_sequence = 1
            
            for level in sorted(series_by_level.keys(), reverse=True):
                print(f'---Processing level {level} with {len(series_by_level[level])} series')
                
                for series in series_by_level[level]:
                    print(f'---Creating MO for series: {series.bom_product_name} (BOM: {series.bom_reference})')
                    
                    # Adjust quantity based on level and serial tracking
                    if level == 1:  # Main product level
                        mo_qty = qty_per_mo
                    else:  # Sub-assembly levels
                        # Check if sub-assembly also has serial tracking
                        sub_product = series.bom_id.product_id or series.bom_id.product_tmpl_id.product_variant_ids[:1]
                        if sub_product and sub_product.tracking == 'serial':
                            # Calculate required quantity based on BOM
                            mo_qty = self._calculate_sub_assembly_qty(series, qty_per_mo, created_mos_for_unit)
                        else:
                            mo_qty = self._calculate_sub_assembly_qty(series, qty_per_mo, created_mos_for_unit)
                    
                    mo = self._create_mo_for_bom_series(
                        series, 
                        sale_line, 
                        created_mos_for_unit,
                        mo_sequence,
                        mo_qty,
                        mo_index + 1 if has_serial_tracking else None
                    )
                    
                    if mo:
                        created_mos_for_unit[series.id] = mo
                        all_created_mos.append(mo)
                        mo_sequence += 1
                        print(f'---Created MO: {mo.name} for level {level} with qty {mo_qty}')
                    else:
                        print(f'---Failed to create MO for series {series.id}')
            
        print(f'---Total MOs created: {len(all_created_mos)}')
        return all_created_mos

    def _create_mo_for_bom_series(self, series, sale_line, created_mos, sequence, quantity=None, unit_index=None):
        """Create MO for a specific BOM series entry with serial tracking support"""
        
        bom = series.bom_id
        product = bom.product_id or bom.product_tmpl_id.product_variant_ids[:1]
        
        if not product:
            print(f'---No product found for BOM {bom.code}')
            return False
        
        # Use provided quantity or calculate from sale line
        if quantity is None:
            quantity = sale_line.product_uom_qty
        
        # Prepare MO values
        mo_vals = {
            'product_id': product.id,
            'product_qty': quantity,
            'product_uom_id': product.uom_id.id,
            'bom_id': bom.id,
            'date_planned_start': fields.Datetime.now(),
            'user_id': self.env.user.id,
            'company_id': sale_line.order_id.company_id.id,
            'origin': sale_line.order_id.name,
            'sale_line_id': sale_line.id,
            'production_sequence': sequence,
            'production_level' : series.level
        }


        
        # Add unit index to name if serial tracking
        if unit_index:
            mo_vals['name'] = f"MO-{sale_line.order_id.name}-L{series.level}-U{unit_index}-{sequence}"
        else:
            mo_vals['name'] = f"MO-{sale_line.order_id.name}-L{series.level}-{sequence}"
        
        # Create the MO
        print(mo_vals)
        mo = self.env['mrp.production'].sudo().create(mo_vals)
        
        # Link child MOs if this is a sub-assembly
        if series.parent_series_id and series.parent_series_id.id in created_mos:
            parent_mo = created_mos[series.parent_series_id.id]
            # You might want to add a custom field to link sub-MOs
            # For now, we'll use origin field to maintain relationship
            mo.origin = f"{mo.origin},{parent_mo.name}"
        
        return mo

    def _calculate_sub_assembly_qty(self, series, main_qty, created_mos):
        """Calculate required quantity for sub-assemblies based on BOM structure"""
        
        # Get the BOM that uses this sub-assembly
        parent_boms = self.env['mrp.bom.line'].search([
            ('product_id', '=', series.bom_id.product_id.id)
        ])
        
        if not parent_boms:
            return main_qty
        
        # Calculate based on BOM ratios
        total_qty = 0
        for bom_line in parent_boms:
            if bom_line.bom_id.product_id:
                # Check if this parent BOM is in our current production
                for created_mo in created_mos.values():
                    if created_mo.bom_id == bom_line.bom_id:
                        total_qty += bom_line.product_qty * created_mo.product_qty
        
        return total_qty or main_qty

    def _create_standard_mo_with_serial_split(self, sale_line):
        """Create standard MO with serial number split"""
        product = sale_line.product_id
        
        # Find BOM for the product
        bom = self.env['mrp.bom']._bom_find(products=product, bom_type='normal')[product]
        
        if not bom:
            print(f'---No BOM found for product {product.name}')
            return []
        
        # Check if serial tracking
        has_serial_tracking = product.tracking == 'serial'
        mo_count = int(sale_line.product_uom_qty) if has_serial_tracking else 1
        qty_per_mo = 1.0 if has_serial_tracking else sale_line.product_uom_qty
        
        created_mos = []
        
        for i in range(mo_count):
            mo_vals = {
                'product_id': product.id,
                'product_qty': qty_per_mo,
                'product_uom_id': product.uom_id.id,
                'bom_id': bom.id,
                'date_planned_start': fields.Datetime.now(),
                'user_id': self.env.user.id,
                'company_id': sale_line.order_id.company_id.id,
                'origin': sale_line.order_id.name,
                'sale_line_id': sale_line.id,
            }
            
            if has_serial_tracking:
                mo_vals['name'] = f"{sale_line.order_id.name}-U{i+1}"
            
            mo = self.env['mrp.production'].sudo().create(mo_vals)
            created_mos.append(mo)
        
        return created_mos

    def _create_standard_mo(self, sale_line):
        """Fallback method to create standard MO when no BOM series available"""
        product = sale_line.product_id
        
        # Get the main BOM for the product
        bom = self.env['mrp.bom']._bom_find(product=product)[product]
        
        if not bom:
            print(f'---No BOM found for {product.name}')
            return False
        
        mo_vals = {
            'product_id': product.id,
            'product_qty': sale_line.product_uom_qty,
            'product_uom_id': product.uom_id.id,
            'bom_id': bom.id,
            'origin': sale_line.order_id.name,
            'sale_line_id': sale_line.id,
        }
        
        mo = self.env['mrp.production'].create(mo_vals)
        print(f'---Created standard MO: {mo.name}')
        return [mo]

    def _get_components_by_level(self, bom, template_id):
        """Organize BOM components by template level"""
        components_by_level = {}
        
        # Map template lines to BOM lines
        for template_line in template_id.template_line_ids:
            if template_line.category == 'processed':
                # Find corresponding BOM line
                bom_lines = bom.bom_line_ids.filtered(
                    lambda l: l.product_id.name == template_line.name or 
                    l.product_id.default_code == template_line.code
                )
                
                for bom_line in bom_lines:
                    level = template_line.level
                    if level not in components_by_level:
                        components_by_level[level] = []
                    
                    components_by_level[level].append({
                        'template_line_id': template_line.id,
                        'template_line': template_line,
                        'bom_line': bom_line,
                        'product_id': bom_line.product_id,
                        'quantity': bom_line.product_qty,
                        'parent_dependencies': template_line.parent_line_ids
                    })
        
        return components_by_level
    
    def _create_mo_for_component(self, component_data, sale_line, created_mos):
        """Create MO for a specific component"""
        template_line = component_data['template_line']
        product = component_data['product_id']
        
        # Check if product has BOM
        if not product.bom_ids:
            return False
        
        # Calculate quantity needed
        qty_needed = sale_line.product_uom_qty * component_data['quantity']
        
        # Check parent dependencies
        parent_mos = []
        for parent_line in component_data['parent_dependencies']:
            if parent_line.id in created_mos:
                parent_mos.append(created_mos[parent_line.id])
        
        # Create MO
        mo_vals = {
            'product_id': product.id,
            'product_qty': qty_needed,
            'product_uom_id': product.uom_id.id,
            'bom_id': product.bom_ids[0].id,
            'origin': sale_line.order_id.name,
            'sale_order_id': sale_line.order_id.id,
            'sale_line_id': sale_line.id,
            'state': 'draft',
            'level': template_line.level,
            'template_line_id': template_line.id,
        }
        
        # Add parent dependencies
        if parent_mos:
            mo_vals['parent_mo_ids'] = [(6, 0, [mo.id for mo in parent_mos])]
        
        mo = self.env['mrp.production'].create(mo_vals)
        
        # Add operation details if specified
        if template_line.operation_name:
            mo.write({
                'operation_name': template_line.operation_name,
                'operation_type': template_line.operation_type,
                'time_cycle': self._calculate_time(template_line.time_formula, sale_line)
            })
        
        return mo
    
    def action_view_manufacturing_orders(self):
        """View all MOs for this SO ordered by production level descending"""
        self.ensure_one()
        
        # Get the base action
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.mrp_production_action")
        
        # Set domain to filter MOs for this SO
        action['domain'] = [('sale_order_id', '=', self.id)]
        
        # Set context without group_by, just default values
        action['context'] = {
            'default_sale_order_id': self.id,
            # Remove any default grouping
            'group_by': [],
            # Clear default filters
            'search_default_todo': 0,
            'search_default_confirmed': 0,
        }
        
        # Search and sort the records
        mos = self.env['mrp.production'].search(
            [('sale_order_id', '=', self.id)],
            order='production_level desc, production_sequence, id'
        )
        
        # If we have specific MOs, update domain to show them in order
        if mos:
            action['domain'] = [('id', 'in', mos.ids)]
        
        return action


    @api.depends('name')
    def _compute_rab_ids(self):
        for order in self:
            order.rab_ids = self.env['kokai.rab'].search([('so_number', '=', order.name)])
    
    @api.depends('rab_ids')
    def _compute_rab_count(self):
        for order in self:
            order.rab_count = len(order.rab_ids)
    
    def action_generate_rab(self):
        """Open wizard to generate RAB from Sale Order"""
        self.ensure_one()
        
        # Check if there are confirmed order lines
        confirmed_lines = self.order_line.filtered(lambda l: l.product_template_id)
        if not confirmed_lines:
            raise UserError(_('There are no confirmed product lines to generate RAB. Please confirm at least one product line.'))
        
        # Check if products have proper configuration
        for line in confirmed_lines:
            if not line.product_template_id:
                raise UserError(_('Product %s does not have a product template configured.') % line.product_id.name)
        
        return {
            'name': _('Generate RAB'),
            'type': 'ir.actions.act_window',
            'res_model': 'generate.rab.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'active_id': self.id,
                'active_model': 'sale.order',
            }
        }
    
    def action_view_rab(self):
        """View related RABs"""
        self.ensure_one()
        
        if self.rab_count == 0:
            raise UserError(_('No RAB found for this Sale Order.'))
        
        action = {
            'name': _('RABs'),
            'type': 'ir.actions.act_window',
            'res_model': 'kokai.rab',
            'context': {'default_so_number': self.name},
        }
        
        if self.rab_count == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.rab_ids[0].id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('so_number', '=', self.name)],
            })
        
        return action

    # def action_show_wizard_generate_product(self):
    #     return {
    #         'name': 'Create Product',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'product.template.wizard',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_name': self.name or '',
    #             'default_source_id': self.id,
    #             'default_source_model': self._name,
    #             # Tambahkan default values lain sesuai kebutuhan
    #         }
    #     }    

    # def action_save_and_close(self):
    #     """Save product and return to caller form"""
    #     self.ensure_one()
        
    #     active_model = self.env.context.get('active_model')
    #     active_id = self.env.context.get('active_id')
        
    #     if not active_model or not active_id:
    #         return {'type': 'ir.actions.act_window_close'}
        
    #     # Create product template
    #     fg_category = self.env['ir.config_parameter'].search([('key','=','default_category_finish_goods')])

    #     product_vals = {
    #         'name': self.suggested_name or self.name,
    #         'default_code': self.code,
    #         'detailed_type': 'product',
    #         'sale_ok': True,
    #         'purchase_ok': True,
    #         'categ_id' : fg_category.value
    #     }
        

    #     res = self.env['product.template'].search_count([('default_code','=',product_vals['default_code'])])
    #     if res > 0 :
    #         raise ValidationError('Product jadi ini sudah ada')

    #         product_template = self.env['product.template'].create(product_vals)
            
    #         # Create attribute selections
    #         for var in self.variant_ids:
    #             if var.attribute_id and var.value_id:
    #                 self.env['product.template.attribute.selection'].create({
    #                     'product_tmpl_id': product_template.id,
    #                     'attribute_id': var.attribute_id.id,
    #                     'value_id': var.value_id.id,
    #                     'name': var.value_id.name,
    #                     'code': var.value_id.code if hasattr(var.value_id, 'code') else '',
    #                 })
            
    #         raise UserError("Gunakan code product")

                
        # Update based on active model
        # if active_model == 'kokai.rab':
        #     # Direct update to RAB
        #     rab = self.env['kokai.rab'].browse(active_id)
        #     if rab.exists():
        #         rab.write({
        #             'finished_goods': product_template.id,
        #         })
                
        #         # Show success notification
        #         return {
        #             'type': 'ir.actions.client',
        #             'tag': 'reload',  # Reload current view to show updated data
        #         }
        
        # elif active_model == 'crm.lead':
        #     # From CRM Lead - should not happen in your flow
        #     # But handle it anyway
        #     lead = self.env['crm.lead'].browse(active_id)



        #     if lead.exists() and lead.rab_ids:
        #         # Update the latest RAB
        #         latest_rab = lead.rab_ids.sorted('create_date', reverse=True)[0]
        #         rabseq = self.env['ir.sequence'].next_by_code('kokai.rab') or _('New')

        #         latest_rab.write({
        #             'finished_goods': product_template.id,
        #             'name' : rabseq
        #         })
        
        return {'type': 'ir.actions.act_window_close'}


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    production_ids = fields.One2many(
        'mrp.production',
        'sale_line_id',
        string='Manufacturing Orders'
    )
    production_count = fields.Integer(
        string='MO Count',
        compute='_compute_production_count'
    )
    
    @api.depends('production_ids')
    def _compute_production_count(self):
        for line in self:
            line.production_count = len(line.production_ids)
    
    def action_view_productions(self):
        """View all manufacturing orders for this sale line"""
        self.ensure_one()
        
        return {
            'name': f'Manufacturing Orders - {self.product_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('sale_line_id', '=', self.id)],
            'context': {'group_by': 'production_level'}
        }