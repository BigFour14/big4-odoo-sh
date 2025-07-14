# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class CashboxPayment(models.Model):

    def create_payment_entry(self):
        for rec in self:
            if rec.bill_id and rec.state == 'approved':
                payment_vals = {
                    'payment_type': 'outbound',
                    'partner_type': 'supplier',
                    'partner_id': rec.vendor_id.id,
                    'amount': rec.amount,
                    'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
                    'journal_id': self.env['account.journal'].search([('type','=','cash')], limit=1).id,
                    'ref': rec.name,
                }
                payment = self.env['account.payment'].create(payment_vals)
                payment.action_post()
                rec.bill_id.js_assign_outstanding_line(payment.move_id.line_ids.filtered(lambda l: l.account_id == rec.bill_id.partner_id.property_account_payable_id))

    _name = 'cashbox.payment'
    _description = 'Cashbox Vendor Payment'
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
    vendor_id = fields.Many2one(
        'res.partner', 
        string='Vendor', 
        required=True,
        domain=[('supplier_rank', '>', 0)],
        tracking=True
    )
    bill_id = fields.Many2one(
        'account.move',
        string='Vendor Bill',
        domain=[('move_type', '=', 'in_invoice'), ('state', '=', 'posted')],
        tracking=True
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
        string='Payment Date', 
        default=fields.Date.today, 
        required=True,
        tracking=True
    )
    description = fields.Text(
        string='Notes',
        translate=True
    )
    receipt_image = fields.Binary(
        string='Receipt Photo',
        help='Upload receipt photo for this payment'
    )
    receipt_filename = fields.Char(
        string='Receipt Filename'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Relations
    cashbox_id = fields.Many2one(
        'account.journal',
        string='Cashbox',
        domain=[('type', '=', 'cash')],
        required=True
    )
    payment_id = fields.Many2one(
        'account.payment',
        string='Payment',
        readonly=True
    )
    
    # User tracking
    user_id = fields.Many2one(
        'res.users',
        string='Created by',
        default=lambda self: self.env.user,
        readonly=True
    )
    paid_by = fields.Many2one(
        'res.users',
        string='Paid by',
        readonly=True
    )
    paid_date = fields.Datetime(
        string='Paid Date',
        readonly=True
    )

    # Computed fields
    remaining_amount = fields.Float(
        string='Remaining Amount',
        compute='_compute_remaining_amount',
        store=True
    )

    @api.depends('bill_id', 'bill_id.amount_residual')
    def _compute_remaining_amount(self):
        for record in self:
            if record.bill_id:
                record.remaining_amount = record.bill_id.amount_residual
            else:
                record.remaining_amount = 0.0

    def write(self, vals):
        """Override write to prevent editing paid payments"""
        # منع التعديل في المدفوعات المكتملة
        for record in self:
            if record.state == 'paid' and record.payment_id:
                # السماح فقط بتغيير الحالة والملاحظات
                allowed_fields = ['state', 'description']
                if any(field not in allowed_fields for field in vals.keys()):
                    raise UserError(_('Cannot modify paid payments. Payment already posted.'))
        
        return super(CashboxPayment, self).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('cashbox.payment') or _('New')
        return super(CashboxPayment, self).create(vals)

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_('Amount must be greater than zero.'))

    @api.constrains('amount', 'bill_id')
    def _check_payment_amount(self):
        for record in self:
            if record.bill_id and record.amount > record.bill_id.amount_residual:
                raise ValidationError(_('Payment amount cannot exceed the remaining bill amount.'))

    @api.onchange('bill_id')
    def _onchange_bill_id(self):
        if self.bill_id:
            self.vendor_id = self.bill_id.partner_id
            self.amount = self.bill_id.amount_residual
            self.currency_id = self.bill_id.currency_id

    def action_submit(self):
        """Submit payment for approval"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft payments can be submitted.'))
            record.state = 'submitted'
            record.message_post(
                body=_('Payment submitted for approval.'),
                message_type='notification'
            )

    def action_pay(self):
        """Process payment"""
        for record in self:
            if record.state != 'submitted':
                raise UserError(_('Only submitted payments can be processed.'))
            
            # Create payment
            payment_vals = record._prepare_payment_vals()
            payment = self.env['account.payment'].create(payment_vals)
            payment.action_post()
            
            record.write({
                'state': 'paid',
                'payment_id': payment.id,
                'paid_by': self.env.user.id,
                'paid_date': fields.Datetime.now()
            })
            record.message_post(
                body=_('Payment processed successfully.'),
                message_type='notification'
            )

    def action_cancel(self):
        """Cancel payment"""
        for record in self:
            if record.state == 'paid':
                raise UserError(_('Cannot cancel paid payments.'))
            record.state = 'cancelled'
            record.message_post(
                body=_('Payment cancelled.'),
                message_type='notification'
            )

    def action_reset_to_draft(self):
        """Reset to draft"""
        for record in self:
            if record.payment_id:
                raise UserError(_('Cannot reset to draft. Payment already processed.'))
            record.state = 'draft'

    def _prepare_payment_vals(self):
        """Prepare payment values"""
        self.ensure_one()
        
        # الحقول الأساسية المطلوبة فقط لـ account.payment في Odoo 18
        payment_vals = {
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'partner_id': self.vendor_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'date': self.date,
            'journal_id': self.cashbox_id.id,
        }
        
        return payment_vals

    def action_pay(self):
        """Process payment and reconcile with bill"""
        for record in self:
            if record.state != 'submitted':
                raise UserError(_('Only submitted payments can be processed.'))
            
            # Create payment
            payment_vals = record._prepare_payment_vals()
            payment = self.env['account.payment'].create(payment_vals)
            payment.action_post()
            
            # ربط الدفعة بالفاتورة الأصلية - استخدام move_id بدلاً من line_ids
            if record.bill_id and payment.move_id:
                # البحث عن سطور الفاتورة والدفعة للتسوية
                bill_lines = record.bill_id.line_ids.filtered(lambda l: l.account_id.account_type == 'liability_payable')
                payment_lines = payment.move_id.line_ids.filtered(lambda l: l.account_id.account_type == 'liability_payable')
                
                # تسوية السطور
                if bill_lines and payment_lines:
                    (bill_lines + payment_lines).reconcile()
            
            record.write({
                'state': 'paid',
                'payment_id': payment.id,
                'paid_by': self.env.user.id,
                'paid_date': fields.Datetime.now()
            })
            record.message_post(
                body=_('Payment processed and reconciled with bill successfully.'),
                message_type='notification'
            )

    def action_print_receipt(self):
        """Print receipt"""
        return self.env.ref('bigfour_cashbox.action_report_cashbox_payment_receipt').report_action(self)

    def unlink(self):
        for record in self:
            if record.state == 'paid':
                raise UserError(_('Cannot delete paid payments.'))
        return super(CashboxPayment, self).unlink()

