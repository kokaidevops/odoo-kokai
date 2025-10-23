from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)

class ProductCategoryTemplate(models.Model):
    _name = 'product.category.template'
    _description = 'Product Category Template (e.g. Ball Valve, Check Valve)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'sequence, name'
    
    # Basic Information
    name = fields.Char(
        string='Category Name',
        required=True,
        tracking=True,
        help='e.g. Ball Valve, Check Valve, Gate Valve'
    )
    
    code = fields.Char(
        string='Category Code',
        required=True,
        tracking=True,
        help='e.g. BV for Ball Valve, CV for Check Valve'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    description = fields.Text(
        string='Description',
        help='Detailed description of this product category'
    )
    
    # Template Structure
    template_line_ids = fields.One2many(
        'product.category.template.line',
        'template_id',
        string='Template Structure',
        copy=True
    )

    product_base_id = fields.Many2one(
        'product.template',
        domain=[('categ_id','=',87)],
        string='Default Product Category',
        help='Default Odoo product category for items created from this template'
    )


    line_count = fields.Integer(
        string='Components Count',
        compute='_compute_line_count',
        store=True
    )
    
    category_types = fields.Char(
        string='Component Types',
        compute='_compute_category_types',
        store=True
    )
    
    max_level = fields.Integer(
        string='Max Level',
        compute='_compute_max_level',
        store=True
    )
    
    @api.depends('template_line_ids')
    def _compute_line_count(self):
        for record in self:
            record.line_count = len(record.template_line_ids)
    
    @api.depends('template_line_ids.component_type')
    def _compute_category_types(self):
        for record in self:
            types = record.template_line_ids.mapped('component_type')
            record.category_types = ', '.join(list(set(types)))
    
    @api.depends('template_line_ids.level')
    def _compute_max_level(self):
        for record in self:
            levels = record.template_line_ids.mapped('level')
            record.max_level = max(levels) if levels else 0

    show_filters = fields.Boolean(
        string='Show Filters',
        default=False
    )
    
    filter_category = fields.Selection([
        ('all', 'All'),
        ('raw', 'Raw Materials'),
        ('processed', 'Processed/WIP')
    ], string='Filter Category', default='all')
    
    filter_component_type = fields.Selection([
        ('all', 'All'),
        ('body', 'Body'),
        ('trim', 'Trim'),
        ('fastener', 'Fasteners'),
        ('sealing', 'Sealing'),
        ('accessory', 'Accessories'),
        ('consumable', 'Consumables'),
        ('other', 'Other')
    ], string='Filter Component Type', default='all')
    
    filter_level = fields.Selection([
        ('all', 'All'),
        ('1', 'Level 1'),
        ('2', 'Level 2'),
        ('3', 'Level 3'),
        ('4', 'Level 4+')
    ], string='Filter Level', default='all')
    
    filtered_line_ids = fields.Many2many(
        'product.category.template.line',
        compute='_compute_filtered_lines',
        string='Filtered Lines'
    )
    
    def action_toggle_filters(self):
        """Toggle filter visibility"""
        self.show_filters = not self.show_filters
        return {'type': 'ir.actions.do_nothing'}
    
    def action_apply_filters(self):
        """Apply selected filters"""
        self._compute_filtered_lines()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Filters applied successfully',
                'type': 'success',
            }
        }

    # Tambahkan di model product.category.template
    def action_open_variant_wizard(self):
        """Open variant generation wizard"""
        return {
            'name': 'Generate Product Variants',
            'type': 'ir.actions.act_window',
            'res_model': 'product.variant.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_category_template_id': self.id,
            }
        }
    

