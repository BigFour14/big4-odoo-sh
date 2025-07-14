# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class CashierExpense(models.Model):
    _name = 'cashier.expense'
    _description = 'Cashier Expense'
    _order = 'date desc, id desc'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Reference', 
        required=True, 
        copy=False,
        readonly=True, 
        default=lambda self: _('New'),
        tracking=True
    )
    expense_name = fields.Char(
        string='Expense Name', 
        required=True,
        tracking=True,
        translate=True
    )
    amount = fields.Float(
        string='Amount', 
        required=True,
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    date = fields.Date(
        string='Date', 
        default=fields.Date.today, 
        required=True,
        tracking=True
    )
    description = fields.Text(
        string='Description',
        translate=True
    )
    receipt_image = fields.Binary(
        string='Receipt Image',
        help='Upload receipt image for this expense'
    )
    receipt_filename = fields.Char(
        string='Receipt Filename'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)
    
    # Relations
    cashbox_id = fields.Many2one(
        'account.journal',
        string='Cashbox',
        domain=[('type', '=', 'cash')],
        required=True
    )
    account_move_id = fields.Many2one(
        'account.move',
        string='Journal Entry',
        readonly=True
    )
    expense_account_id = fields.Many2one(
        'account.account',
        string='Expense Account',
        required=True,
        domain=[('account_type', 'in', ['expense', 'asset_current'])]
    )
    
    # User tracking
    user_id = fields.Many2one(
        'res.users',
        string='Created by',
        default=lambda self: self.env.user,
        readonly=True
    )
    approved_by = fields.Many2one(
        'res.users',
        string='Approved by',
        readonly=True
    )
    approved_date = fields.Datetime(
        string='Approved Date',
        readonly=True
    )

    def write(self, vals):
        """Override write to prevent editing approved expenses"""
        # منع التعديل في المصروفات الموافق عليها
        for record in self:
            if record.state == 'approved' and record.account_move_id:
                # السماح فقط بتغيير الحالة والملاحظات
                allowed_fields = ['state', 'description']
                if any(field not in allowed_fields for field in vals.keys()):
                    raise UserError(_('Cannot modify approved expenses. Journal entry already posted.'))
        
        return super(CashierExpense, self).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('cashier.expense') or _('New')
        return super(CashierExpense, self).create(vals)

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_('Amount must be greater than zero.'))

    def action_submit(self):
        """Submit expense for approval"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft expenses can be submitted.'))
            record.state = 'submitted'
            record.message_post(
                body=_('Expense submitted for approval.'),
                message_type='notification'
            )

    def action_approve(self):
        """Approve expense and create journal entry"""
        for record in self:
            if record.state != 'submitted':
                raise UserError(_('Only submitted expenses can be approved.'))
            
            # Create journal entry
            move_vals = record._prepare_move_vals()
            move = self.env['account.move'].create(move_vals)
            move.action_post()
            
            record.write({
                'state': 'approved',
                'account_move_id': move.id,
                'approved_by': self.env.user.id,
                'approved_date': fields.Datetime.now()
            })
            record.message_post(
                body=_('Expense approved and journal entry created.'),
                message_type='notification'
            )

    def action_reject(self):
        """Reject expense"""
        for record in self:
            if record.state not in ['submitted']:
                raise UserError(_('Only submitted expenses can be rejected.'))
            record.state = 'rejected'
            record.message_post(
                body=_('Expense rejected.'),
                message_type='notification'
            )

    def action_reset_to_draft(self):
        """Reset to draft"""
        for record in self:
            if record.account_move_id:
                raise UserError(_('Cannot reset to draft. Journal entry already created.'))
            record.state = 'draft'

    def _prepare_move_vals(self):
        """Prepare journal entry values"""
        self.ensure_one()
        
        move_lines = []
        
        # Debit line (expense)
        move_lines.append((0, 0, {
            'name': self.expense_name,
            'account_id': self.expense_account_id.id,
            'debit': self.amount,
            'credit': 0.0,
            'currency_id': self.currency_id.id,
        }))
        
        # Credit line (cash)
        move_lines.append((0, 0, {
            'name': self.expense_name,
            'account_id': self.cashbox_id.default_account_id.id,
            'debit': 0.0,
            'credit': self.amount,
            'currency_id': self.currency_id.id,
        }))
        
        return {
            'journal_id': self.cashbox_id.id,
            'date': self.date,
            'ref': self.name,
            'line_ids': move_lines,
            'currency_id': self.currency_id.id,
        }

    def action_print_receipt(self):
        """Print receipt"""
        return self.env.ref('bigfour_cashbox.action_report_cashier_expense_receipt').report_action(self)

    def unlink(self):
        for record in self:
            if record.state == 'approved':
                raise UserError(_('Cannot delete approved expenses.'))
        return super(CashierExpense, self).unlink()

