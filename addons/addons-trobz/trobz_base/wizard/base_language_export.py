# -*- coding: utf-8 -*-
##############################################################################

import base64
import cStringIO

from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.misc import get_iso_codes
import csv
import os
import logging
import tarfile
import tempfile
from os.path import join

NEW_LANG_KEY = '__new__'
_logger = logging.getLogger(__name__)


def trans_export(lang, modules, buffer_data, format_type, cr, context={}):

    def _process(format_type, modules, rows, buffer_data, lang, context={}):
        context = context or {}
        export_type = context.get('export_type', '')
        if format_type == 'csv':
            writer = csv.writer(buffer_data, 'UNIX')
            # write header first
            writer.writerow(
                ("module", "type", "name", "res_id", "src", "value"))
            for module, type_data, name, res_id, src, trad, comments in rows:
                # Comments are ignored by the CSV writer
                writer.writerow((module, type_data, name, res_id, src, trad))
        elif format_type == 'po':
            writer = tools.TinyPoFile(buffer_data)
            writer.write_infos(modules)

            # we now group the translations by source. That means one
            # translation per source.
            grouped_rows = {}

            for module, type_data, name, res_id, src, trad, comments in rows:
                comments = ''
                row = grouped_rows.setdefault(src, {})
                row.setdefault('modules', set()).add(module)

                if not row.get('translation') and trad != src:
                    row['translation'] = trad
                row.setdefault('tnrs', []).append((type_data, name, res_id))
                row.setdefault('comments', set()).update(comments)

            rows = grouped_rows.items()
            rows.sort()
            trans = 'translated'
            not_trans = 'not_yet_translated'
            for res in rows:
                src, row = res
                if not lang:
                    # translation template, so no translation value
                    row['translation'] = ''
                elif not row.get('translation'):
                    row['translation'] = src

                if export_type == trans and row['translation'] == src:
                    continue
                if export_type == not_trans and row['translation'] != src:
                    continue
                writer.write(
                    row['modules'],
                    row['tnrs'],
                    src,
                    row['translation'],
                    row['comments'])

        elif format_type == 'tgz':
            rows_by_module = {}
            for row in rows:
                module = row[0]
                rows_by_module.setdefault(module, []).append(row)
            tmpdir = tempfile.mkdtemp()
            for mod, modrows in rows_by_module.items():
                tmpmoddir = join(tmpdir, mod, 'i18n')
                os.makedirs(tmpmoddir)
                pofilename = (lang if lang else mod) + \
                    ".po" + ('t' if not lang else '')
                buf = file(join(tmpmoddir, pofilename), 'w')
                _process('po', [mod], modrows, buf, lang)
                buf.close()

            tar = tarfile.open(fileobj=buffer_data, mode='w|gz')
            tar.add(tmpdir, '')
            tar.close()

        else:
            raise Exception(_('Unrecognized extension: must be one of '
                              '.csv, .po, or .tgz (received .%s).'
                              % format_type))

    trans_lang = lang
    if not trans_lang and format_type == 'csv':
        # CSV files are meant for translators and they need a starting point,
        # so we at least put the original term in the translation column
        trans_lang = 'en_US'
    translations = tools.trans_generate(lang, modules, cr)
    modules = set([t[0] for t in translations[1:]])
    _process(format_type, modules, translations,
             buffer_data, lang, context=context)
    del translations


class base_language_export(osv.TransientModel):
    _inherit = "base.language.export"

    _columns = {
        'export_type': fields.selection([('all', 'All'),
                                         ('translated', 'Translated'),
                                         ('not_yet_translated', 'Not Yet \
                                         Translated')], string='Export Type',
                                        required=True)
    }

    _defaults = {
        'export_type': 'all',
    }

    def act_getfile(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        lang = this.lang if this.lang != NEW_LANG_KEY else False
        mods = map(lambda m: m.name, this.modules) or ['all']
        mods.sort()
        buf = cStringIO.StringIO()
        trans_export(
            lang, mods, buf, this.format, cr,
            context={'export_type': this.export_type})
        filename = 'new'
        if lang:
            filename = get_iso_codes(lang)
        elif len(mods) == 1:
            filename = mods[0]
        this.name = "%s.%s" % (filename, this.format)
        out = base64.encodestring(buf.getvalue())
        buf.close()
        self.write(cr, uid, ids, {'state': 'get',
                                  'data': out,
                                  'name': this.name}, context=context)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'base.language.export',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
