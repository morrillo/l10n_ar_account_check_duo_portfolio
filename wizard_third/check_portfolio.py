# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2012 OpenERP - Team de Localización Argentina.
# https://launchpad.net/~openerp-l10n-ar-localization
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields
from tools.translate import _
import netsvc
from datetime import date

class account_check_portfolio(osv.osv_memory):
    _name = 'account.check.portfolio'

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
    }

    def action_deposit(self, cr, uid, ids, context=None):
        third_check = self.pool.get('account.third.check')
        wf_service = netsvc.LocalService('workflow')

        move_line = self.pool.get('account.move.line')

        wizard = self.browse(cr, uid, ids[0], context=context)

        if context is None:
            context = {}
        record_ids = context.get('active_ids', [])

        check_objs = third_check.browse(cr, uid, record_ids, context=context)

        for check in check_objs:
                     
            if check.state != 'draft':
                raise osv.except_osv('Check %s selected error' % (check.number),
                    'The selected checks must to be in draft state.' )
    
            else:
		parameter_id = self.pool.get('ir.config_parameter').search(cr,uid,[('key','=','THIRD_CHECK_JOURNAL')])
		if not parameter_id:
			raise osv.except_osv('THIRD_CHECK_JOURNAL parameter not configured. Not being able to move check/s to portfolio.')
		else:
			parameter_value = self.pool.get('ir.config_parameter').read(cr,uid,parameter_id,['value'])
			journal_id = self.pool.get('account.journal').search(cr,uid,[('code','=',parameter_value[0]['value'])])
			if not journal_id:
				raise osv.except_osv('%s not configured. Not being able to move check/s to portfolio.'%(parameter_value[0]['value']))

			journal_sequence_id = self.pool.get('account.journal').read(cr,uid,journal_id,['sequence_id'])

	                name = self.pool.get('ir.sequence').next_by_id(cr, uid, journal_sequence_id[0]['sequence_id'][0], context=context)
			
			debit_account_id = self.pool.get('account.account').search(cr,uid,[('name','=','Valores a depositar')])
			credit_account_id = self.pool.get('account.account').search(cr,uid,[('name','=','Deudores por ventas')])

			period_id = self.pool.get('account.period').search(cr,uid,[('date_start','<=',date.today()),('date_stop','>=',date.today())])

	                move_id = self.pool.get('account.move').create(cr, uid, {
        	                'name': name,
                	        'journal_id': journal_id[0],
                        	'state': 'draft',
				'period_id': period_id[0],
        	                'date': date.today(),
                	        'ref': 'Check Deposit Nr. ' + check.number,
	                })
               
			 
        	        move_line.create(cr, uid, {
                	        'name': name,
	                        'centralisation': 'normal',
        	                'account_id': debit_account_id[0],
                	        'move_id': move_id,
        	                'journal_id': journal_id[0],
				'period_id': period_id[0],
                	        'date': date.today(),
                        	'debit': check.amount,
	                        'credit': 0.0,
        	                'ref': 'Check Deposit Nr. ' + check.number,
                	        'state': 'valid',
	                })
        	        move_line.create(cr, uid, {
                	        'name': name,
                        	'centralisation': 'normal',
	                        'account_id': credit_account_id[0],
        	                'move_id': move_id,
                	        'journal_id': journal_id[0],
				'period_id': period_id[0],
	                        'date': date.today(),
        	                'debit': 0.0,
                	        'credit': check.amount,
                        	'ref': 'Check Deposit Nr. ' + check.number,
	                        'state': 'valid',
        	        })
               
		        vals_check = {
		                'source_partner_id': wizard.partner_id.id,
		                'state': 'holding',
		                'change_date': date.today(),
                		}
		        return_id = self.pool.get('account.third.check').write(cr,uid,check.id,vals_check)
 
                	# wf_service.trg_validate(uid, 'account.third.check', check.id,'holding', cr)
	                self.pool.get('account.move').write(cr, uid, [move_id], {'state': 'posted'})

        return {}

account_check_portfolio()