# Debug button action
    def action_open_variant_wizard(self):
        """Open variant wizard with populated template lines"""
        self.ensure_one()
        
        # Validate
        if not self.template_line_ids:
            raise UserError(_("No template lines defined. Please add template lines first."))
        
        # Create wizard
        wizard = self.env['product.variant.wizard'].create({
            'category_template_id': self.id,
            'product_template_id': self.product_base_id.id if self.product_base_id else False,
            'variant_generation_type': 'all',
        })
        
        # Populate template lines
        self._populate_wizard_lines(wizard)
        
        # Populate attribute lines
        self._populate_wizard_attributes(wizard)
        
        # Commit to ensure data is saved
        self.env.cr.commit()
        
        # Return action to open wizard
        return {
            'name': _('Generate Product Variants - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.variant.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'active_model': self._name,
            }
        }
    
    def _populate_wizard_lines(self, wizard):
        """Populate wizard with template lines"""
        _logger.info(f"Populating wizard with {len(self.template_line_ids)} template lines")
        
        for line in self.template_line_ids:
            line_vals = {
                'wizard_id': wizard.id,
                'template_line_id': line.id,
                'name': line.name or '',
                'level': line.level or 0,
                'category': line.category or 'raw',
                'component_type': line.component_type or 'other',
                'selected': bool(line.material_attribute_ids),  # Auto-select if has attributes
            }
            
            # Add product if exists
            if line.product_id:
                line_vals['product_id'] = line.product_id.id
            
            # Add material attributes if exists
            if line.material_attribute_ids:
                line_vals['material_attribute_ids'] = [(6, 0, line.material_attribute_ids.ids)]
            
            wizard_line = self.env['product.variant.wizard.line'].create(line_vals)
            _logger.info(f"Created wizard line: {wizard_line.name} (ID: {wizard_line.id})")
    
    def _populate_wizard_attributes(self, wizard):
        """Populate wizard with product attributes"""
        if not wizard.product_template_id:
            return
            
        # Get all unique attributes from template lines
        all_attributes = self.env['product.attribute']
        for line in self.template_line_ids:
            if line.material_attribute_ids:
                all_attributes |= line.material_attribute_ids
        
        _logger.info(f"Found {len(all_attributes)} unique attributes")
        
        # Create attribute lines in wizard
        for attribute in all_attributes:
            # Check if attribute exists in product template
            product_attr_line = wizard.product_template_id.attribute_line_ids.filtered(
                lambda l: l.attribute_id == attribute
            )
            
            attr_vals = {
                'wizard_id': wizard.id,
                'attribute_id': attribute.id,
                'required': True,
            }
            
            if product_attr_line:
                attr_vals['attribute_line_id'] = product_attr_line.id
                # Pre-select all values
                attr_vals['value_ids'] = [(6, 0, product_attr_line.value_ids.ids)]
            
            self.env['product.variant.wizard.attribute'].create(attr_vals)

    def action_clear_filters(self):
        """Clear all filters"""
        self.filter_category = 'all'
        self.filter_component_type = 'all'
        self.filter_level = 'all'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Filters cleared',
                'type': 'info',
            }
        }
    
    @api.depends('template_line_ids', 'filter_category', 'filter_component_type', 'filter_level')
    def _compute_filtered_lines(self):
        """Compute filtered template lines based on selected filters"""
        for record in self:
            domain = [('template_id', '=', record.id)]
            
            # Apply category filter
            if record.filter_category and record.filter_category != 'all':
                domain.append(('category', '=', record.filter_category))
            
            # Apply component type filter
            if record.filter_component_type and record.filter_component_type != 'all':
                domain.append(('component_type', '=', record.filter_component_type))
            
            # Apply level filter
            if record.filter_level and record.filter_level != 'all':
                if record.filter_level == '4':
                    domain.append(('level', '>=', 4))
                else:
                    domain.append(('level', '=', int(record.filter_level)))
            
            # Get filtered lines
            filtered_lines = self.env['product.category.template.line'].search(domain)
            record.filtered_line_ids = [(6, 0, filtered_lines.ids)]


