# -*- coding: utf-8 -*-

from openerp.tools.convert import xml_import, escape, escape_re, convert_xml_import
from openerp.tools import convert
import logging
from lxml import etree
from openerp.tools import misc
from xml.dom import minidom
from xml.dom.minidom import Document
_logger = logging.getLogger(__name__)
import os.path
from openerp.tools.config import config


def _new_tag_menuitem(self, cr, rec, data_node=None, mode=None):
    rec_id = rec.get("id", '').encode('ascii')
    self._test_xml_id(rec_id)
    m_l = map(escape, escape_re.split(rec.get("name", '').encode('utf8')))

    values = {'parent_id': False}
    if rec.get('parent', False) is False and len(m_l) > 1:
        # No parent attribute specified
        # and the menu name has several menu components,
        # try to determine the ID of the parent according to menu path
        pid = False
        res = None
        values['name'] = m_l[-1]
        # last part is our name, not a parent
        m_l = m_l[:-1]
        for idx, menu_elem in enumerate(m_l):
            if pid:
                cr.execute('select id '
                           'from ir_ui_menu '
                           'where parent_id=%s '
                           'and name=%s', (pid, menu_elem))
            else:
                cr.execute('select id '
                           'from ir_ui_menu '
                           'where parent_id '
                           'is null and name=%s', (menu_elem,))
            res = cr.fetchone()
            if res:
                pid = res[0]
            else:
                # the menuitem does't exist but we are in branch (not a leaf)
                _logger.warning('Warning no ID '
                                'for submenu %s of menu %s !',
                                menu_elem, str(m_l))
                pid = self.pool['ir.ui.menu'].create(
                    cr, self.uid, {'parent_id': pid, 'name': menu_elem})
        values['parent_id'] = pid
    else:
        # The parent attribute was specified,
        # if non-empty determine its ID, otherwise
        # explicitly make a top-level menu
        if rec.get('parent'):
            menu_parent_id = self.id_get(cr, rec.get('parent', ''))
        else:
            # we get here with <menuitem parent="">,
            # explicit clear of parent, or
            # if no parent attribute at all but menu name is not a menu path
            menu_parent_id = False
        values = {'parent_id': menu_parent_id}
        if rec.get('name'):
            values['name'] = rec.get('name')
        try:
            res = [self.id_get(cr, rec.get('id', ''))]
        except:
            res = None
    action_type = False
    action_id = False
    if rec.get('action'):
        a_action = rec.get('action', '').encode('utf8')

        # determine the type of action
        action_type, action_id = self.model_id_get(cr, a_action)
        # keep only type part
        action_type = action_type.split('.')[-1]

        if not values.get('name') and action_type in (
                'act_window', 'wizard', 'url', 'client', 'server'):
            a_table = 'ir_act_%s' % action_type.replace('act_', '')
            cr.execute('select name from "%s" where id=%%s' % a_table, (
                int(action_id),))
            resw = cr.fetchone()
            if resw:
                values['name'] = resw[0]

    if not values.get('name'):
        # ensure menu has a name
        values['name'] = rec_id or '?'

    if rec.get('sequence'):
        values['sequence'] = int(rec.get('sequence'))

    if rec.get('groups'):
        g_names = rec.get('groups', '').split(',')
        groups_value = []
        for group in g_names:
            if group.startswith('-'):
                group_id = self.id_get(cr, group[1:])
                groups_value.append((3, group_id))
            else:
                group_id = self.id_get(cr, group)
                groups_value.append((4, group_id))
        values['groups_id'] = groups_value

    if rec.get('invisible_groups'):
        invi_g_names = rec.get('invisible_groups', '').split(',')
        invi_groups_value = []
        for group in invi_g_names:
            if group.startswith('-'):
                group_id = self.id_get(cr, group[1:])
                invi_groups_value.append((3, group_id))
            else:
                group_id = self.id_get(cr, group)
                invi_groups_value.append((4, group_id))
        values['invisible_groups_ids'] = invi_groups_value

    pid = self.pool['ir.model.data']._update(
        cr, self.uid, 'ir.ui.menu', self.module, values, rec_id,
        noupdate=self.isnoupdate(data_node),
        mode=self.mode, res_id=res and res[0] or False)

    if rec_id and pid:
        self.idref[rec_id] = int(pid)

    if rec.get('action') and pid:
        action = "ir.actions.%s,%d" % (action_type, action_id)
        self.pool['ir.model.data'].ir_set(
            cr, self.uid, 'action', 'tree_but_open', 'Menuitem',
            [('ir.ui.menu', int(pid))], action, True, True, xml_id=rec_id)
    return 'ir.ui.menu', pid

xml_import._tag_menuitem = _new_tag_menuitem


def new_convert_xml_import(
        cr, module, xmlfile, idref=None,
        mode='init', noupdate=False, report=None):
    doc = etree.parse(xmlfile)
    xdoc = Document()
    rng_doc = minidom.parse(
        os.path.join(config['root_path'], 'import_xml.rng'))
    rng_element_tags = rng_doc.getElementsByTagName('rng:element')
    for rng_element in rng_element_tags:
        attributes = dict(rng_element.attributes)
        if attributes.get('name', False) \
                and attributes['name'].value == 'menuitem':
            new_optional = xdoc.createElement('rng:optional')
            new_attribute = xdoc.createElement('rng:attribute')
            new_attribute.setAttribute('name', 'invisible_groups')

            new_optional.appendChild(new_attribute)
            rng_element.appendChild(new_optional)

    relaxng = etree.RelaxNG(
        etree.fromstring(rng_doc.toxml()))
    try:
        relaxng.assert_(doc)
    except Exception:
        _logger.error('The XML file does not fit the required schema !')
        _logger.error(misc.ustr(relaxng.error_log.last_error))
        raise

    if idref is None:
        idref = {}
    obj = xml_import(cr, module, idref, mode, report=report, noupdate=noupdate)
    obj.parse(doc.getroot(), mode=mode)
    return True

convert.convert_xml_import = new_convert_xml_import