from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, groupby
import logging


_logger = logging.getLogger(__name__)

class ks_ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'
    

    PROTECTED_CATEGORY_NAMES = 'Test / Base / Finished Goods'
    
    # Computed field untuk check apakah category locked
    is_category_locked = fields.Boolean(
        string='Category Locked',
        compute='_compute_is_category_locked',
        store=False,
        help='Category is locked for non-admin users'
    )

    track_weight_by_serial = fields.Boolean(
        string='Track Weight by Serial',
        help='Track weight for each serial number'
    )
    
    standard_weight_per_unit = fields.Float(
        string='Standard Weight per Unit (kg)',
        digits='Product Unit of Measure',
        help='Standard weight for valuation calculation'
    )
    
    weight_tolerance = fields.Float(
        string='Weight Tolerance (%)',
        default=5.0,
        help='Acceptable weight variance percentage'
    )
    
    valuation_by_actual_weight = fields.Boolean(
        string='Valuation by Actual Weight',
        help='Calculate valuation based on actual weight instead of quantity'
    )
    
    
    raw_type = fields.Selection(
        string='Type Material',
        selection=[('fg', 'Finished Goods'), ('wip', 'WIP'),('rm','Raw Material')]
    )
    
    base_code = fields.Char(
        string='RM Code',
        help='Base code for Raw Material (e.g., SHIRT, SHOE)'
    )    
    
    base_product_id = fields.Many2one(
        string='Base Product',
        comodel_name='product.template',
        domain =[('categ_id','=',87)],
        ondelete='restrict',
    )
    

    @api.depends('categ_id')
    def _compute_is_category_locked(self):
        """Check if current category is protected"""
        is_admin = self.env.user.has_group('base.group_system')
        
        for record in self:
            # Category is locked if:
            # 1. User is not admin AND
            # 2. Current category is in protected list
            if not is_admin and record.categ_id:
                # Check category name (case insensitive)
                category_name = record.categ_id.name
                if record.categ_id.complete_name == self.PROTECTED_CATEGORY_NAMES:
                    record.is_category_locked = True
            else:
                record.is_category_locked = False


    @api.model
    def create(self, vals):
        template = super().create(vals)
        # Auto generate codes after creation
        # if template.base_code and template.product_variant_ids:
        #     template.generate_variant_codes()
        return template    
    

    def button_bom_cost(self):
        templates = self.filtered(lambda t: t.product_variant_count == 1 and t.bom_count > 0)
        if templates:
            return templates.mapped('product_variant_id').button_bom_cost()


    auto_generate_bom = fields.Boolean(
        string='Auto Generate BOM',
        help='Automatically generate BOMs for product variants'
    )
    
    bom_component_ids = fields.One2many(
        'product.bom.component',
        'product_tmpl_id',
        string='BOM Components Configuration'
    )
    
    attribute_selection_ids = fields.One2many(
        'product.template.attribute.selection',
        'product_tmpl_id',
        string='Saved Attribute Combinations'
    )
    attribute_selection_count = fields.Integer(
        string='# Combinations',
        compute='_compute_attribute_selection_count'
    )
    
    category_template_id = fields.Many2one(
        'product.category.template',
        string='Category Template',
        help='Template used to create this product'
    )

    def action_generate_bom_from_template(self):
        """Generate BOM based on category template and product specifications"""
        self.ensure_one()
        
        if not self.category_template_id:
            raise UserError(_('Please select a Category Template first.'))
        
        # Get product specifications (attribute values)
        specifications = self._get_product_specifications()
        print('-----spec')
        print(specifications)
        
        # Generate BOM structure
        bom = self._generate_bom_structure(specifications)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom',
            'res_id': bom.id,
            'view_mode': 'form',
            'target': 'current',
        }
 
 
    def _get_product_specifications(self):
        """Get product attribute values as specifications"""
        specifications = {}
        
        # Always try to get from attribute_selection_ids first
        print('--att')
        print(self.attribute_selection_ids)
        
        if self.attribute_selection_ids:
            for line in self.attribute_selection_ids:
                attr_name = line.attribute_id.name.upper().replace(' ', '_')
                # Get selected values - adjust field name based on actual model
                selected_values = line.selected_value_ids if hasattr(line, 'selected_value_ids') else line.value_id
                if selected_values:
                    if hasattr(line, 'selected_value_ids'):  # Multiple values
                        specifications[attr_name] = {
                            'attribute_id': line.attribute_id.id,
                            'attribute_name': line.attribute_id.name,
                            'values': selected_values.mapped('name'),
                            'value_ids': selected_values.ids
                        }
                    else:  # Single value
                        specifications[attr_name] = {
                            'attribute_id': line.attribute_id.id,
                            'attribute_name': line.attribute_id.name,
                            'value': selected_values.name,
                            'value_id': selected_values.id
                        }
        
        # Only use product variant as fallback if no attribute_selection_ids found
        elif self.product_variant_id and self.product_variant_id.product_template_attribute_value_ids:
            print('--fallback to product variant')
            for pav in self.product_variant_id.product_template_attribute_value_ids:
                attr_name = pav.attribute_id.name.upper().replace(' ', '_')
                specifications[attr_name] = {
                    'attribute_id': pav.attribute_id.id,
                    'attribute_name': pav.attribute_id.name,
                    'value': pav.name,
                    'value_id': pav.product_attribute_value_id.id
                }
        
        print(f'--specifications: {specifications}')
        return specifications 
 


    def _generate_bom_structure(self, specifications):
        """Generate complete BOM structure based on template"""
        # Check if BOM already exists
        print(specifications)
        
        existing_bom = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.id),
            ('active', '=', True)
        ], limit=1)
        
        if existing_bom:
            raise UserError(_('BOM already exists for this product. Please archive it first.'))
        
        # Create main BOM for finished goods
        bom_vals = {
            'product_tmpl_id': self.id,
            'product_id' : self.product_variant_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'code': self.default_code or self.name,
        }
        main_bom = self.env['mrp.bom'].create(bom_vals)
        
        # Get template lines
        template_lines = self.category_template_id.template_line_ids
        print('---temp_line')
        print(template_lines)        
        # Store created components by template line
        created_components = {}
        
        # First, create all components (all levels)
        for template_line in template_lines:
            component_product = self._create_or_get_component(
                template_line, 
                specifications, 
                created_components
            )
            
            if component_product:
                created_components[template_line.id] = {
                    'product': component_product,
                    'template_line': template_line,
                }
        
        # Add ONLY LEVEL 1 components to main BOM
        level_1_lines = template_lines.filtered(lambda l: l.level == 1)
        
        for template_line in level_1_lines:
            if template_line.id in created_components:
                component_product = created_components[template_line.id]['product']
                
                # Calculate quantity based on formula
                quantity = self._evaluate_quantity_formula(
                    template_line.quantity_formula,
                    specifications
                )
                
                # Create BOM line for main product
                bom_line_vals = {
                    'bom_id': main_bom.id,
                    'product_id': component_product.id,
                    'product_qty': quantity,
                    'product_uom_id': template_line.uom_id.id,
                    'sequence': template_line.sequence,
                }
                
                self.env['mrp.bom.line'].create(bom_line_vals)
        
        # Create sub-BOMs for processed components (level 1 and higher)
        # self._create_sub_boms_hierarchical(created_components, specifications)
        
        return main_bom    


    def _generate_bom_structure_above1(self, specifications):
        """Generate complete BOM structure for all product variants based on template"""
        _logger.info(f"=== BOM Generation Start ===")
        _logger.info(f"Product Template: {self.name}")
        _logger.info(f"Specifications: {specifications}")
        
        if not self.category_template_id:
            raise UserError(_('No category template found for this product.'))
        
        # Get all product variants for this template
        variants = self.product_variant_ids
        if not variants:
            raise UserError(_('No product variants found. Please create variants first.'))
        
        _logger.info(f"Creating BOMs for {len(variants)} variants")
        
        created_boms = self.env['mrp.bom']  # Initialize as empty recordset
        
        # Create BOM for each variant
        for variant in variants:
            _logger.info(f"Processing variant: {variant.display_name}")
            
            # Check if BOM already exists for this variant
            existing_bom = self.env['mrp.bom'].search([
                ('product_id', '=', variant.id),
                ('product_tmpl_id', '=', self.id),
                ('active', '=', True)
            ], limit=1)
            
            if existing_bom:
                _logger.info(f"BOM already exists for variant {variant.display_name}, skipping")
                created_boms |= existing_bom  # Add to recordset
                continue
            
            # Create main BOM for this variant
            main_bom = self._create_main_bom_for_variant(variant, specifications)
            if main_bom:
                created_boms |= main_bom  # Add to recordset instead of list
                
                # Create hierarchical sub-BOMs
                sub_boms = self._create_hierarchical_sub_boms(variant, specifications, main_bom)
                if sub_boms:
                    created_boms |= sub_boms
        
        _logger.info(f"=== BOM Generation Complete: {len(created_boms)} BOMs created ===")
        
        # Return single BOM if only one created, otherwise return recordset
        if len(created_boms) == 1:
            return created_boms  # This will be a single record that has .id
        return created_boms  # This will be a recordset

    def _create_main_bom_for_variant(self, variant, specifications):
        """Create main BOM for a specific product variant"""
        try:
            # Create main BOM
            bom_vals = {
                'product_tmpl_id': self.id,
                'product_id': variant.id,
                'product_qty': 1.0,
                'type': 'normal',
                'code': variant.default_code or variant.name,
                'active': True,
            }
            
            main_bom = self.env['mrp.bom'].create(bom_vals)
            _logger.info(f"Created main BOM {main_bom.id} for variant {variant.display_name}")
            
            # Get template lines and create components
            template_lines = self.category_template_id.template_line_ids
            created_components = {}
            
            # Create all component products first
            for template_line in template_lines:
                component_product = self._create_or_get_component(
                    template_line, 
                    specifications, 
                    created_components,
                    variant
                )
                
                if component_product:
                    created_components[template_line.id] = {
                        'product': component_product,
                        'template_line': template_line,
                    }
            
            # Add Level 1+ components to main BOM
            level_above1_lines = template_lines.filtered(lambda l: l.level > 1).sorted('sequence')
            
            for template_line in level_above1_lines:
                if template_line.id in created_components:
                    component_product = created_components[template_line.id]['product']
                    
                    # Calculate quantity
                    quantity = self._evaluate_quantity_formula(
                        template_line.quantity_formula or '1',
                        specifications,
                        variant
                    )
                    
                    # Create BOM line
                    bom_line_vals = {
                        'bom_id': main_bom.id,
                        'product_id': component_product.id,
                        'product_qty': quantity,
                        'product_uom_id': template_line.uom_id.id if template_line.uom_id else component_product.uom_id.id,
                        'sequence': template_line.sequence or 10,
                    }
                    
                    bom_line = self.env['mrp.bom.line'].create(bom_line_vals)
                    _logger.info(f"Added component {component_product.name} (qty: {quantity}) to main BOM")
            
            return main_bom
            
        except Exception as e:
            _logger.error(f"Error creating main BOM for variant {variant.display_name}: {str(e)}")
            raise UserError(_(f'Failed to create BOM for variant {variant.display_name}: {str(e)}'))

    def _create_hierarchical_sub_boms(self, variant, specifications, main_bom):
        """Create hierarchical sub-BOMs for processed components"""
        template_lines = self.category_template_id.template_line_ids
        
        # Get all processed components that need their own BOMs
        processed_lines = template_lines.filtered(
            lambda l: l.category == 'processed' and l.level > 0
        ).sorted('level', reverse=True)  # Start from highest level
        
        created_sub_boms = self.env['mrp.bom']  # Initialize as empty recordset
        
        for template_line in processed_lines:
            try:
                # Find the component product for this template line
                component_product = self._find_component_product(template_line, specifications, variant)
                
                if not component_product:
                    _logger.warning(f"No component product found for template line {template_line.name}")
                    continue
                
                # Check if sub-BOM already exists
                existing_sub_bom = self.env['mrp.bom'].search([
                    ('product_id', '=', component_product.id),
                    ('active', '=', True)
                ], limit=1)
                
                if existing_sub_bom:
                    created_sub_boms |= existing_sub_bom
                    continue
                
                # Create sub-BOM for this processed component
                sub_bom_vals = {
                    'product_tmpl_id': component_product.product_tmpl_id.id,
                    'product_id': component_product.id,
                    'product_qty': 1.0,
                    'type': 'normal',
                    'code': f"SUB-{component_product.default_code or component_product.name}",
                    'active': True,
                }
                
                sub_bom = self.env['mrp.bom'].create(sub_bom_vals)
                created_sub_boms |= sub_bom
                
                _logger.info(f"Created sub-BOM {sub_bom.id} for component {component_product.name}")
                
                # Add components to this sub-BOM (components with lower level)
                self._add_components_to_sub_bom(
                    sub_bom, 
                    template_line, 
                    template_lines, 
                    specifications, 
                    variant
                )
                
            except Exception as e:
                _logger.error(f"Error creating sub-BOM for template line {template_line.name}: {str(e)}")
                continue
        
        return created_sub_boms

    def _add_components_to_sub_bom(self, sub_bom, parent_template_line, all_template_lines, specifications, variant):
        """Add components to a sub-BOM based on template hierarchy"""
        
        # Find child components (components that this processed item consumes)
        child_lines = all_template_lines.filtered(
            lambda l: l.level < parent_template_line.level and 
                    l.id in parent_template_line.child_line_ids.ids
        ) if hasattr(parent_template_line, 'child_line_ids') else []
        
        # If no explicit children defined, use all components of lower level
        if not child_lines:
            child_lines = all_template_lines.filtered(
                lambda l: l.level < parent_template_line.level
            )
        
        for child_line in child_lines.sorted('sequence'):
            try:
                child_product = self._find_component_product(child_line, specifications, variant)
                
                if child_product:
                    # Calculate quantity for this component
                    quantity = self._evaluate_quantity_formula(
                        child_line.quantity_formula or '1',
                        specifications,
                        variant
                    )
                    
                    # Create BOM line in sub-BOM
                    sub_bom_line_vals = {
                        'bom_id': sub_bom.id,
                        'product_id': child_product.id,
                        'product_qty': quantity,
                        'product_uom_id': child_line.uom_id.id if child_line.uom_id else child_product.uom_id.id,
                        'sequence': child_line.sequence or 10,
                    }
                    
                    self.env['mrp.bom.line'].create(sub_bom_line_vals)
                    _logger.info(f"Added {child_product.name} (qty: {quantity}) to sub-BOM {sub_bom.code}")
                    
            except Exception as e:
                _logger.error(f"Error adding component {child_line.name} to sub-BOM: {str(e)}")
                continue

    def _find_component_product(self, template_line, specifications, variant):
        """Find or create component product based on template line and specifications"""
        
        if template_line.product_id:
            base_product = template_line.product_id
            
            # If base product has variants, find matching one
            if base_product.product_variant_count > 1:
                # Match based on specifications/attributes
                matching_variant = self._find_matching_variant(
                    base_product, 
                    template_line, 
                    specifications, 
                    variant
                )
                return matching_variant
            else:
                # Return single variant
                return base_product.product_variant_ids[:1] if base_product.product_variant_ids else None
        
        return None

    def _find_matching_variant(self, base_product, template_line, specifications, main_variant):
        """Find product variant that matches the specifications"""
        
        if not template_line.material_attribute_ids:
            # No specific material requirements, return first variant
            return base_product.product_variant_ids[:1] if base_product.product_variant_ids else None
        
        # Get main product's attribute values for matching
        main_variant_attrs = main_variant.product_template_attribute_value_ids.mapped('product_attribute_value_id')
        
        # Find component variant with matching material attributes
        for component_variant in base_product.product_variant_ids:
            component_attrs = component_variant.product_template_attribute_value_ids.mapped('product_attribute_value_id')
            
            # Check if this variant matches required material attributes
            matches = True
            for required_attr in template_line.material_attribute_ids:
                # Find corresponding attribute value from main variant
                main_attr_value = main_variant_attrs.filtered(lambda v: v.attribute_id == required_attr)
                component_attr_value = component_attrs.filtered(lambda v: v.attribute_id == required_attr)
                
                if main_attr_value and component_attr_value:
                    if main_attr_value != component_attr_value:
                        matches = False
                        break
                elif main_attr_value and not component_attr_value:
                    matches = False
                    break
            
            if matches:
                return component_variant
        
        # Return first variant if no exact match found
        return base_product.product_variant_ids[:1] if base_product.product_variant_ids else None

    def _evaluate_quantity_formula(self, formula, specifications, variant=None):
        """Safely evaluate quantity formula with specifications"""
        if not formula or formula.strip() == '':
            return 1.0
        
        try:
            # Create safe evaluation context
            safe_dict = {
                '__builtins__': {},
                'abs': abs,
                'min': min,
                'max': max,
                'round': round,
                'float': float,
                'int': int,
            }
            
            # Add specifications to context
            if isinstance(specifications, dict):
                safe_dict.update(specifications)
            
            # Add variant attributes to context if available
            if variant:
                for attr_val in variant.product_template_attribute_value_ids:
                    attr_name = attr_val.attribute_id.name.replace(' ', '_').lower()
                    value_name = attr_val.product_attribute_value_id.name
                    safe_dict[attr_name] = value_name
            
            # Evaluate formula
            result = eval(formula, safe_dict)
            return float(result) if result else 1.0
            
        except Exception as e:
            _logger.warning(f"Failed to evaluate formula '{formula}': {str(e)}")
            return 1.0

    def _create_or_get_component(self, template_line, specifications, created_components, variant=None):
        """Create or get component product for template line"""
        
        # Check if already created
        if template_line.id in created_components:
            return created_components[template_line.id]['product']
        
        # Find existing component product
        component_product = self._find_component_product(template_line, specifications, variant)
        
        if not component_product and template_line.product_id:
            # Create new variant if needed
            component_product = self._create_component_variant(template_line, specifications, variant)
        
        return component_product

    def _create_component_variant(self, template_line, specifications, variant):
        """Create new component variant if it doesn't exist"""
        
        base_product = template_line.product_id
        if not base_product:
            return None
        
        try:
            # If base product has no variants, create the first one
            if not base_product.product_variant_ids:
                base_product._create_variant_ids()
            
            # For now, return the first available variant
            # In a more sophisticated implementation, you would create
            # variants with specific attribute combinations
            return base_product.product_variant_ids[:1] if base_product.product_variant_ids else None
            
        except Exception as e:
            _logger.error(f"Error creating component variant for {base_product.name}: {str(e)}")
            return None

    def action_generate_bom_above_1(self):
        """Generate BOM based on category template and product specifications"""
        self.ensure_one()
        
        if not self.category_template_id:
            raise UserError(_('Please select a Category Template first.'))
        
        # Get product specifications (attribute values)
        specifications = self._get_product_specifications()
        print('-----spec')
        print(specifications)
        
        # Generate BOM structure
        bom = self._generate_bom_structure_above1(specifications)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom',
            'res_id': bom.id,
            'view_mode': 'form',
            'target': 'current',
        }
         


    def _calculate_variant_match_score(self, variant_attrs, spec_attrs, template_line):
        """Calculate how well a variant matches the specifications"""
        if not spec_attrs:
            return 0
        
        score = 0
        total_possible = len(spec_attrs)
        
        print(f'---calculating score: variant_attrs={variant_attrs}, spec_attrs={spec_attrs}')
        
        for attr_id, spec_value_id in spec_attrs.items():
            if attr_id in variant_attrs:
                if variant_attrs[attr_id] == spec_value_id:
                    score += 1
                    print(f'---attribute {attr_id}: MATCH (variant={variant_attrs[attr_id]}, spec={spec_value_id})')
                else:
                    print(f'---attribute {attr_id}: NO MATCH (variant={variant_attrs[attr_id]}, spec={spec_value_id})')
            else:
                print(f'---attribute {attr_id}: NOT FOUND in variant')
        
        print(f'---final score: {score}/{total_possible}')
        return score

    def _variant_matches_specifications(self, variant_attrs, spec_attrs, template_line):
        """Check if variant attributes match the specifications (legacy method)"""
        print(f'---legacy match check: variant_attrs={variant_attrs}, spec_attrs={spec_attrs}')
        
        if not spec_attrs:
            print('---no spec_attrs, returning True')
            return True
        
        # If template line has specific attributes to match, use those
        if hasattr(template_line, 'material_attribute_ids') and template_line.material_attribute_ids:
            relevant_attr_ids = template_line.material_attribute_ids.ids
            print(f'---using material_attribute_ids: {relevant_attr_ids}')
        else:
            # Otherwise, match all common attributes
            relevant_attr_ids = list(set(variant_attrs.keys()) & set(spec_attrs.keys()))
            print(f'---using common attributes: {relevant_attr_ids}')
        
        # Check if all relevant attributes match
        for attr_id in relevant_attr_ids:
            if attr_id in spec_attrs and attr_id in variant_attrs:
                if variant_attrs[attr_id] != spec_attrs[attr_id]:
                    print(f'---mismatch at attribute {attr_id}: {variant_attrs[attr_id]} != {spec_attrs[attr_id]}')
                    return False
                else:
                    print(f'---match at attribute {attr_id}: {variant_attrs[attr_id]} == {spec_attrs[attr_id]}')
        
        print('---all attributes match, returning True')
        return True



    def _get_processed_variant(self, template_line, specifications):
        """Get the appropriate processed product variant based on specifications"""
        product_template = template_line.product_id
        
        # If no variants available, return the template's default variant
        if not product_template.product_variant_ids:
            print('---no variants available, returning default')
            return product_template.product_variant_id
        
        print(f'---looking for processed variant from {len(product_template.product_variant_ids)} variants')
        print(f'---template_line: {template_line.name}')
        print(f'---product_template: {product_template.name}')
        print(f'---specifications received: {specifications}')
        
        # Convert specifications to attribute mapping for comparison
        spec_attrs = {}
        for spec_key, spec_data in specifications.items():
            print(f'---processing spec: {spec_key} = {spec_data}')
            if isinstance(spec_data, dict) and 'attribute_id' in spec_data:
                attr_id = spec_data['attribute_id']
                if 'value_id' in spec_data:  # Single value
                    spec_attrs[attr_id] = spec_data['value_id']
                    print(f'---added single value: attr_id {attr_id} = value_id {spec_data["value_id"]}')
                elif 'value_ids' in spec_data and spec_data['value_ids']:  # Multiple values, take first
                    spec_attrs[attr_id] = spec_data['value_ids'][0]
                    print(f'---added first of multiple values: attr_id {attr_id} = value_id {spec_data["value_ids"][0]}')
        
        print('---masuk_spec')
        print(f'---spec_attrs: {spec_attrs}')
        
        # Find matching variant
        best_match = None
        best_match_score = -1
        
        for variant in product_template.product_variant_ids:
            variant_attrs = {}
            for ptav in variant.product_template_attribute_value_ids:
                attr_id = ptav.attribute_id.id
                value_id = ptav.product_attribute_value_id.id
                variant_attrs[attr_id] = value_id
            
            print(f'---checking variant {variant.name} (ID: {variant.id}): {variant_attrs}')
            
            # Calculate match score
            match_score = self._calculate_variant_match_score(variant_attrs, spec_attrs, template_line)
            print(f'---match score for {variant.name}: {match_score}')
            
            if match_score > best_match_score:
                best_match = variant
                best_match_score = match_score
                print(f'---new best match: {variant.name} with score {match_score}')
            
            # If perfect match (all attributes match), return immediately
            if match_score == len(spec_attrs) and len(spec_attrs) > 0:
                print(f'---perfect match found: {variant.name}')
                return variant
        
        if best_match:
            print(f'---returning best match: {best_match.name} with score {best_match_score}')
            return best_match
        
        # If no match found, return the first variant as fallback
        print('---no match found, returning first variant')
        return product_template.product_variant_ids[0]


    def _variant_matches_specifications(self, variant_attrs, spec_attrs, template_line):
        """Check if variant attributes match the specifications"""
        # If template line has specific attributes to match, use those
        if hasattr(template_line, 'material_attribute_ids') and template_line.material_attribute_ids:
            relevant_attr_ids = template_line.material_attribute_ids.ids
        else:
            # Otherwise, match all common attributes
            relevant_attr_ids = set(variant_attrs.keys()) & set(spec_attrs.keys())
        
        # Check if all relevant attributes match
        for attr_id in relevant_attr_ids:
            if attr_id in spec_attrs and attr_id in variant_attrs:
                if variant_attrs[attr_id] != spec_attrs[attr_id]:
                    return False
        
        return True


    def _create_or_get_component(self, template_line, specifications, created_components):
        """Create or get component product based on template line and specifications"""
        
        # Determine product name based on specifications
        product_name = self._generate_component_name(template_line, specifications)
        print('---prod__name')
        print(product_name)
        # For raw materials, try to find existing product
        if template_line.category == 'raw':
            # Check if base product is defined
            print('---temp_line2')
            if template_line.product_id:
                # Check if we need variant based on material attributes
                if template_line.material_attribute_ids:
                    return self._get_material_variant(template_line, specifications)
                else:
                    return template_line.product_id.product_variant_id
            else:
                # Search for existing product by name/code
                domain = [('name', '=', product_name)]
                if template_line.code:
                    domain = ['|', ('default_code', '=', template_line.code)] + domain
                
                existing = self.env['product.product'].search(domain, limit=1)
                if existing:
                    return existing
        elif template_line.category == 'processed':
            print('---processed category')
            if template_line.product_id:
                return self._get_processed_variant(template_line, specifications)
            else:
                # Search for existing processed product by name/code
                domain = [('name', '=', product_name)]
                if template_line.code:
                    domain = ['|', ('default_code', '=', template_line.code)] + domain
                
                existing = self.env['product.product'].search(domain, limit=1)
                if existing:
                    return existing        
        # For processed items or if raw material not found, create new
        # product_vals = {
        #     'name': product_name,
        #     'type': 'product' if template_line.category == 'raw' else 'product',
        #     'categ_id': self.categ_id.id,
        #     'default_code': self._generate_component_code(template_line, specifications),
        #     'route_ids': [(6, 0, [self.env.ref('mrp.route_warehouse0_manufacture').id])] if template_line.category == 'processed' else [],
        #     'purchase_ok': template_line.category == 'raw',
        #     'sale_ok': False,  # Components are not for sale
        #     'tracking': 'serial' if template_line.component_type in ['body', 'trim'] else 'none',
        # }
        
        # return self.env['product.product'].create(product_vals)
    
    def _get_material_variant(self, template_line, specifications):
        """Get specific material variant based on specifications"""
        base_product = template_line.product_id
        
        # Build domain for attribute values based on material selection rule
        domain = [('product_tmpl_id', '=', base_product.id)]
        
        # Parse material selection rule
        if template_line.material_selection_rule:
            # Example rule: "For PRESSURE > 600LB use MATERIAL = A105"
            # This is simplified - in real implementation, use a proper rule parser
            
            for attr in template_line.material_attribute_ids:
                attr_name = attr.name.upper().replace(' ', '_')
                if attr_name in specifications:
                    spec_value = specifications[attr_name].get('value') or specifications[attr_name].get('values', [''])[0]
                    
                    # Find matching attribute value
                    attr_value = self.env['product.attribute.value'].search([
                        ('attribute_id', '=', attr.id),
                        ('name', '=', spec_value)
                    ], limit=1)
                    
                    if attr_value:
                        domain.append(('product_template_attribute_value_ids.product_attribute_value_id', '=', attr_value.id))
        
        variant = self.env['product.product'].search(domain, limit=1)
        if variant:
            return variant
        
        # If no variant found, return base product's first variant
        return base_product.product_variant_id
    
    def _generate_component_name(self, template_line, specifications):
        """Generate component name based on template and specifications"""
        name_parts = [template_line.name]
        
        # Add specification values to name
        if template_line.category == 'processed':
            # Add main specifications to processed item names
            for spec_key in ['SIZE', 'PRESSURE', 'TYPE']:
                if spec_key in specifications:
                    value = specifications[spec_key].get('value') or specifications[spec_key].get('values', [''])[0]
                    name_parts.append(value)
        
        return ' '.join(name_parts)
    
    def _generate_component_code(self, template_line, specifications):
        """Generate component code based on template and specifications"""
        code_parts = []
        
        # Add template code
        if self.category_template_id.code:
            code_parts.append(self.category_template_id.code)
        
        # Add component code
        if template_line.code:
            code_parts.append(template_line.code)
        
        # Add specification codes (simplified)
        for spec_key in ['SIZE', 'PRESSURE']:
            if spec_key in specifications:
                value = specifications[spec_key].get('value') or specifications[spec_key].get('values', [''])[0]
                # Extract numeric or short code
                code_value = ''.join(filter(str.isalnum, value))[:4]
                code_parts.append(code_value)
        
        return '-'.join(code_parts)
    
    def _evaluate_quantity_formula(self, formula, specifications):
        """Evaluate quantity formula with specifications context"""
        if not formula:
            return 1.0
        
        # Create safe context for evaluation
        safe_context = {
            '__builtins__': {},
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
        }
        
        # Add specification values to context
        for spec_key, spec_data in specifications.items():
            # Try to extract numeric value
            value = spec_data.get('value') or spec_data.get('values', [''])[0]
            try:
                # Extract numeric part (e.g., "2 inch" -> 2)
                numeric_value = float(''.join(filter(lambda x: x.isdigit() or x == '.', str(value))))
                safe_context[spec_key] = numeric_value
            except:
                safe_context[spec_key] = 1.0
        
        try:
            result = eval(formula, safe_context)
            return float(result)
        except Exception as e:
            # Log error and return default
            return 1.0
    
    def _get_or_create_operation(self, template_line):
        """Get or create routing operation for template line"""
        # This is simplified - in real implementation, link to actual routing
        workcenter = self.env['mrp.workcenter'].search([
            ('name', 'ilike', template_line.operation_type or 'General')
        ], limit=1)
        
        if not workcenter:
            workcenter = self.env['mrp.workcenter'].create({
                'name': template_line.operation_type or 'General',
                'time_efficiency': 100.0,
            })
        
        routing = self.env['mrp.routing'].search([
            ('name', '=', self.category_template_id.name + ' Routing')
        ], limit=1)
        
        if not routing:
            routing = self.env['mrp.routing'].create({
                'name': self.category_template_id.name + ' Routing',
            })
        
        # Create routing operation
        operation_vals = {
            'name': template_line.operation_name,
            'workcenter_id': workcenter.id,
            'routing_id': routing.id,
            'time_cycle': self._evaluate_quantity_formula(
                template_line.time_formula or '30',
                self._get_product_specifications()
            ),
            'sequence': template_line.sequence,
        }
        
        return self.env['mrp.routing.workcenter'].create(operation_vals)
    
    def _create_sub_boms(self, created_components, specifications):
        """Create sub-BOMs for processed components based on dependencies"""
        for comp_id, comp_data in created_components.items():
            template_line = comp_data['template_line']
            
            if template_line.category == 'processed' and template_line.parent_line_ids:
                # Create sub-BOM for this component
                product = comp_data['product']
                
                sub_bom_vals = {
                    'product_id': product.id,
                    'product_tmpl_id': product.product_tmpl_id.id,
                    'product_qty': 1.0,
                    'type': 'normal',
                }
                sub_bom = self.env['mrp.bom'].create(sub_bom_vals)
                
                # Add parent components as BOM lines
                for parent_line in template_line.parent_line_ids:
                    if parent_line.id in created_components:
                        parent_product = created_components[parent_line.id]['product']
                        
                        qty = self._evaluate_quantity_formula(
                            parent_line.quantity_formula,
                            specifications
                        )
                        
                        self.env['mrp.bom.line'].create({
                            'bom_id': sub_bom.id,
                            'product_id': parent_product.id,
                            'product_qty': qty,
                            'product_uom_id': parent_line.uom_id.id,
                        })


    @api.depends('attribute_selection_ids')
    def _compute_attribute_selection_count(self):
        for record in self:
            record.attribute_selection_count = len(record.attribute_selection_ids)
    
    def action_view_attribute_selections(self):
        """View all saved combinations"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Attribute Combinations',
            'res_model': 'product.template.attribute.selection',
            'view_mode': 'tree,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {
                'default_product_tmpl_id': self.id,
            }
        }

    # @api.model
    def generate_variant_boms(self):
        """Generate BOMs for all variants based on attribute configuration"""
        for template in self:
            if not template.auto_generate_bom:
                continue
                
            # Get all product variants
            for variant in template.product_variant_ids:
                # Check if BOM already exists
                existing_bom = self.env['mrp.bom'].search([
                    ('product_id', '=', variant.id),
                    ('product_tmpl_id', '=', template.id)
                ], limit=1)
                
                if not existing_bom:
                    bom_vals = {
                        'product_tmpl_id': template.id,
                        'product_id': variant.id,
                        'code': "BOM-"f"{variant.default_code or ''}",
                        'type': 'normal',
                    }
                    
                    # Create BOM
                    bom = self.env['mrp.bom'].create(bom_vals)
                    
                    # Add BOM lines based on configuration
                    self._create_bom_lines(bom, variant)
    
    # def _create_bom_lines(self, bom, variant):
    #     """Create BOM lines based on variant attributes"""
    #     for component_config in self.bom_component_ids:
    #         # Check if component applies to this variant
    #         if self._component_applies_to_variant(component_config, variant):
    #             qty = component_config.quantity
                
    #             # Adjust quantity based on attribute values if needed
    #             for attr_value in variant.product_template_attribute_value_ids:
    #                 if attr_value.attribute_id.id in component_config.attribute_value_ids.mapped('attribute_id').ids:
    #                     qty *= component_config.get_multiplier_for_value(attr_value)
                
    #             self.env['mrp.bom.line'].create({
    #                 'bom_id': bom.id,
    #                 'product_id': component_config.component_id.id,
    #                 'product_qty': qty,
    #             })
    
    # def _component_applies_to_variant(self, component_config, variant):
    #     """Check if component configuration applies to variant"""
    #     if not component_config.attribute_value_ids:
    #         return True
            
    #     variant_value_ids = variant.product_template_attribute_value_ids.mapped('product_attribute_value_id').ids
    #     config_value_ids = component_config.attribute_value_ids.ids
        
    #     return bool(set(variant_value_ids) & set(config_value_ids))


    def _create_bom_lines(self, bom, variant):
        """Create BOM lines based on variant attributes"""
        for component_config in self.bom_component_ids:
            # Check if component applies to this variant
            if self._component_applies_to_variant(component_config, variant):
                qty = component_config.quantity
                
                # Adjust quantity based on attribute values if needed
                for attr_value in variant.product_template_attribute_value_ids:
                    if attr_value.attribute_id.id in component_config.attribute_value_ids.mapped('attribute_id').ids:
                        qty *= component_config.get_multiplier_for_value(attr_value)
                
                # Get the correct product variant for the component
                component_variant = self._get_component_variant(component_config, variant)
                
                self.env['mrp.bom.line'].create({
                    'bom_id': bom.id,
                    'product_id': component_variant.id,
                    'product_qty': qty,
                })

    def _get_component_variant(self, component_config, main_variant):
        """Get the appropriate component variant based on main variant attributes"""
        component_template = component_config.component_id
        
        # If component template has no variants, return the template itself
        if not component_template.product_variant_ids:
            return component_template
        
        # Get main variant's attribute values
        main_variant_attrs = {}
        for ptav in main_variant.product_template_attribute_value_ids:
            attr_id = ptav.attribute_id.id
            value_id = ptav.product_attribute_value_id.id
            main_variant_attrs[attr_id] = value_id
        
        # Find matching component variant
        for component_variant in component_template.product_variant_ids:
            variant_attrs = {}
            for ptav in component_variant.product_template_attribute_value_ids:
                attr_id = ptav.attribute_id.id
                value_id = ptav.product_attribute_value_id.id
                variant_attrs[attr_id] = value_id
            
            # Check if this component variant matches the main variant's relevant attributes
            if self._variant_attributes_match(main_variant_attrs, variant_attrs, component_config):
                return component_variant
        
        # If no specific variant found, return the first variant or template
        return component_template.product_variant_ids[0] if component_template.product_variant_ids else component_template

    def _variant_attributes_match(self, main_attrs, component_attrs, component_config):
        """Check if component variant attributes match main variant for relevant attributes"""
        # Get relevant attribute IDs from component configuration
        relevant_attr_ids = component_config.attribute_value_ids.mapped('attribute_id').ids
        
        # If no specific attributes configured, use all common attributes
        if not relevant_attr_ids:
            relevant_attr_ids = set(main_attrs.keys()) & set(component_attrs.keys())
        
        # Check if all relevant attributes match
        for attr_id in relevant_attr_ids:
            if attr_id in main_attrs and attr_id in component_attrs:
                if main_attrs[attr_id] != component_attrs[attr_id]:
                    return False
            elif attr_id in main_attrs or attr_id in component_attrs:
                # One has the attribute, the other doesn't - no match
                return False
        
        return True

    def _component_applies_to_variant(self, component_config, variant):
        """Check if component configuration applies to variant"""
        if not component_config.attribute_value_ids:
            return True
            
        variant_value_ids = variant.product_template_attribute_value_ids.mapped('product_attribute_value_id').ids
        config_value_ids = component_config.attribute_value_ids.ids
        
        return bool(set(variant_value_ids) & set(config_value_ids))

    def generate_variant_codes(self):
        """Generate codes for all variants based on attribute combinations"""
        self.ensure_one()
        
        if not self.base_code:
            raise UserError("Please set base code first!")
        
        # Update all variants
        for variant in self.product_variant_ids:
            variant._generate_variant_code()
            
        return True


    bom_series_ids = fields.One2many(
        'product.bom.series', 'product_tmpl_id', 
        string='BOM Series',
        help='Manufacturing sequence levels for this product'
    )
    bom_series_count = fields.Integer(
        string='BOM Series Count',
        compute='_compute_bom_series_count'
    )
    max_production_level = fields.Integer(
        string='Max Production Level',
        compute='_compute_max_production_level',
        store=True
    )
    
    @api.depends('bom_series_ids')
    def _compute_bom_series_count(self):
        for record in self:
            record.bom_series_count = len(record.bom_series_ids)
    
    @api.depends('bom_series_ids.level')
    def _compute_max_production_level(self):
        for record in self:
            if record.bom_series_ids:
                record.max_production_level = max(record.bom_series_ids.mapped('level'))
            else:
                record.max_production_level = 0
    
    def action_view_bom_series(self):
        """Open BOM series view"""
        self.ensure_one()
        return {
            'name': f'BOM Series - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'product.bom.series',
            'view_mode': 'tree,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {
                'default_product_tmpl_id': self.id,
                'group_by': 'level'
            }
        }

    def action_recompute_variants(self):
        """Simple recompute variants"""
        self.ensure_one()
        
        # Clear cache
        self.clear_caches()
        
        # Create missing variants and archive invalid ones
        self._create_variant_ids()
        
        # Update prices
        self._update_variant_prices()
        
        # Show success message
        message = _('%d variants processed for %s') % (
            len(self.product_variant_ids), 
            self.name
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def _update_variant_prices(self):
        """Update variant prices based on attributes"""
        for variant in self.product_variant_ids:
            # Calculate price extra from attributes
            price_extra = 0.0
            for ptav in variant.product_template_attribute_value_ids:
                price_extra += ptav.price_extra
            
            # Update variant price
            variant.write({
                'price_extra': price_extra,
                'lst_price': self.list_price + price_extra
            })
    
    def write(self, vals):
        """Override write to check category changes"""
        if 'categ_id' in vals:
            self._check_category_change_permission(vals['categ_id'])
        
        return super(ks_ProductTemplate, self).write(vals)

    def _check_category_change_permission(self, new_categ_id):
        """Check if user can change category"""
        # Admin can always change
        if self.env.user.has_group('base.group_system'):
            return True
        
        new_category = self.env['product.category'].browse(new_categ_id)
        
        for record in self:
            old_category = record.categ_id
            
            # Check if OLD category is protected
            old_is_protected = self._is_protected_category(old_category)
            
            # Check if NEW category is protected
            new_is_protected = self._is_protected_category(new_category)
            
            # If either old or new category is protected, block the change
            if old_is_protected or new_is_protected:
                error_msg = _(
                    'You cannot change product category for protected categories.\n\n'
                    'Product: %s\n'
                    'Current Category: %s%s\n'
                    'New Category: %s%s\n\n'
                    'Protected categories: %s\n\n'
                    'Only administrators can modify products in these categories.'
                ) % (
                    record.name,
                    old_category.name,
                    ' (Protected)' if old_is_protected else '',
                    new_category.name,
                    ' (Protected)' if new_is_protected else '',
                    ', '.join(self.PROTECTED_CATEGORY_NAMES)
                )
                
                # Log the attempt
                _logger.warning(
                    'User %s attempted to change category of product %s from %s to %s',
                    self.env.user.name,
                    record.name,
                    old_category.name,
                    new_category.name
                )
                
                raise UserError(error_msg)

    def generate_bom_series(self):
        """Generate BOM series based on existing BOMs"""
        self.ensure_one()
        
        # Clear existing series
        self.bom_series_ids.unlink()
        
        # Get all BOMs for this product and its variants
        bom_ids = self.env['mrp.bom'].search([
            '|', 
            ('product_tmpl_id', '=', self.id),
            ('product_id', 'in', self.product_variant_ids.ids)
        ])
        
        if not bom_ids:
            raise UserError(f"No BOMs found for product {self.name}")
        
        # Generate series for each BOM
        for bom in bom_ids:
            self._create_bom_series_recursive(bom, level=1, parent_series=None)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'BOM series generated successfully for {self.name}',
                'type': 'success'
            }
        }
    
    def _create_bom_series_recursive(self, bom, level, parent_series, processed_boms=None):
        """Recursively create BOM series entries"""
        
        # Initialize processed BOMs set to avoid infinite recursion
        if processed_boms is None:
            processed_boms = set()
        
        # Skip if this BOM was already processed
        if bom.id in processed_boms:
            print(f'---BOM {bom.code or bom.id} already processed, skipping')
            return
        
        processed_boms.add(bom.id)
        print(processed_boms)
        print(f'---Processing BOM at level {level}: {bom.code or bom.product_tmpl_id.name} (ID: {bom.id})')
        
        # Create series entry for current BOM
        series_vals = {
            'product_tmpl_id': self.id,
            'bom_id': bom.id,
            'level': level,
            'sequence': level * 10,
            'parent_series_id': parent_series.id if parent_series else False,
            'product_variant_id': bom.product_id.id if bom.product_id else False,
        }
        
        current_series = self.env['product.bom.series'].create(series_vals)
        print(f'---Created series entry: Level {level}, BOM {bom.code or bom.id}')
        
        # Process BOM lines to find sub-assemblies
        print(f'---Processing {len(bom.bom_line_ids)} BOM lines')
        for line in bom.bom_line_ids:
            component_product = line.product_id
            print(f'---Checking component: {component_product.name} (ID: {component_product.id})')
            print(f'---Component template: {component_product.product_tmpl_id.name} (ID: {component_product.product_tmpl_id.id})')
            
            # Check if component has its own BOM (sub-assembly)
            # Search more comprehensively
            component_bom_domain = [
                '|', '|', '|',
                ('product_tmpl_id', '=', component_product.product_tmpl_id.id),
                ('product_id', '=', component_product.id),
                ('product_id', '=', False),  # Template-level BOMs
                ('product_tmpl_id', '=', component_product.product_tmpl_id.id)
            ]
            
            # print(f'---Searching BOMs with domain: {component_bom_domain}')
            component_boms = self.env['mrp.bom'].search(component_bom_domain)
            # print(component_boms)
            
            print(f'---Found {len(component_boms)} BOMs for component {component_product.name}')
            for cb in component_boms:
                print(cb)
                if cb.product_tmpl_id.name == 'Ball valve side body':
                    print('---ada')
                print(f'   - BOM ID: {cb.id}, Code: {cb.code}, Product: {cb.product_tmpl_id.name}, Variant: {cb.product_id.name if cb.product_id else "All"}')
            
            if component_boms:
                # Filter BOMs that actually produce this component
                valid_boms = component_boms.filtered(
                    lambda b: b.product_tmpl_id.id == component_product.product_tmpl_id.id and 
                    (not b.product_id or b.product_id.id == component_product.id)
                )
                
                print(f'---Valid BOMs after filtering: {len(valid_boms)}')
                
                if valid_boms:
                    # Recursively create series for sub-assemblies
                    for component_bom in valid_boms:
                        print(f'---Recursing into BOM: {component_bom.code or component_bom.id}')
                        self._create_bom_series_recursive(
                            component_bom, 
                            level + 1, 
                            current_series,
                            processed_boms
                        )
                else:
                    print(f'---No valid BOMs found for {component_product.name}')
            else:
                print(f'---No BOMs found for component {component_product.name} - treating as raw material')

    # def _create_bom_series_recursive(self, bom, level, parent_series):
    #     """Recursively create BOM series entries"""
        
    #     # Create series entry for current BOM
    #     series_vals = {
    #         'product_tmpl_id': self.id,
    #         'bom_id': bom.id,
    #         'level': level,
    #         'sequence': level * 10,
    #         'parent_series_id': parent_series.id if parent_series else False,
    #         'product_variant_id': bom.product_id.id if bom.product_id else False,
    #     }
        
    #     current_series = self.env['product.bom.series'].create(series_vals)
        
    #     # Process BOM lines to find sub-assemblies
    #     for line in bom.bom_line_ids:
    #         # print('---line')
    #         # print(line)
    #         component_product = line.product_id
            
    #         # Check if component has its own BOM (sub-assembly)
    #         component_boms = self.env['mrp.bom'].search([
    #             '|',
    #             ('product_tmpl_id', '=', component_product.product_tmpl_id.id),
    #             ('product_id', '=', component_product.id)
    #         ])
            
    #         # print(component_boms)
    #         if component_boms:
    #             # Recursively create series for sub-assemblies
    #             for component_bom in component_boms:
    #                 self._create_bom_series_recursive(
    #                     component_bom, 
    #                     level + 1, 
    #                     current_series
    #                 )


class ProductBomSeries(models.Model):
    _name = 'product.bom.series'
    _description = 'Product BOM Series'
    _order = 'level, sequence, id'
    
    product_tmpl_id = fields.Many2one(
        'product.template', 
        string='Product Template',
        required=True,
        ondelete='cascade'
    )
    bom_id = fields.Many2one(
        'mrp.bom', 
        string='Bill of Materials',
        required=True
    )
    level = fields.Integer(
        string='Production Level',
        required=True,
        help='Level in production hierarchy (1=final product, 2=sub-assembly, etc.)'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of execution within the same level'
    )
    parent_series_id = fields.Many2one(
        'product.bom.series',
        string='Parent Series',
        help='Parent level in production hierarchy'
    )
    child_series_ids = fields.One2many(
        'product.bom.series',
        'parent_series_id',
        string='Child Series'
    )
    product_variant_id = fields.Many2one(
        'product.product',
        string='Product Variant'
    )
    
    # Related fields for easy access
    bom_product_name = fields.Char(
        related='bom_id.product_tmpl_id.name',
        string='BOM Product',
        store=True
    )
    bom_reference = fields.Char(
        related='bom_id.code',
        string='BOM Reference',
        store=True
    )
    bom_type = fields.Selection(
        related='bom_id.type',
        string='BOM Type',
        store=True
    )
    
    manufacturing_lead_time = fields.Float(
        related='bom_id.product_tmpl_id.produce_delay',
        string='Manufacturing Lead Time',
        store=True
    )
    
    @api.depends('level')
    def _compute_display_name(self):
        for record in self:
            level_prefix = "  " * (record.level - 1)
            record.display_name = f"{level_prefix}Level {record.level}: {record.bom_product_name}"
    
    def action_view_bom(self):
        """Open the related BOM"""
        self.ensure_one()
        return {
            'name': f'BOM - {self.bom_product_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom',
            'res_id': self.bom_id.id,
            'view_mode': 'form',
            'target': 'current'
        }
    
    def action_create_mo(self):
        """Create Manufacturing Order for this BOM level"""
        self.ensure_one()
        
        return {
            'name': f'Create MO - Level {self.level}',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_bom_id': self.bom_id.id,
                'default_product_id': self.bom_id.product_id.id or self.bom_id.product_tmpl_id.product_variant_id.id,
            }
        }


class ProductBomComponent(models.Model):
    _name = 'product.bom.component'
    _description = 'Product BOM Component Configuration'
    
    product_tmpl_id = fields.Many2one('product.template', required=True)
    component_id = fields.Many2one('product.template', string='Component', required=True)
    quantity = fields.Float(string='Base Quantity', default=1.0, required=True)
    attribute_value_ids = fields.Many2many(
        'product.attribute.value',
        string='Applicable Attribute Values',
        help='Leave empty to apply to all variants'
    )
    multiplier_config = fields.One2many(
        'bom.component.multiplier',
        'component_config_id',
        string='Quantity Multipliers'
    )
    
    def get_multiplier_for_value(self, attr_value):
        """Get quantity multiplier for specific attribute value"""
        multiplier = self.multiplier_config.filtered(
            lambda m: m.attribute_value_id == attr_value.product_attribute_value_id
        )
        return multiplier.multiplier if multiplier else 1.0


class BomComponentMultiplier(models.Model):
    _name = 'bom.component.multiplier'
    _description = 'BOM Component Quantity Multiplier'
    
    component_config_id = fields.Many2one('product.bom.component', required=True)
    attribute_value_id = fields.Many2one('product.attribute.value', required=True)
    multiplier = fields.Float(string='Multiplier', default=1.0, required=True)


class ks_ProductProduct(models.Model):
    # _name = 'product.product'
    _inherit = 'product.product'
    
    def button_bom_cost(self):
        self.ensure_one()
        self._set_price_from_bom()
    
    track_weight_by_serial = fields.Boolean(
        string='Track Weight by Serial',
        help='Track weight for each serial number'
    )
    

    def _set_price_from_bom(self, boms_to_recompute=False):
        self.ensure_one()
        bom = self.env['mrp.bom']._bom_find(self)[self]
        if bom:
            self.standard_price = self._compute_bom_price(bom, boms_to_recompute=boms_to_recompute)
        else:
            bom = self.env['mrp.bom'].search([('byproduct_ids.product_id', '=', self.id)], order='sequence, product_id, id', limit=1)
            if bom:
                price = self._compute_bom_price(bom, boms_to_recompute=boms_to_recompute, byproduct_bom=True)
                if price:
                    self.standard_price = price
                    
                    
    def get_weight_for_valuation(self, lot_id=None, quantity=1):
        """Get weight for valuation calculation"""
        self.ensure_one()
        
        if not self.track_weight_by_serial:
            return quantity * self.standard_weight_per_unit
        
        if lot_id:
            lot = self.env['stock.lot'].browse(lot_id)
            return lot.current_weight
        
        return quantity * self.standard_weight_per_unit
    

    def _compute_bom_price(self, bom, boms_to_recompute=False, byproduct_bom=False):
        print('---el')
        
        self.ensure_one()
        if not bom:
            return 0
        if not boms_to_recompute:
            boms_to_recompute = []
        total = 0
        
        for opt in bom.operation_ids:
            if opt._skip_operation_line(self):
                continue

            duration_expected = (
                opt.workcenter_id._get_expected_duration(self) +
                opt.time_cycle * 100 / opt.workcenter_id.time_efficiency)
            total += (duration_expected / 60) * opt._total_cost_per_hour()

        for line in bom.bom_line_ids:
            if line._skip_bom_line(self):
                continue
            weight_contribution = line.weight_contribution
            print('---e')
            print(weight_contribution)
            # Compute recursive if line has `child_line_ids`
            if line.child_bom_id and line.child_bom_id in boms_to_recompute:
                child_total = line.product_id._compute_bom_price(line.child_bom_id, boms_to_recompute=boms_to_recompute)
                total += line.product_id.uom_id._compute_price(child_total, line.product_uom_id) * line.product_qty
            else:
                total += line.product_id.uom_id._compute_price(line.product_id.standard_price, line.product_uom_id) * line.product_qty
        
            total = total + (total * ((100 - weight_contribution)/100))
        
        if byproduct_bom:
            byproduct_lines = bom.byproduct_ids.filtered(lambda b: b.product_id == self and b.cost_share != 0)
            product_uom_qty = 0
            for line in byproduct_lines:
                product_uom_qty += line.product_uom_id._compute_quantity(line.product_qty, self.uom_id, round=False)
            byproduct_cost_share = sum(byproduct_lines.mapped('cost_share'))
            if byproduct_cost_share and product_uom_qty:
                return total * byproduct_cost_share / 100 / product_uom_qty
        else:
            byproduct_cost_share = sum(bom.byproduct_ids.mapped('cost_share'))
            if byproduct_cost_share:
                total *= float_round(1 - byproduct_cost_share / 100, precision_rounding=0.0001)
            return bom.product_uom_id._compute_price(total / bom.product_qty, self.uom_id)



class ProductTemplateAttributeSelection(models.Model):
    _name = 'product.template.attribute.selection'
    _description = 'Product Template Attribute Selection'
    _order = 'sequence, id'
    
    product_tmpl_id = fields.Many2one(
        'product.template', 
        string='Product Template',
        required=True,
        ondelete='cascade',
        index=True
    )
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(
        string='Name',
    )
    code = fields.Char(
        string='Code',
        store=True
    )
    active = fields.Boolean(default=True)
    
    attribute_id = fields.Many2one('product.attribute','attribute_id'
    )

    # value_id = fields.Many2one('product.attribute_value','value_id')

    value_id = fields.Many2one(
        'product.attribute.value',
        string='Value',
        domain="[('attribute_id', '=', attribute_id)]",
        required=True
    )

    # Attribute selections
    # attribute_line_ids = fields.One2many(
    #     'product.template.attribute.selection.line',
    #     'selection_id',
    #     string='Attribute Values'
    # )
    
    # Generated product info
    product_id = fields.Many2one(
        'product.product',
        string='Generated Product',
        readonly=True
    )
    is_generated = fields.Boolean(
        string='Is Generated',
        compute='_compute_is_generated',
        store=True
    )
    
    @api.depends('attribute_line_ids.value_id')
    def _compute_name(self):
        for record in self:
            names = []
            for line in record.attribute_line_ids:
                if line.value_id:
                    names.append(line.value_id.name)
            record.name = ' '.join(names)
    
    @api.depends('attribute_line_ids.value_id')
    def _compute_code(self):
        for record in self:
            codes = []
            for line in record.attribute_line_ids:
                if line.value_id and line.value_id.code:
                    codes.append(line.value_id.code)
            record.code = ''.join(codes)
    
    @api.depends('product_id')
    def _compute_is_generated(self):
        for record in self:
            record.is_generated = bool(record.product_id)
    
    def action_generate_variant(self):
        """Generate product variant from this selection"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'generate.product.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_tmpl_id': self.product_tmpl_id.id,
                'default_selection_id': self.id,
                'load_from_selection': True,
            }
        }
    
    def action_view_product(self):
        """View generated product"""
        self.ensure_one()
        if self.product_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'product.product',
                'res_id': self.product_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

    # def generate_bom_series(self):
    #     """Generate BOM series based on existing BOMs"""
    #     self.ensure_one()
        
    #     # Clear existing series
    #     self.bom_series_ids.unlink()
        
    #     # Get all BOMs for this product and its variants
    #     bom_ids = self.env['mrp.bom'].search([
    #         '|', 
    #         ('product_tmpl_id', '=', self.id),
    #         ('product_id', 'in', self.product_variant_ids.ids)
    #     ])
        
    #     print(bom_ids)
    #     # if not bom_ids:
    #     #     raise UserError(f"No BOMs found for product {self.name}")
        
    #     # # Generate series for each BOM
    #     # for bom in bom_ids:
    #     #     self._create_bom_series_recursive(bom, level=1, parent_series=None)
        
    #     # return {
    #     #     'type': 'ir.actions.client',
    #     #     'tag': 'display_notification',
    #     #     'params': {
    #     #         'title': 'Success',
    #     #         'message': f'BOM series generated successfully for {self.name}',
    #     #         'type': 'success'
    #     #     }
    #     # }


