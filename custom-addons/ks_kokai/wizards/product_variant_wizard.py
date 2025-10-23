# wizards/product_variant_wizard.py

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from itertools import product as iter_product
from collections import defaultdict

_logger = logging.getLogger(__name__)

class ProductVariantWizard(models.TransientModel):
    _name = 'product.variant.wizard'
    _description = 'Product Variant Generation Wizard'

    # Basic fields
    category_template_id = fields.Many2one(
        'product.category.template',
        string='Category Template',
        required=True,
        default=lambda self: self.env.context.get('active_id')
    )
    
    # Template lines
    template_line_ids = fields.One2many(
        'product.variant.wizard.line',
        'wizard_id',
        string='Components',
        compute='_compute_template_lines',
        store=True,
        readonly=False
    )

    product_template_id = fields.Many2one(
        'product.template',
        string='Product Template',
        help='Optional: Select specific product template to generate variants'
    )
    
    variant_generation_type = fields.Selection([
        ('all', 'All Products'),
        ('selected', 'Selected Products Only'),
    ], string='Generation Type', default='selected', required=True)
        
    # Attribute configuration
    attribute_line_ids = fields.One2many(
        'product.variant.wizard.attribute',
        'wizard_id',
        string='Attributes'
    )
    
    # Statistics
    total_products = fields.Integer(
        'Total Products',
        compute='_compute_statistics'
    )
    total_possible_variants = fields.Integer(
        'Possible Variants',
        compute='_compute_statistics'
    )
    total_existing_variants = fields.Integer(
        'Existing Variants',
        compute='_compute_statistics'
    )
    total_new_variants = fields.Integer(
        'New Variants',
        compute='_compute_statistics'
    )
    
    # Options
    skip_existing = fields.Boolean('Skip Existing', default=True)
    batch_size = fields.Integer('Batch Size', default=100)
    
    @api.depends('category_template_id')
    def _compute_template_lines(self):
        for wizard in self:
            if wizard.category_template_id and not wizard.template_line_ids:
                lines = []
                for template_line in wizard.category_template_id.template_line_ids:
                    if template_line.product_id:
                        lines.append((0, 0, {
                            'template_line_id': template_line.id,
                            'product_id': template_line.product_id.id,
                            'name': template_line.name,
                            'level': template_line.level,
                            'category': template_line.category,
                            'component_type': template_line.component_type,
                            'selected': True,
                        }))
                wizard.template_line_ids = lines
    
    @api.depends('template_line_ids.selected', 'attribute_line_ids.value_ids')
    def _compute_statistics(self):
        for wizard in self:
            selected_products = wizard.template_line_ids.filtered('selected').mapped('product_id')
            wizard.total_products = len(selected_products)
            
            # Calculate total possible variants
            total_possible = 0
            total_existing = 0
            
            for product in selected_products:
                # Get attribute combinations
                attr_count = 1
                for attr_line in wizard.attribute_line_ids:
                    if attr_line.value_ids:
                        attr_count *= len(attr_line.value_ids)
                
                total_possible += attr_count
                total_existing += len(product.product_variant_ids)
            
            wizard.total_possible_variants = total_possible
            wizard.total_existing_variants = total_existing
            wizard.total_new_variants = max(0, total_possible - total_existing)

    def action_generate_variants(self):
        """Generate variants using direct SQL"""
        self.ensure_one()
        
        if not self.template_line_ids.filtered('selected'):
            raise UserError(_('Please select at least one product.'))
        
        if not self.attribute_line_ids or not any(line.value_ids for line in self.attribute_line_ids):
            raise UserError(_('Please select at least one attribute value.'))
        
        # Start generation
        results = self._generate_all_variants()
        
        # Show results
        return self._show_results(results)
    
    def _generate_all_variants(self):
        """Generate all variants using SQL"""
        cr = self.env.cr
        results = {
            'created': 0,
            'skipped': 0,
            'errors': []
        }
        
        # Get selected products
        selected_products = self.template_line_ids.filtered('selected').mapped('product_id')
        
        # Get attribute combinations
        attribute_combinations = self._get_attribute_combinations()
        
        if not attribute_combinations:
            return results
        
        # Process each product
        for product in selected_products:
            try:
                created, skipped = self._process_product_variants_sql(
                    product.id, 
                    attribute_combinations
                )
                results['created'] += created
                results['skipped'] += skipped
                
                # Commit every batch
                if (results['created'] + results['skipped']) % self.batch_size == 0:
                    cr.commit()
                    
            except Exception as e:
                cr.rollback()
                results['errors'].append(f"{product.name}: {str(e)}")
                _logger.error(f"Error processing {product.name}: {str(e)}")
        
        # Final commit
        cr.commit()
        
        # Clear cache
        self.env.invalidate_all()
        
        return results
    
    def _get_attribute_combinations(self):
        """Get all attribute combinations"""
        attributes = []
        value_lists = []
        
        for attr_line in self.attribute_line_ids:
            if attr_line.value_ids:
                attributes.append(attr_line.attribute_id.id)
                value_lists.append(attr_line.value_ids.ids)
        
        if not value_lists:
            return []
        
        # Generate all combinations
        combinations = []
        for values in iter_product(*value_lists):
            combo = list(zip(attributes, values))
            combinations.append(combo)
        
        return combinations
    
    def _process_product_variants_sql(self, product_tmpl_id, combinations):
        """Process variants for one product using SQL"""
        cr = self.env.cr
        created = 0
        skipped = 0
        
        # Get existing variants
        existing = self._get_existing_variants_sql(product_tmpl_id)
        
        # Ensure attribute lines exist
        self._ensure_attribute_lines_sql(product_tmpl_id, combinations)
        
        # Process each combination
        for combo in combinations:
            combo_key = frozenset(combo)
            
            if self.skip_existing and combo_key in existing:
                skipped += 1
                continue
            
            # Create variant
            variant_id = self._create_variant_sql(product_tmpl_id, combo)
            if variant_id:
                created += 1
            else:
                skipped += 1
        
        return created, skipped
    
    def _get_existing_variants_sql(self, product_tmpl_id):
        """Get existing variant combinations"""
        cr = self.env.cr
        
        query = """
            SELECT pp.id,
                   array_agg(
                       ARRAY[pav.attribute_id, pav.id]::int[] 
                       ORDER BY pav.attribute_id
                   ) as combo
            FROM product_product pp
            JOIN product_variant_combination pvc ON pvc.product_product_id = pp.id
            JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
            JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
            WHERE pp.product_tmpl_id = %s AND pp.active = true
            GROUP BY pp.id
        """
        
        cr.execute(query, (product_tmpl_id,))
        
        existing = set()
        for row in cr.fetchall():
            if row[1]:
                combo = frozenset(tuple(pair) for pair in row[1])
                existing.add(combo)
        
        return existing
    
    def _ensure_attribute_lines_sql(self, product_tmpl_id, combinations):
        """Ensure attribute lines exist on product template"""
        cr = self.env.cr
        
        # Get all needed attributes
        needed_attrs = defaultdict(set)
        for combo in combinations:
            for attr_id, value_id in combo:
                needed_attrs[attr_id].add(value_id)
        
        for attr_id, value_ids in needed_attrs.items():
            # Check if attribute line exists
            cr.execute("""
                SELECT id FROM product_template_attribute_line
                WHERE product_tmpl_id = %s AND attribute_id = %s
            """, (product_tmpl_id, attr_id))
            
            result = cr.fetchone()
            
            if result:
                line_id = result[0]
                # Add missing values
                for value_id in value_ids:
                    cr.execute("""
                        INSERT INTO product_attribute_value_product_template_attribute_line_rel
                        (product_attribute_value_id, product_template_attribute_line_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (value_id, line_id))
            else:
                # Create attribute line
                cr.execute("""
                    INSERT INTO product_template_attribute_line
                    (product_tmpl_id, attribute_id, active, create_uid, write_uid, create_date, write_date)
                    VALUES (%s, %s, true, %s, %s, NOW(), NOW())
                    RETURNING id
                """, (product_tmpl_id, attr_id, self.env.uid, self.env.uid))
                
                line_id = cr.fetchone()[0]
                
                # Add values
                for value_id in value_ids:
                    cr.execute("""
                        INSERT INTO product_attribute_value_product_template_attribute_line_rel
                        (product_attribute_value_id, product_template_attribute_line_id)
                        VALUES (%s, %s)
                    """, (value_id, line_id))
    
    def _create_variant_sql(self, product_tmpl_id, combination):
        """Create single variant using SQL"""
        cr = self.env.cr
        
        try:
            # Create product variant
            cr.execute("""
                INSERT INTO product_product
                (product_tmpl_id, active, default_code, create_uid, write_uid, create_date, write_date)
                VALUES (%s, true, '', %s, %s, NOW(), NOW())
                RETURNING id
            """, (product_tmpl_id, self.env.uid, self.env.uid))
            
            variant_id = cr.fetchone()[0]
            
            # Create PTAVs and combinations
            ptav_ids = []
            
            for attr_id, value_id in combination:
                # Get or create PTAV
                cr.execute("""
                    SELECT ptav.id
                    FROM product_template_attribute_value ptav
                    JOIN product_template_attribute_line ptal ON ptal.id = ptav.attribute_line_id
                    WHERE ptav.product_tmpl_id = %s 
                      AND ptav.attribute_id = %s 
                      AND ptav.product_attribute_value_id = %s
                """, (product_tmpl_id, attr_id, value_id))
                
                result = cr.fetchone()
                
                if not result:
                    # Get attribute line
                    cr.execute("""
                        SELECT id FROM product_template_attribute_line
                        WHERE product_tmpl_id = %s AND attribute_id = %s
                    """, (product_tmpl_id, attr_id))
                    
                    line_id = cr.fetchone()[0]
                    
                    # Create PTAV
                    cr.execute("""
                        INSERT INTO product_template_attribute_value
                        (product_tmpl_id, attribute_id, product_attribute_value_id, 
                         attribute_line_id, ptav_active, create_uid, write_uid, create_date, write_date)
                        VALUES (%s, %s, %s, %s, true, %s, %s, NOW(), NOW())
                        RETURNING id
                    """, (product_tmpl_id, attr_id, value_id, line_id, self.env.uid, self.env.uid))
                    
                    ptav_id = cr.fetchone()[0]
                else:
                    ptav_id = result[0]
                
                ptav_ids.append(str(ptav_id))
                
                # Create combination
                cr.execute("""
                    INSERT INTO product_variant_combination
                    (product_product_id, product_template_attribute_value_id)
                    VALUES (%s, %s)
                """, (variant_id, ptav_id))
            
            # Update combination indices
            cr.execute("""
                UPDATE product_product
                SET combination_indices = %s
                WHERE id = %s
            """, (','.join(sorted(ptav_ids)), variant_id))
            
            return variant_id
            
        except Exception as e:
            _logger.error(f"Error creating variant: {str(e)}")
            cr.rollback()
            return None
    
    def _show_results(self, results):
        """Show generation results"""
        if results['errors']:
            message = f"Created: {results['created']}, Skipped: {results['skipped']}\n\nErrors:\n"
            message += "\n".join(results['errors'][:5])
            msg_type = 'warning'
        else:
            message = f"Successfully created {results['created']} new variants. Skipped {results['skipped']} existing."
            msg_type = 'success'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Variant Generation Complete'),
                'message': message,
                'type': msg_type,
                'sticky': bool(results['errors']),
            }
        }

    @api.depends('category_template_id', 'product_template_id')
    def _compute_template_lines(self):
        for wizard in self:
            if wizard.category_template_id and not wizard.template_line_ids:
                lines = []
                for template_line in wizard.category_template_id.template_line_ids:
                    if template_line.product_id:
                        # Check if specific product template is selected
                        if wizard.product_template_id and template_line.product_id != wizard.product_template_id:
                            continue
                            
                        lines.append((0, 0, {
                            'template_line_id': template_line.id,
                            'product_id': template_line.product_id.id,
                            'name': template_line.name,
                            'level': template_line.level,
                            'category': template_line.category,
                            'component_type': template_line.component_type,
                            'selected': True,
                        }))
                wizard.template_line_ids = lines
                
                # Initialize attribute lines WITHOUT values
                wizard._initialize_empty_attributes()
    
    def _initialize_empty_attributes(self):
        """Initialize attribute lines with empty values"""
        self.ensure_one()
        
        # Get all unique attributes from selected template lines
        attributes = self.env['product.attribute']
        
        for line in self.template_line_ids:
            if line.material_attribute_ids:
                attributes |= line.material_attribute_ids
        
        # Create attribute lines with NO values selected
        attribute_lines = []
        for attribute in attributes:
            attribute_lines.append((0, 0, {
                'attribute_id': attribute.id,
                'value_ids': [(5, 0, 0)],  # Clear all values
            }))
        
        self.attribute_line_ids = attribute_lines
    
    def load_all_values(self):
        """Load all available values for each attribute"""
        self.ensure_one()
        
        for attr_line in self.attribute_line_ids:
            all_values = self.env['product.attribute.value'].search([
                ('attribute_id', '=', attr_line.attribute_id.id)
            ])
            attr_line.value_ids = [(6, 0, all_values.ids)]
        
        return {'type': 'ir.actions.do_nothing'}
    
    def load_common_values(self):
        """Load only common/frequently used values"""
        self.ensure_one()
        
        # Define common values per attribute (customize as needed)
        common_values_map = {
            'Size': ['1/2"', '3/4"', '1"', '1-1/2"', '2"'],
            'Material': ['SS316', 'SS304', 'Carbon Steel'],
            'Pressure': ['150#', '300#', '600#'],
            # Add more as needed
        }
        
        for attr_line in self.attribute_line_ids:
            attr_name = attr_line.attribute_id.name
            
            if attr_name in common_values_map:
                common_value_names = common_values_map[attr_name]
                values = self.env['product.attribute.value'].search([
                    ('attribute_id', '=', attr_line.attribute_id.id),
                    ('name', 'in', common_value_names)
                ])
                attr_line.value_ids = [(6, 0, values.ids)]
        
        return {'type': 'ir.actions.do_nothing'}
    
    def clear_all_values(self):
        """Clear all selected attribute values"""
        self.attribute_line_ids.write({'value_ids': [(5, 0, 0)]})
        return {'type': 'ir.actions.do_nothing'}



class ProductVariantWizardLine(models.TransientModel):
    _name = 'product.variant.wizard.line'
    _description = 'Product Selection Line'
    
    wizard_id = fields.Many2one('product.variant.wizard', required=True, ondelete='cascade')
    template_line_id = fields.Many2one('product.category.template.line')
    
    product_id = fields.Many2one('product.template', 'Product', required=True)
    name = fields.Char('Component', readonly=True)
    selected = fields.Boolean('Generate', default=True)
    # ADD material attributes display
    material_attribute_ids = fields.Many2many(
        'product.attribute',
        related='template_line_id.material_attribute_ids',
        readonly=True
    )
        
    # Info fields
    level = fields.Integer('Level', readonly=True)
    category = fields.Selection([
        ('raw', 'Raw Material'),
        ('processed', 'Processed/WIP')
    ], readonly=True)
    component_type = fields.Selection([
        ('body', 'Body'),
        ('trim', 'Trim'),
        ('fastener', 'Fasteners'),
        ('sealing', 'Sealing'),
        ('accessory', 'Accessories'),
        ('consumable', 'Consumables'),
        ('other', 'Other')
    ], readonly=True)
    
    existing_variants = fields.Integer(
        'Existing',
        compute='_compute_variant_info'
    )
    
    @api.depends('product_id')
    def _compute_variant_info(self):
        for line in self:
            if line.product_id:
                line.existing_variants = len(line.product_id.product_variant_ids)
            else:
                line.existing_variants = 0


class ProductVariantWizardAttribute(models.TransientModel):
    _name = 'product.variant.wizard.attribute'
    _description = 'Attribute Selection'
    
    wizard_id = fields.Many2one('product.variant.wizard', required=True, ondelete='cascade')
    attribute_id = fields.Many2one('product.attribute', 'Attribute', required=True)
    value_ids = fields.Many2many('product.attribute.value', string='Values')
    
    value_count = fields.Integer('Selected', compute='_compute_counts')
    available_value_count = fields.Integer('Available', compute='_compute_counts')
    required = fields.Boolean('Required', default=True)
    attribute_line_id = fields.Many2one('product.template.attribute.line')
    
    @api.depends('value_ids', 'attribute_id')
    def _compute_counts(self):
        for line in self:
            line.value_count = len(line.value_ids)
            if line.attribute_id:
                available_values = self.env['product.attribute.value'].search_count([
                    ('attribute_id', '=', line.attribute_id.id)
                ])
                line.available_value_count = available_values
            else:
                line.available_value_count = 0
                


    @api.depends('category_template_id', 'product_template_id')
    def _compute_template_lines(self):
        for wizard in self:
            if wizard.category_template_id and not wizard.template_line_ids:
                lines = []
                for template_line in wizard.category_template_id.template_line_ids:
                    if template_line.product_id:
                        # Check if specific product template is selected
                        if wizard.product_template_id and template_line.product_id != wizard.product_template_id:
                            continue
                            
                        lines.append((0, 0, {
                            'template_line_id': template_line.id,
                            'product_id': template_line.product_id.id,
                            'name': template_line.name,
                            'level': template_line.level,
                            'category': template_line.category,
                            'component_type': template_line.component_type,
                            'selected': True,
                        }))
                wizard.template_line_ids = lines
                
                # Initialize attribute lines WITHOUT values
                wizard._initialize_empty_attributes()
    
    def _initialize_empty_attributes(self):
        """Initialize attribute lines with empty values"""
        self.ensure_one()
        
        # Get all unique attributes from selected template lines
        attributes = self.env['product.attribute']
        
        for line in self.template_line_ids:
            if line.material_attribute_ids:
                attributes |= line.material_attribute_ids
        
        # Create attribute lines with NO values selected
        attribute_lines = []
        for attribute in attributes:
            attribute_lines.append((0, 0, {
                'attribute_id': attribute.id,
                'value_ids': [(5, 0, 0)],  # Clear all values
            }))
        
        self.attribute_line_ids = attribute_lines
    
    def load_all_values(self):
        """Load all available values for each attribute"""
        self.ensure_one()
        
        for attr_line in self.attribute_line_ids:
            all_values = self.env['product.attribute.value'].search([
                ('attribute_id', '=', attr_line.attribute_id.id)
            ])
            attr_line.value_ids = [(6, 0, all_values.ids)]
        
        return {'type': 'ir.actions.do_nothing'}
    
    def load_common_values(self):
        """Load only common/frequently used values"""
        self.ensure_one()
        
        # Define common values per attribute (customize as needed)
        common_values_map = {
            'Size': ['1/2"', '3/4"', '1"', '1-1/2"', '2"'],
            'Material': ['SS316', 'SS304', 'Carbon Steel'],
            'Pressure': ['150#', '300#', '600#'],
            # Add more as needed
        }
        
        for attr_line in self.attribute_line_ids:
            attr_name = attr_line.attribute_id.name
            
            if attr_name in common_values_map:
                common_value_names = common_values_map[attr_name]
                values = self.env['product.attribute.value'].search([
                    ('attribute_id', '=', attr_line.attribute_id.id),
                    ('name', 'in', common_value_names)
                ])
                attr_line.value_ids = [(6, 0, values.ids)]
        
        return {'type': 'ir.actions.do_nothing'}
    
    def clear_all_values(self):
        """Clear all selected attribute values"""
        self.attribute_line_ids.write({'value_ids': [(5, 0, 0)]})
        return {'type': 'ir.actions.do_nothing'}