class ProductCategoryTemplateLine(models.Model):
    _name = 'product.category.template.line'
    _description = 'Product Category Template Line'
    _order = 'level, sequence, id'
    
    template_id = fields.Many2one(
        'product.category.template',
        string='Template',
        required=True,
        ondelete='cascade'
    )
    
    # Level and Sequence
    level = fields.Integer(
        string='Level',
        required=True,
        default=1,
        help='Manufacturing level. Level 1 is processed first.'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Sequence within the same level'
    )
    
    # Item Definition
    name = fields.Char(
        string='Name',
        required=True,
        help='Generic name for this component (e.g. Main Body, Side Body, Ball)'
    )
    
    
    product_id = fields.Many2one(
        string='Base',
        comodel_name='product.template',
        ondelete='restrict',
        domain=[('raw_type', '!=', False)]
    )
    
    
    code = fields.Char(
        string='Code',
        help='Internal code for this component'
    )
    
    category = fields.Selection([
        ('raw', 'Raw Material'),
        ('processed', 'Processed/WIP')
    ], string='Category', required=True, default='raw')
    
    # Component Type for categorization
    component_type = fields.Selection([
        ('body', 'Body'),
        ('trim', 'Trim'),
        ('fastener', 'Fasteners'),
        ('sealing', 'Sealing'),
        ('accessory', 'Accessories'),
        ('consumable', 'Consumables'),
        ('other', 'Other')
    ], string='Type', default='other')
    
    
    material_attribute_ids = fields.Many2many(
        'product.attribute',
        'product_category_template_line_attribute_rel',
        'template_line_id',
        'attribute_id',
        string='Material Specification Attributes',
        help='Select product attributes that will be used to determine material specifications for this component'
    )    
    
    # Material Selection Rules
    material_selection_rule = fields.Text(
        string='Material Selection Rule',
        help='Define rules for material selection based on specifications (e.g. "For pressure > 600LB use A105")'
    )
    
    # Base UoM
    uom_id = fields.Many2one(
        'uom.uom',
        string='Default UoM',
        required=True,
        default=lambda self: self.env.ref('uom.product_uom_unit')
    )
    
    # Quantity formula (can use specification variables)
    quantity_formula = fields.Char(
        string='Quantity Formula',
        default='1',
        help='Formula to calculate quantity. Can use specification codes (e.g. "2" for fixed, or "SIZE/2" for dynamic)'
    )
    
    # Operation details for processed items
    operation_name = fields.Char(
        string='Operation Name',
        help='Manufacturing operation name'
    )
    
    operation_type = fields.Selection([
        ('machining', 'Machining'),
        ('assembly', 'Assembly'),
        ('welding', 'Welding'),
        ('testing', 'Testing'),
        ('finishing', 'Finishing'),
        ('other', 'Other')
    ], string='Operation Type')
    
    time_formula = fields.Char(
        string='Time Formula (minutes)',
        help='Formula to calculate operation time. Can use specifications (e.g. "SIZE * 30")'
    )
    
    # Dependencies
    parent_line_id = fields.Many2one(
        'product.category.template.line',
        string='Depends On',
        domain="[('level', '>', level)]"
    )


    parent_line_ids = fields.Many2many(
        'product.category.template.line',
        'product_category_template_line_parent_rel',
        'child_id',
        'parent_id',
        string='Depends On',
        # domain="[('template_id', '=', template_id), ('level', '>', level)]",
        help='Select components that this line depends on'
    )
    
    # Optional: Add inverse relation to see dependencies
    child_line_ids = fields.Many2many(
        'product.category.template.line',
        'product_category_template_line_parent_rel',
        'parent_id',
        'child_id',
        string='Required By',
        help='Components that depend on this line'
    )
    
    @api.constrains('parent_line_ids', 'level')
    def _check_parent_level(self):
        """Ensure all parent lines have lower level"""
        for record in self:
            for parent in record.parent_line_ids:
                if parent.level <= record.level:
                    raise ValidationError(
                        _('Parent line "%s" must have a lower level than current line level %s.') 
                        % (parent.name, record.level)
                    )
                if parent.template_id != record.template_id:
                    raise ValidationError(
                        _('Parent line "%s" must belong to the same template.') 
                        % parent.name
                    )
    
    @api.constrains('parent_line_ids')
    def _check_circular_dependency(self):
        """Check for circular dependencies"""
        for record in self:
            if record in record.parent_line_ids:
                raise ValidationError(_('A line cannot depend on itself!'))
            # Check deeper circular dependencies
            self._check_circular_dependency_recursive(record, record.parent_line_ids)
    
    def _check_circular_dependency_recursive(self, original_record, parents):
        """Recursively check for circular dependencies"""
        for parent in parents:
            if original_record in parent.parent_line_ids:
                raise ValidationError(
                    _('Circular dependency detected! "%s" cannot depend on "%s" because it creates a circular reference.') 
                    % (original_record.name, parent.name)
                )
            if parent.parent_line_ids:
                self._check_circular_dependency_recursive(original_record, parent.parent_line_ids)    
    # Notes
    notes = fields.Text(
        string='Notes',
        help='Additional notes or specifications for this component'
    )
    
    @api.onchange('level', 'template_id')
    def _onchange_level_template(self):
        """Update domain when level or template changes"""
        if self.parent_line_id:
            if self.parent_line_id.level >= self.level:
                self.parent_line_id = False
            if self.parent_line_id.template_id != self.template_id:
                self.parent_line_id = False    
    