class ProductTemplateAttributeSelectionLine(models.Model):
    _name = 'product.template.attribute.selection.line'
    _description = 'Product Template Attribute Selection Line'
    _order = 'sequence, id'
    
    selection_id = fields.Many2one(
        'product.template.attribute.selection',
        string='Selection',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequence', default=10)
    
    attribute_id = fields.Many2one(
        'product.attribute',
        string='Attribute',
        required=True
    )
    value_id = fields.Many2one(
        'product.attribute.value',
        string='Value',
        domain="[('attribute_id', '=', attribute_id)]",
        required=True
    )
    
    @api.onchange('attribute_id')
    def _onchange_attribute_id(self):
        if self.attribute_id:
            # Clear value if attribute changed
            if self.value_id and self.value_id.attribute_id != self.attribute_id:
                self.value_id = False
                
                
                
class ProductTemplateAttributeLine(models.Model):
    _inherit = 'product.template.attribute.line'
    _order = 'sequence, id'
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Determines the order of attributes. Lower values come first.'
    )
    
    # Optional: Auto-increment sequence for new lines
    @api.model
    def create(self, vals):
        if 'sequence' not in vals:
            # Get the highest sequence for this template
            template_id = vals.get('product_tmpl_id')
            if template_id:
                max_sequence = self.search([
                    ('product_tmpl_id', '=', template_id)
                ], order='sequence desc', limit=1).sequence or 0
                vals['sequence'] = max_sequence + 10
        
        return super().create(vals)
    
    
    
