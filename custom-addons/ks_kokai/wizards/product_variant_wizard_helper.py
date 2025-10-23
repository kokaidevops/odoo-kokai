# models/product_variant_wizard_helpers.py

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import re
from ast import literal_eval

class ProductVariantWizardHelpers(models.TransientModel):
    _inherit = 'product.variant.wizard'
    
    def action_quick_select_all(self):
        """Quick action to select all template lines"""
        for line in self.template_line_ids:
            line.selected = True
        return {'type': 'ir.actions.do_nothing'}
    
    def action_quick_clear_all(self):
        """Quick action to clear all selections"""
        for line in self.template_line_ids:
            line.selected = False
        return {'type': 'ir.actions.do_nothing'}
    
    def action_quick_select_raw(self):
        """Quick action to select only raw materials"""
        for line in self.template_line_ids:
            line.selected = (line.category == 'raw')
        return {'type': 'ir.actions.do_nothing'}
    
    def action_quick_select_processed(self):
        """Quick action to select only processed items"""
        for line in self.template_line_ids:
            line.selected = (line.category == 'processed')
        return {'type': 'ir.actions.do_nothing'}
    
    def action_select_by_level(self, level):
        """Select components by manufacturing level"""
        for line in self.template_line_ids:
            if level == 'all':
                line.selected = True
            elif level == '4+':
                line.selected = (line.level >= 4)
            else:
                line.selected = (line.level == int(level))
        return {'type': 'ir.actions.do_nothing'}
    
    def action_select_by_component_type(self, component_type):
        """Select components by type"""
        for line in self.template_line_ids:
            if component_type == 'all':
                line.selected = True
            else:
                line.selected = (line.component_type == component_type)
        return {'type': 'ir.actions.do_nothing'}
    
    def _evaluate_formula(self, formula, variant, context_vals=None):
        """
        Safely evaluate formula with variant context
        
        :param formula: Formula string to evaluate
        :param variant: Product variant for context
        :param context_vals: Additional context values
        :return: Evaluated result
        """
        if not formula:
            return 1.0
        
        # Build evaluation context
        eval_context = {
            'variant': variant,
            'product': variant,
        }
        
        # Add attribute values to context
        for attr_val in variant.product_template_attribute_value_ids:
            attr_name = attr_val.attribute_id.name.upper().replace(' ', '_')
            # Try to get numeric value if possible
            try:
                value = float(attr_val.product_attribute_value_id.name)
                eval_context[attr_name] = value
            except (ValueError, TypeError):
                eval_context[attr_name] = attr_val.product_attribute_value_id.name
        
        # Add additional context values
        if context_vals:
            eval_context.update(context_vals)
        
        # Safe evaluation
        try:
            # Replace common patterns
            formula = formula.replace('SIZE', str(eval_context.get('SIZE', 1)))
            formula = formula.replace('PRESSURE', str(eval_context.get('PRESSURE', 1)))
            
            # Use literal_eval for safety (limited but secure)
            # For production, consider using safe_eval from odoo.tools
            result = eval(formula, {"__builtins__": {}}, eval_context)
            return float(result)
        except Exception as e:
            # Log error and return default
            _logger.warning(f"Failed to evaluate formula '{formula}': {str(e)}")
            return 1.0
    
    def _match_material_rule(self, rule, variant):
        """
        Check if material selection rule matches variant attributes
        
        :param rule: Rule string (e.g., "pressure > 600")
        :param variant: Product variant to check
        :return: Boolean indicating if rule matches
        """
        if not rule:
            return True
        
        # Build context for rule evaluation
        rule_context = {}
        
        for attr_val in variant.product_template_attribute_value_ids:
            attr_name = attr_val.attribute_id.name.lower().replace(' ', '_')
            val_name = attr_val.product_attribute_value_id.name
            
            # Try to extract numeric value
            numeric_match = re.search(r'(\d+)', val_name)
            if numeric_match:
                rule_context[attr_name] = float(numeric_match.group(1))
            else:
                rule_context[attr_name] = val_name.lower()
        
        # Evaluate rule
        try:
            # Simple rule parsing - for production use proper parser
            rule_lower = rule.lower()
            
            # Replace attribute references
            for key, value in rule_context.items():
                rule_lower = rule_lower.replace(key, str(value))
            
            # Safe evaluation
            return eval(rule_lower, {"__builtins__": {}}, rule_context)
        except:
            return False
    

    def clear_all_values(self):
        self.ensure_one()
        
        # Clear values using SQL for immediate effect
        for line in self.attribute_line_ids:
            line.value_ids = [(5,)]
        
        # Force save
        self.env.cr.commit()
        
        # Return reload action
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.variant.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
            'flags': {'mode': 'edit'},
        }
    def _get_component_product_advanced(self, template_line, variant):
        """
        Advanced component product selection based on material rules
        
        :param template_line: Category template line
        :param variant: Product variant being created
        :return: Product.product record or False
        """
        # Check if there's a material selection rule
        if template_line.material_selection_rule:
            if not self._match_material_rule(template_line.material_selection_rule, variant):
                return False
        
        # Base product
        base_product = template_line.product_id
        if not base_product:
            return False
        
        # If base product has variants, try to match attributes
        if len(base_product.product_variant_ids) > 1:
            # Get material attributes for this line
            material_attrs = template_line.material_attribute_ids
            
            if material_attrs:
                # Find best matching variant
                best_match = False
                best_score = 0
                
                for component_variant in base_product.product_variant_ids:
                    score = 0
                    
                    # Check each material attribute
                    for attr in material_attrs:
                        # Get value from main variant
                        main_value = variant.product_template_attribute_value_ids.filtered(
                            lambda v: v.attribute_id == attr
                        )
                        
                        if main_value:
                            # Check if component has same value
                            component_value = component_variant.product_template_attribute_value_ids.filtered(
                                lambda v: v.product_attribute_value_id == main_value.product_attribute_value_id
                            )
                            
                            if component_value:
                                score += 1
                    
                    if score > best_score:
                        best_score = score
                        best_match = component_variant
                
                return best_match
        
        # Return single variant or first variant
        return base_product.product_variant_ids[:1] if base_product.product_variant_ids else False
    
    def _create_structured_bom(self, variant, template_lines):
        """
        Create structured BOM with proper parent-child relationships
        
        :param variant: Product variant
        :param template_lines: Selected template lines
        :return: Created BOM record
        """
        # Create main BOM
        main_bom_vals = {
            'product_tmpl_id': variant.product_tmpl_id.id,
            'product_id': variant.id,
            'code': f"BOM-{variant.default_code or variant.id}",
            'type': 'normal',
        }
        main_bom = self.env['mrp.bom'].create(main_bom_vals)
        
        # Process lines by level
        processed_components = {}  # Track processed components by template_line_id
        
        # Sort lines by level (highest first for dependencies)
        sorted_lines = template_lines.sorted('level', reverse=True)
        
        for tmpl_line in sorted_lines:
            # Get component product
            component_product = self._get_component_product_advanced(tmpl_line, variant)
            
            if not component_product:
                continue
            
            # Calculate quantity
            quantity = self._evaluate_formula(tmpl_line.quantity_formula, variant)
            
            # Check if this is a sub-assembly (has parent dependencies)
            if tmpl_line.parent_line_ids and tmpl_line.category == 'processed':
                # Create sub-BOM for this component
                sub_bom_vals = {
                    'product_tmpl_id': component_product.product_tmpl_id.id,
                    'product_id': component_product.id,
                    'code': f"SUB-{component_product.default_code or component_product.id}",
                    'type': 'normal',
                }
                sub_bom = self.env['mrp.bom'].create(sub_bom_vals)
                
                # Add parent components to sub-BOM
                for parent_line in tmpl_line.parent_line_ids:
                    if parent_line.id in processed_components:
                        parent_product = processed_components[parent_line.id]['product']
                        parent_qty = self._evaluate_formula(
                            parent_line.quantity_formula, 
                            variant
                        )
                        
                        sub_bom_line_vals = {
                            'bom_id': sub_bom.id,
                            'product_id': parent_product.id,
                            'product_qty': parent_qty,
                            'product_uom_id': parent_line.uom_id.id,
                        }
                        self.env['mrp.bom.line'].create(sub_bom_line_vals)
                
                # Store processed component
                processed_components[tmpl_line.id] = {
                    'product': component_product,
                    'bom': sub_bom
                }
                
                # Add sub-assembly to main BOM
                main_bom_line_vals = {
                    'bom_id': main_bom.id,
                    'product_id': component_product.id,
                    'product_qty': quantity,
                    'product_uom_id': tmpl_line.uom_id.id,
                    'child_bom_id': sub_bom.id,
                }
            else:
                # Regular component - add directly to main BOM
                processed_components[tmpl_line.id] = {
                    'product': component_product,
                    'bom': None
                }
                
                main_bom_line_vals = {
                    'bom_id': main_bom.id,
                    'product_id': component_product.id,
                    'product_qty': quantity,
                    'product_uom_id': tmpl_line.uom_id.id,
                }
            
            # Create BOM line
            self.env['mrp.bom.line'].create(main_bom_line_vals)
        
        return main_bom
    
    def _create_variant_routing(self, variant, template_lines):
        """
        Create manufacturing routing with operations
        
        :param variant: Product variant
        :param template_lines: Selected template lines with operations
        :return: Created routing record
        """
        # Filter lines with operations
        operation_lines = template_lines.filtered(
            lambda l: l.operation_name and l.category == 'processed'
        ).sorted('level')
        
        if not operation_lines:
            return False
        
        # Create routing
        routing_vals = {
            'name': f"Routing - {variant.display_name}",
            'active': True,
            'code': f"RT-{variant.default_code or variant.id}",
        }
        routing = self.env['mrp.routing'].create(routing_vals)
        
        # Get or create workcenters by operation type
        workcenters = {}
        for op_type in ['machining', 'assembly', 'welding', 'testing', 'finishing', 'other']:
            wc = self.env['mrp.workcenter'].search([
                ('name', 'ilike', op_type)
            ], limit=1)
            
            if not wc:
                wc = self.env['mrp.workcenter'].create({
                    'name': op_type.capitalize() + ' Center',
                    'working_state': 'normal',
                    'capacity': 1.0,
                })
            
            workcenters[op_type] = wc
        
        # Add operations
        sequence = 10
        for line in operation_lines:
            # Get appropriate workcenter
            wc = workcenters.get(line.operation_type or 'other', workcenters['other'])
            
            # Calculate cycle time
            cycle_time = self._evaluate_formula(line.time_formula, variant)
            
            operation_vals = {
                'name': line.operation_name,
                'routing_id': routing.id,
                'workcenter_id': wc.id,
                'sequence': sequence,
                'time_cycle': cycle_time,
                'time_mode': 'manual',
                'time_mode_batch': 1,
                'note': line.notes or '',
            }
            
            self.env['mrp.routing.workcenter'].create(operation_vals)
            sequence += 10
        
        return routing
    
    def action_preview_bom_structure(self):
        """Preview BOM structure before generation"""
        self.ensure_one()
        
        if not self.template_line_ids:
            raise UserError(_("No template lines available for preview."))
        
        # Generate preview HTML
        preview_html = "<div style='font-family: monospace; padding: 10px;'>"
        preview_html += "<h3>BOM Structure Preview</h3>"
        
        # Group by level
        levels = {}
        for line in self.template_line_ids.filtered('selected'):
            level = line.level
            if level not in levels:
                levels[level] = []
            levels[level].append(line)
        
        # Display by level
        for level in sorted(levels.keys(), reverse=True):
            preview_html += f"<h4>Level {level}</h4><ul>"
            
            for line in levels[level]:
                style = 'color: green;' if line.category == 'raw' else 'color: blue;'
                preview_html += f"<li style='{style}'>"
                preview_html += f"<b>{line.name}</b> ({line.component_type})"
                
                if line.parent_lines_display:
                    preview_html += f" - Depends on: {line.parent_lines_display}"
                
                if line.product_id:
                    preview_html += f" - Product: {line.product_id.display_name}"
                
                preview_html += "</li>"
            
            preview_html += "</ul>"
        
        preview_html += "</div>"
        
        # Create wizard to show preview
        return {
            'type': 'ir.actions.act_window',
            'name': 'BOM Structure Preview',
            'res_model': 'product.variant.wizard.preview',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_preview_html': preview_html,
                'default_wizard_id': self.id,
            }
        }


class ProductVariantWizardPreview(models.TransientModel):
    _name = 'product.variant.wizard.preview'
    _description = 'Product Variant Wizard BOM Preview'
    
    wizard_id = fields.Many2one(
        'product.variant.wizard',
        string='Parent Wizard'
    )
    
    preview_html = fields.Html(
        string='Preview',
        readonly=True
    )
    
    def action_confirm(self):
        """Return to main wizard"""
        return {'type': 'ir.actions.act_window_close'}