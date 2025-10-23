from odoo import _, api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    source = fields.Selection(selection_add=[('pq', 'Price Query')], string='Source', ondelete={'pq': 'cascade'})
    pq_line_id = fields.Many2one('price.query.line', string='PQ Line')
    parent_id = fields.Many2one('mrp.production', string='Parent')
    component_id = fields.Many2one('stock.move', string='Component')

    def action_show_child(self):
        self.ensure_one()
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['domain'] = [('parent_id', '=', self.id)]
        return action

    def generate_mrp_production_child(self):
        self.ensure_one()
        components = self.move_raw_ids.filtered(lambda line: line.is_child)
        for component in components:
            self.env['mrp.production'].create({
                'parent_id': self.id,
                'source': self.source,
                'pq_line_id': self.pq_line_id.id,
                'order_id': self.order_id.id,
                'company_id': self.company_id.id,
                'product_id': component.product_id.id,
                'component_id': component.id,
            })

    # def generate_mo_material(self):
    #     res = super(MrpProduction, self).generate_mo_material()
    #     if self.ability == 'indent' and self.source == 'pq' and self.pq_line_id:
    #         self.write({
    #             'line_ids': [(0,0,{
    #                 'part_id': part.part_id.id,
    #                 'material_id': part.material_id.id,
    #                 'product_id': part.product_id.id,
    #                 'product_tmpl_id': part.product_tmpl_id.id,
    #                 'init_qty': part.product_qty,
    #                 'product_uom_id': part.product_uom_id.id,
    #                 'total_qty': self.product_qty*part.product_qty,
    #             }) for part in self.pq_line_id.bom_ids ],
    #         })
    #     return res


class MRPBom(models.Model):
    _inherit = 'mrp.bom'

    query_id = fields.Many2one('price.query.line', string='Query')


class MRPBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    query_line_id = fields.Many2one('price.query.line', string='Query')


class StockMove(models.Model):
    _inherit = 'stock.move'

    is_child = fields.Boolean('Is Child?', default=True)