class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_recompute_variants(self):
        """Redirect to template recompute"""
        self.ensure_one()
        return self.product_tmpl_id.action_recompute_variants()
    
    def _generate_variant_code(self):
        """Generate code for single variant"""
        self.ensure_one()
        
        # Get base code from template
        base_code = self.product_tmpl_id.base_code
        if not base_code:
            return False
            
        # Get attribute values sorted by attribute sequence
        attribute_values = self.product_template_attribute_value_ids.sorted(
            lambda x: (x.attribute_id.sequence)
        )

        attribute_lines = self.attribute_line_ids.sorted(
            lambda x: (x.sequence)
        )
        print(len(attribute_lines))

        # Build code parts
        code_parts = [base_code]
        attr_code = []

        for ptal in attribute_lines:
            # print(ptal.code)
            print(ptal.sequence)


        for ptav in attribute_values:
            # print(ptav.product_attribute_value_id.sequence)
            if ptav.product_attribute_value_id.code:
                code_parts.append(ptav.product_attribute_value_id.code)
                attr_code.append(ptav.product_attribute_value_id.code)

        # Generate final code
        self.default_code = ''.join(code_parts)
        self.tracking = 'serial'
        
        if self.product_tmpl_id.raw_type == 'rm':
            self.categ_id = 95
        elif self.product_tmpl_id.raw_type == 'wip':
            self.categ_id = 96
        self.attribute_code = attr_code

        return True
    
    # @api.model
    # def create(self, vals):
    #     product = super().create(vals)
    #     # Auto generate code if not provided
    #     if not product.default_code and product.product_tmpl_id.base_code:
    #         product._generate_variant_code()
    #     return product