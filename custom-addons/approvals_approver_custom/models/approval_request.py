from odoo import _, api, fields, models, Command
from odoo.exceptions import ValidationError


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    approver_id = fields.Many2one('res.users', string='Approver')

    @api.depends('category_id', 'request_owner_id')
    def _compute_approver_ids(self):
        for request in self:
            if not request.category_id.custom_approver:
                return super()._compute_approver_ids()
            approver_id_vals = []
            approver_ids = []
            for approver in request.category_id.approver_ids:
                user = False
                if approver.category == 'director':
                    user = request.env.company.director
                    if not user:
                        raise ValidationError("Director not yet set. Please contact Administrator!")
                if approver.category == 'manager':
                    user = request.request_owner_id.department_id.manager_id.user_id
                    if not user:
                        raise ValidationError("Manager Dept not yet set. Please contact Administrator!")
                if approver.category == 'pic':
                    user = request.request_owner_id.department_id.pic_id
                    if not user:
                        raise ValidationError("PIC Dept not yet set. Please contact Administrator!")
                if approver.category == 'approver':
                    user = self.approver_id
                if approver.category == 'user':
                    user = approver.user_id
                if not user:
                    raise ValidationError("User not found. Please contact Administrator!")

                if user.id in approver_ids:
                    continue
                required = approver.required
                # current_approver = users_to_approver[user.id]
                # if current_approver and current_approver.required != required:
                #     approver_id_vals.append(Command.update(current_approver.id, {'required': required}))
                # elif not current_approver:
                sequence = (approver.sequence or 1000) if request.approver_sequence else 10
                approver_id_vals.append(Command.create({
                    'user_id': user.id,
                    'status': 'new',
                    'required': required,
                    'sequence': sequence,
                }))
                approver_ids.append(user.id)
            request.update({'approver_ids': approver_id_vals})


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    custom_approver = fields.Boolean('Custom Approver?')


class ApprovalCategoryApprover(models.Model):
    _inherit = 'approval.category.approver'

    category = fields.Selection([
        ('director', 'Director'),
        ('manager', 'Manager'),
        ('pic', 'PIC'),
        # ('hr', 'HR'),
        # ('hr_manager', 'HR Manager'),
        ('approver', 'Approver'),
        ('user', 'User'),
    ], string='Category', default='user', required=True)
    user_id = fields.Many2one('res.users', default=2)