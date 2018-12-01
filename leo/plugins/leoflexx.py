# -*- coding: utf-8 -*-
#@+leo-ver=5-thin
#@+node:ekr.20181103094900.1: * @file leoflexx.py
#@@first
#@@language python
#@@tabwidth -4
#@+<< flexx.py docstring >>
#@+node:ekr.20181122215342.1: ** << flexx.py docstring >>
#@@language md
#@@wrap
'''
flexx.py: A stand-alone prototype for Leo using flexx.

This file, not leowapp.py or leoflexx.jx, is the main line of the LeoWapp project.
https://github.com/leo-editor/leo-editor/issues/1005

# Prerequites

Install flexx: https://flexx.readthedocs.io/en/stable/start.html

# Running

You should run leoflexx.py from a console:

    python <path to>leoflexx.py --flexx-webruntime=firefox-browser​

The --flex-webruntime command-line arg is optional. If omitted, you'll use
the webruntime environment.

You should see the flexx (Tornado) server start up in the console.
Something that looks like Leo should appear in the browser.

The startup code uses Leo's bridge module to load unitTest.leo. You should
see the top-level nodes of this file in the tree pane. Everything you see
is real, and most of it is "live".

# The tree pane

The tree pane is mostly functional, but you may see "can't happen"
messages. I'm working on it.

- Selecting a node selects the proper body text.

- Moving nodes with Ctrl-U/Ctrl-D work.

- You can expand/contract nodes by clicking on them.

- You can *not* edit headlines. It will take some doing to make this
  happen, but a workaround is coming soon.
  
# Key handling

Many keystrokes work.

- Ctrl-S will save the file but I don't recommend doing that yet!

- Alt-X does not work yet.

- Ctrl-F does not work yet: the browser (Mozilla) grabs the keystroke.

# Minibuffer Easter Eggs

You can execute test commands by clicking in the Minibuffer, typing the
command and hitting return.

See app.do_command (in this file) for a full list. The notable commands:

- cls: clears the console.

- unit: runs all unit tests. They all pass for me.

Coming soon:

- mini: Simulate Alt-x. You will be prompted for a minibuffer command.

- find: Simulate Ctrl-F in minibuffer find mode.

- head: Simulate editing the headline. You will be prompted for headline
  text. Hitting return will replace c.p.h by what you type.

'''
#@-<< flexx.py docstring >>
# pylint: disable=logging-not-lazy
#@+<< leoflexx imports >>
#@+node:ekr.20181113041314.1: ** << leoflexx imports >>
import leo.core.leoGlobals as g
    # **Note**: JS code can not use g.trace, g.callers.
import leo.core.leoBridge as leoBridge
import leo.core.leoFrame as leoFrame
import leo.core.leoGui as leoGui
import leo.core.leoMenu as leoMenu
import leo.core.leoNodes as leoNodes
import leo.core.leoTest as leoTest
from flexx import flx
import difflib
import re
import time
assert re and time
    # Suppress pyflakes complaints
#@-<< leoflexx imports >>
debug_body = True
debug_changed = False # Trace c.changed()
debug_focus = False # puts 'focus' in g.app.debug.
debug_keys = True # puts 'keys' in g.app.debug.
debug_redraw = False
debug_select = False
debug_tree = False
verbose_debug_tree = False
use_ace = True # False: use Code Mirror.
warnings_only = False # False is better for debugging.
print('\nuse_ace', use_ace, '\n')
# For now, always include ace assets: they are used in the log, etc.
#@+<< ace assets >>
#@+node:ekr.20181111074958.1: ** << ace assets >>
# Assets for ace JS editor.
base_url = 'https://cdnjs.cloudflare.com/ajax/libs/ace/1.2.6/'
flx.assets.associate_asset(__name__, base_url + 'ace.js')
flx.assets.associate_asset(__name__, base_url + 'mode-python.js')
flx.assets.associate_asset(__name__, base_url + 'theme-solarized_dark.js')
#@-<< ace assets >>
if not use_ace:
    #@+<< CodeMirror assets >>
    #@+node:ekr.20181130082321.1: ** << CodeMirror assets >>
    # Assets for CodeMirror JS editor.
    base_url = 'https://cdnjs.cloudflare.com/ajax/libs/codemirror/'
    flx.assets.associate_asset(__name__, base_url + '5.21.0/codemirror.min.css')
    flx.assets.associate_asset(__name__, base_url + '5.21.0/codemirror.min.js')
    flx.assets.associate_asset(__name__, base_url + '5.21.0/mode/python/python.js')
    flx.assets.associate_asset(__name__, base_url + '5.21.0/theme/solarized.css')
    flx.assets.associate_asset(__name__, base_url + '5.21.0/addon/selection/active-line.js')
    flx.assets.associate_asset(__name__, base_url + '5.21.0/addon/edit/matchbrackets.js')
    #@-<< CodeMirror assets >>
#@+others
#@+node:ekr.20181121040901.1: **  top-level functions
#@+node:ekr.20181122102523.1: *3* banner
def banner(s):
    '''Print s so it stands out.'''
    if g.unitTesting:
        return
    if debug_focus or debug_keys or debug_tree:
        print('')
        print(s)
        print('')
#@+node:ekr.20181121091633.1: *3* dump_event
def dump_event (ev):
    '''Print a description of the event.'''
    id_ = ev.source.title or ev.source.text
    kind = '' if ev.new_value else 'un-'
    s = kind + ev.type
    message = '%s: %s' % (s.rjust(15), id_)
    print('dump_event: ' + message)
#@+node:ekr.20181121040857.1: *3* get_root
def get_root():
    '''
    Return the LeoBrowserApp instance.
    
    This is the same as self.root for any flx.Component.
    '''
    root = flx.loop.get_active_component().root
        # Only called at startup, so this will never be None.
    assert isinstance(root, LeoBrowserApp), repr(root)
    return root
#@+node:ekr.20181112165240.1: *3* info (deprecated)
def info (s):
    '''Send the string s to the flex logger, at level info.'''
    if not isinstance(s, str):
        s = repr(s)
    flx.logger.info('Leo: ' + s)
        # A hack: automatically add the "Leo" prefix so
        # the top-level suppression logic will not delete this message.
#@+node:ekr.20181103151350.1: *3* init
def init():
    # At present, leoflexx is not a true plugin.
    # I am executing leoflexx.py from an external script.
    return False
#@+node:ekr.20181113041410.1: *3* suppress_unwanted_log_messages (not used)
def suppress_unwanted_log_messages():
    '''
    Suppress the "Automatically scrolling cursor into view" messages by
    *allowing* only important messages.
    '''
    allowed = r'(Traceback|Critical|Error|Leo|Session|Starting|Stopping|Warning)'
    pattern = re.compile(allowed, re.IGNORECASE)
    flx.set_log_level('INFO', pattern)
#@+node:ekr.20181115071559.1: ** Py side: App & wrapper classes
#@+node:ekr.20181127151027.1: *3* class AceWrapper (StringTextWrapper)
class AceWrapper (leoFrame.StringTextWrapper):
    '''
    A wrapper class that implements the high-level interface for the ace widget.
    
    See: https://ace.c9.io/#nav=api
    '''

    def __init__(self, c, name):
        assert name in ('body', 'log', 'minibuffer'), repr(name)
            # These are the Leo widgets that use ace widgets.
        super().__init__(c, name)
        assert self.c == c
        assert self.name == name
        self.tag = '(AceWrapper: %s)' % name
        self.vtag = '===== (AceWrapper: %s)' % name
        self.root = get_root()
        
    def flx_wrapper(self):
        if self.root.inited:
            w = self.root.main_window
            return getattr(w, self.name)
        # print(self.vtag, 'app not inited', g.callers())
        return g.NullObject()
        
    def setFocus(self):
        print(self.tag, 'setAllText')
        self.flx_wrapper().set_focus()

    # No need to override getters.
    #@+others
    #@+node:ekr.20181128101421.1: *4* AceWrapper.Selection Setters
    def seeInsertPoint(self):
        # print(self.tag, 'seeInsertPoint')
        self.flx_wrapper().see_insert_point()

    def selectAllText(self, insert=None):
        print(self.tag, 'selectAllText', repr(insert))
        self.sel = 0, len(self.s)
        self.ins = len(self.s) if insert is None else insert
        self.flx_wrapper().select_all_text()
        if insert is not None:
            self.flx_wrapper().set_insert_point(insert)

    def setInsertPoint(self, pos, s=None):
        # print(self.tag, 'setInsertPoint', pos, len(s) if s else 0, g.callers(1))
        self.virtualInsertPoint = pos
        self.ins = pos
        self.sel = pos, pos
        self.flx_wrapper().set_insert_point(pos)

    def setSelectionRange(self, i, j, insert=None):
        print(self.tag, 'setSelectionRange', i, j, repr(insert))
        self.sel = i, j
        self.flx_wrapper().set_selection_range(i, j)
        if insert is not None:
            self.ins = insert
            self.flx_wrapper().set_insert_point(insert)
    #@+node:ekr.20181127121642.1: *4* AceWrapper.Text Setters
    # Override StringTextWrapper setters to update flx.body widget.
    # Careful: do not set c.p.b or similar here.

    def appendText(self, s):
        trace = debug_keys and not g.unitTesting
        trace_changed = debug_changed and not g.unitTesting
        if trace: print(self.tag, 'appendText', len(s))
        c = self.c
        if s and self.name == 'body':
            if trace_changed: print('body.ace_wrapper.appendText: BODY CHANGED')
            c.setChanged()
        self.s = self.s + s
        self.ins = len(self.s)
        self.sel = self.ins, self.ins
        c.p.v.setBodyString(self.s)
        ### self.flx_wrapper().set_text(self.s)
        ### self.flx_wrapper().set_insert_point(self.ins)

    def delete(self, i, j=None):
        # trace = debug_keys and not g.unitTesting
        trace_changed = debug_changed and not g.unitTesting
        c = self.c
        print(self.tag, 'delete', repr(i), repr(j))
        super().delete(i, j)
        if self.name == 'body':
            if trace_changed:
                print('body.ace_wrapper.delete: BODY CHANGED')
            c.setChanged()
        c.p.v.setBodyString(self.s)
        ### self.flx_wrapper().set_text(self.s)
        ### self.flx_wrapper().set_insert_point(self.ins)

    def deleteTextSelection(self):
        trace = debug_keys and not g.unitTesting
        trace_changed = debug_changed and not g.unitTesting
        c = self.c
        if trace:
            print(self.tag, 'deleteTextSelection')
        i, j = super().getSelectionRange()
        if i == j:
            return
        if self.name == 'body':
            if trace_changed:
                print('body.ace_wrapper.deleteTextSelection.BODY CHANGED')
            c.setChanged()
        super().deleteTextSelection()
        c.p.v.setBodyString(self.s)
        ### self.flx_wrapper().set_text(self.s)
        ### self.flx_wrapper().set_insert_point(self.ins)
        
    def insert(self, i, s):
        '''Called from Leo's core on every keystroke.'''
        trace = debug_keys and not g.unitTesting
        trace_changed = debug_changed and not g.unitTesting
        c = self.c
        if not s:
            return
        if self.name == 'body':
            if trace_changed:
                print('body.ace_wrapper.insert: BODY CHANGED')
            c.setChanged()
        # doPlainChar, insertNewlineHelper, etc.
        self.s = self.s[: i] + s + self.s[i:]
        i += len(s)
        self.ins = i
        self.sel = i, i
        if trace:
            print(self.tag, 'insert', i, g.callers(1), 'self.s:', repr(g.truncate(self.s, 60)))
        c.p.v.setBodyString(self.s)
        self.flx_wrapper().insert(s)
        ### self.flx_wrapper().set_insert_point(self.ins)

    def setAllText(self, s):
        # Called by set_body_text_after_select.
        c = self.c
        if 0:
            print(self.tag, 'setAllText', g.callers(1))
            print(repr(g.truncate(s, 60)))
        self.s = s
        c.p.v.setBodyString(s)
        self.flx_wrapper().set_text(s)
        self.flx_wrapper().set_insert_point(self.ins)
    #@-others
#@+node:ekr.20181107052522.1: *3* class LeoBrowserApp
# pscript never converts flx.PyComponents to JS.

class LeoBrowserApp(flx.PyComponent):
    '''
    The browser component of Leo in the browser.

    **Important**: This is self.root for all flexx components.

    **Important**: This is *not* g.app. The LeoBride defines g.app.
    '''
    
    main_window = flx.ComponentProp(settable=True)

    def init(self):
        c, g = self.open_bridge()
        self.c = c
        self.gui = gui = LeoBrowserGui()
        assert gui.guiName() == 'browser'
            # Important: the leoTest module special cases this name.
        self.inited = False
            # Set by app.finish_create.
        self.tag = '(app wrapper)'
        # Inject the newly-created gui into g.app.
        g.app.gui = gui
        if debug_focus:
            g.app.debug.append('focus')
        if debug_keys:
            g.app.debug.append('keys')
        title = c.computeWindowTitle(c.mFileName)
        c.frame = gui.lastFrame = LeoBrowserFrame(c, title, gui)
            # Instantiate all wrappers first.
        # Force minibuffer find mode.
        c.findCommands.minibuffer_mode = True
        # Init all ivars
        self.create_gnx_to_vnode()
        self.old_flattened_outline = []
        self.old_redraw_dict = {}
        self.redraw_generation = 0
        # Create the main window and all its components.
        c.selectPosition(c.rootPosition()) ### A temp hack.
        c.contractAllHeadlines()
        main_window = LeoFlexxMainWindow()
        self._mutate('main_window', main_window)

    #@+others
    #@+node:ekr.20181126103604.1: *4*  app.Initing
    #@+node:ekr.20181114015356.1: *5* app.create_all_data
    def create_gnx_to_vnode(self):
        t1 = time.clock()
        self.gnx_to_vnode = { v.gnx: v for v in self.c.all_unique_nodes() }
            # This is likely the only data that ever will be needed.
        if 0:
            t2 = time.clock()
            print('app.create_all_data: %5.3f sec. %s entries' % (
                (t2-t1), len(list(self.gnx_to_vnode.keys()))))
        self.test_round_trip_positions()
    #@+node:ekr.20181124133513.1: *5* app.finish_create
    @flx.action
    def finish_create(self):
        '''
        Initialize all ivars and widgets.
        
        Called after all flx.Widgets have been fully inited!
        '''
        c, w = self.c, self.main_window
        self.inited = True
        # Monkey-patch the FindTabManager
        c.findCommands.ftm = g.NullObject()
        # Init g.app data
        self.old_flattened_outline = self.flatten_outline()
        self.old_redraw_dict = self.make_redraw_dict(c.p)
        self.redraw_generation = 0
        # Init the log pane.
        w.log.put('%s\n%s' % (g.app.signon, g.app.signon2))
        # Init the body pane.
        self.set_body_text()
        # Init the status line.
        self.set_status()
        # Init the tree.
        self.redraw(c.p)
        # Init the focus.
        # It's debatable:
        if 1:
            self.gui.set_focus(c, c.frame.tree)
            w.tree.set_focus()
        else:
            self.gui.set_focus(c, c.frame.body)
            w.body.set_focus()
        
    # These must be separate because they are called from the tree logic.

    @flx.action
    def set_status(self):
        c, w = self.c, self.main_window
        lt, rt = c.frame.statusLine.update(c.p.b, 0)
        w.status_line.update(lt, rt)
        
    @flx.action
    def set_body_text(self):
        c, w = self.c, self.main_window
        w.body.set_text(c.p.b)
    #@+node:ekr.20181117163223.1: *4* app.do_key
    # https://flexx.readthedocs.io/en/stable/ui/widget.html#flexx.ui.Widget.key_down
    # See Widget._create_key_event in flexx/ui/_widget.py:

    @flx.action
    def do_key (self, ev, ivar):
        '''
        LeoBrowserApp.do_key: The central key handler.
        
        Will be called *in addition* to any inner key handlers,
        unless the inner key handler calls e.preventDefault()
        '''
        trace = debug_keys and not g.unitTesting
        trace_master_key_handler = False
        c = self.c
        browser_wrapper = getattr(c.frame, ivar)
            # Essential: there is no way to pass the actual wrapper.
        #@+<< check browser_wrapper >>
        #@+node:ekr.20181129073812.1: *5* << check browser_wrapper >>
        assert isinstance(browser_wrapper, (
            LeoBrowserBody,
            ### LeoBrowserFrame,
            LeoBrowserLog,
            LeoBrowserMinibuffer,
            LeoBrowserStatusLine,
            LeoBrowserTree,
        )), repr(browser_wrapper)
        #@-<< check browser_wrapper >>
        key, mods = ev ['key'], ev ['modifiers']
            # ev is a dict, keys are type, source, key, modifiers
            # mods in ('Alt', 'Shift', 'Ctrl', 'Meta')
        #@+<< set char to the translated key name >>
        #@+node:ekr.20181129073905.1: *5* << set char to the translated key name >>
        d = {
            'ArrowDown':'Down',
            'ArrowLeft':'Left',
            'ArrowRight': 'Right',
            'ArrowUp': 'Up',
            'Enter': '\n', # For k.fullCommand, etc.
            'PageDown': 'Next',
            'PageUp': 'Prior',
        }
        char = d.get(key, key)
        if 'Ctrl' in mods:
            mods.remove('Ctrl')
            mods.append('Control')
        #@-<< set char to the translated key name >>
        binding = '%s%s' % (''.join(['%s+' % (z) for z in mods]), char)
        if trace:
            g.trace('%s from %s: %r c.p.h: %s' % (
                self.tag, browser_wrapper.tag, binding, c.p.h))
        #@+<< create key_event >>
        #@+node:ekr.20181129073734.1: *5* << create key_event >>
        # create the key event, but don't bother tracing it.
        old_debug = g.app.debug
        try:
            g.app.debug = []
            key_event = leoGui.LeoKeyEvent(c,
                char = char,
                binding = binding,
                event = { 'c': c },
                w = browser_wrapper,
            )
        finally:
            g.app.debug = old_debug
        #@-<< create key_event >>
        old_debug = g.app.debug
        try:
            if not trace_master_key_handler:
                g.app.debug = []
            c.k.masterKeyHandler(key_event)
        finally:
            g.app.debug = old_debug
    #@+node:ekr.20181122132345.1: *4* app.Drawing...
    #@+node:ekr.20181113042549.1: *5* app.action.redraw
    @flx.action
    def redraw (self, p):
        '''
        Send a **redraw list** to the tree.
        
        This is a recusive list lists of items (ap, gnx, headline) describing
        all and *only* the presently visible nodes in the tree.
        
        As a side effect, app.make_redraw_dict updates all internal dicts.
        '''
        trace = False and not g.unitTesting
        c = self.c
        p = p or c.p
        w = self.main_window
        #
        # Be careful: c.frame.redraw can be called before app.finish_create.
        if not w or not w.tree:
            return
        #
        # Profile times when all nodes are expanded.
        if 0:
            self.test_full_outline(p)
        #
        # Redraw only the visible nodes.
        t1 = time.clock()
        ap = self.p_to_ap(p)
        w.tree.select_ap(ap)
        redraw_dict = self.make_redraw_dict(p)
            # Needed to compare generations, even if there are no changes.
        new_flattened_outline = self.flatten_outline()
        redraw_instructions = self.make_redraw_list(
            self.old_flattened_outline, new_flattened_outline)
        w.tree.redraw_with_dict(redraw_dict, redraw_instructions)
            # At present, this does a full redraw using redraw_dict.
            # The redraw instructions are not used.
        # Set c.changed if there are any redraw instructions.
        if redraw_instructions:
            if debug_changed: print('app.redraw: C CHANGED')
            c.setChanged()
        t2 = time.clock()
        if trace:
            g.trace('%5.3f sec.' % (t2-t1))
        #
        # Move to the next redraw generation.
        self.old_flattened_outline = new_flattened_outline
        self.old_redraw_dict = redraw_dict
        self.redraw_generation += 1
    #@+node:ekr.20181111095640.1: *5* app.action.send_children_to_tree
    @flx.action
    def send_children_to_tree(self, parent_ap):
        '''
        Call w.tree.receive_children(d), where d is compatible with make_redraw_dict:
            {
                'parent_ap': parent_ap,
                'items': [
                    self.make_dict_for_position(p)
                        for p in for p in p.children()
                ],
            }
        '''
        trace = False and debug_tree and not g.unitTesting
        verbose = False
        p = self.ap_to_p(parent_ap)
        assert p, repr(parent_ap)
        if trace:
            # There is a similar trace in flx.tree.receive_children.
            print('===== send_children_to_tree: %s children' % len(list(p.children())))
            if verbose: # Corresponds to the trace in flx_tree.populate_children.
                for child in p.children():
                    print('  ' + child.h)
        #
        # Always respond, even if there are no children.
        # This allows the tree widget to reset state properly.
        w = self.main_window
        # assert parent_ap == self.p_to_ap(p), '\n%r\n%r' % (parent_ap, self.p_to_ap(p))
            # This assert can fail because the expansion bits don't match.
        w.tree.receive_children({
            'parent_ap': parent_ap,
            'items': [
                self.make_dict_for_position(p)
                    for p in p.children()
                # For compatibility with flx.tree.create_item_with_parent.
            ],
        })
    #@+node:ekr.20181111203114.1: *5* app.ap_to_p
    def ap_to_p (self, ap):
        '''Convert an archived position to a true Leo position.'''
        childIndex = ap ['childIndex']
        v = self.gnx_to_vnode [ap ['gnx']]
        stack = [
            (self.gnx_to_vnode [d ['gnx']], d ['childIndex'])
                for d in ap ['stack']
        ]
        return leoNodes.position(v, childIndex, stack)
    #@+node:ekr.20181124071215.1: *5* app.dump_top_level
    def dump_top_level(self):
        '''Dump the top-level nodes.'''
        trace = debug_tree and not g.unitTesting
        if trace:
            c = self.c
            banner('===== app.dump_top_level...')
            # print('root:', c.rootPosition().h)
            # print(' c.p:', c.p.h)
            # print('')
            # print('Top-level nodes...')
            for p in c.rootPosition().self_and_siblings():
                print('  %5s %s' % (p.isExpanded(), p.h))
            print('')
    #@+node:ekr.20181126083055.1: *5* app.flatten_outline
    def flatten_outline (self):
        '''Return a flat list of strings "level:gnx" for all *visible* positions.'''
        trace = False and not g.unitTesting
        t1 = time.clock()
        c, aList = self.c, []
        for p in c.rootPosition().self_and_siblings():
            self.extend_flattened_outline(aList, p)
        if trace:
            t2 = time.clock()
            print('app.flatten_outline: %s entries %6.4f sec.' % (
                len(aList), (t2-t1)))
        return aList
            
    def extend_flattened_outline(self, aList, p):
        '''Add p and all p's visible descendants to aList.'''
        aList.append('%s:%s:%s\n' % (p.level(), p.gnx, p.h))
            # Padding the fields causes problems later.
        if p.isExpanded():
            for child in p.children():
                self.extend_flattened_outline(aList, child)
    #@+node:ekr.20181113043539.1: *5* app.make_redraw_dict & helper
    def make_redraw_dict(self, p=None):
        '''
        Return a **recursive**, archivable, list of lists describing all the
        visible nodes of the tree.
        
        As a side effect, recreate gnx_to_vnode.
        '''
        trace = False and not g.unitTesting
        c = self.c
        p = p or c.p
        t1 = time.clock()
        c.expandAllAncestors(c.p)
            # Ensure that c.p will be shown.
        d = {
            'c.p': self.p_to_ap(p),
            'items': [
                self.make_dict_for_position(p)
                    for p in c.rootPosition().self_and_siblings()
            ],
        }
        t2 = time.clock()
        if trace:
            print('app.make_redraw_dict: %s direct children %5.3f sec.' % (
                len(list(c.rootPosition().self_and_siblings())), (t2-t1)))
        return d
    #@+node:ekr.20181113044701.1: *6* app.make_dict_for_position
    def make_dict_for_position(self, p):
        ''' 
        Recursively add a sublist for p and all its visible nodes.
        It is already known that p itself is visible.
        '''
        trace = debug_tree and verbose_debug_tree and not g.unitTesting
        assert p.v
        self.gnx_to_vnode[p.v.gnx] = p.v
        if trace:
            print('%s%s' % ('  '*p.level(), p.h))
                # A superb trace. There are similar traces in:
                # - flx_tree.redraw_with_dict  and its helper, flx_tree.create_item_with_parent.
                # - flx_tree.populate_children and its helper, flx_tree.create_item_for_ap
        if p.isExpanded(): # Do not use p.v.isExpanded().
            children = [
                self.make_dict_for_position(child)
                    for child in p.children()
            ]
        else:
            children = []
        return {
            'ap': self.p_to_ap(p),
            # 'body': p.b, # This would transfer much too much data.
            'children': children,
            'gnx': p.v.gnx,
            'headline': p.h,
        }
    #@+node:ekr.20181126094040.1: *5* app.make_redraw_list & helpers
    def make_redraw_list(self, a, b):
        '''
        Diff the a (old) and b (new) outline lists.
        Then optimize the diffs to create a redraw instruction list.
        '''
        trace = False and not g.unitTesting
        if a == b:
            return []

        def gnxs(aList):
            '''Return the gnx list. Do not try to remove this!'''
            return [z.strip() for z in aList]

        d = difflib.SequenceMatcher(None, a, b)
        op_codes = list(d.get_opcodes())
        # self.dump_op_codes(a, b, op_codes)
        #
        # Generate the instruction list, and verify the result.
        opcodes, result = [], []
        for tag, i1, i2, j1, j2 in op_codes:
            if tag == 'insert':
                opcodes.append(['insert', i1, gnxs(b[j1:j2])])
            elif tag == 'delete':
                opcodes.append(['delete', i1, gnxs(a[i1:i2])])
            elif tag == 'replace':
                opcodes.append(['replace', i1, gnxs(a[i1:i2]), gnxs(b[j1:j2])])
            result.extend(b[j1:j2])
        assert b == result, (a, b)
        #
        # Run the peephole.
        opcodes = self.peep_hole(opcodes)
        if trace:
            print('app.make_redraw_list: opcodes after peephole...')
            self.opcodes(opcodes)
        return opcodes
    #@+node:ekr.20181126183815.1: *6* app.dump_op_codes
    def dump_op_codes(self, a, b, op_codes):
        '''Dump the opcodes returned by difflib.SequenceMatcher.'''
        
        def summarize(aList):
            pat = re.compile(r'.*:.*:(.*)')
            return ', '.join([pat.match(z).group(1) for z in aList])
            
        for tag, i1, i2, j1, j2 in op_codes:
            if tag == 'equal':
                print('%7s at %s:%s (both) ==> %r' % (tag, i1, i2, summarize(b[j1:j2])))
            elif tag == 'insert':
                print('%7s at %s:%s (b)    ==> %r' % (tag, i1, i2, summarize(b[j1:j2])))
            elif tag == 'delete':
                print('%7s at %s:%s (a)    ==> %r' % (tag, i1, i2, summarize(a[i1:i2])))
            elif tag == 'replace':
                print('%7s at %s:%s (a)    ==> %r' % (tag, i1, i2, summarize(a[i1:i2])))
                print('%7s at %s:%s (b)    ==> %r' % (tag, i1, i2, summarize(b[j1:j2])))
            else:
                print('unknown tag')
    #@+node:ekr.20181126183817.1: *6* app.opcodes
    def opcodes(self, opcodes):
        '''Dump the opcodes returned by app.peep_hole and app.make_redraw_list.'''
        for z in opcodes:
            kind = z[0]
            if kind == 'replace':
                kind, i1, gnxs1, gnxs2 = z
                print(kind, i1)
                print('  a: [%s]' % ',\n    '.join(gnxs1))
                print('  b: [%s]' % ',\n    '.join(gnxs2))
            elif kind in ('delete', 'insert'):
                kind, i1, gnxs = z
                print(kind, i1)
                print('  [%s]' % ',\n    '.join(gnxs))
            else:
                print(z)
    #@+node:ekr.20181126154357.1: *5* app.peep_hole
    def peep_hole(self, opcodes):
        '''Scan the list of opcodes, merging adjacent op-codes.'''
        i, result = 0, []
        while i < len(opcodes):
            op0 = opcodes[i]
            if i == len(opcodes)-1:
                result.append(op0)
                break
            op1 = opcodes[i+1]
            kind0, kind1 = op0[0], op1[0]
            # Merge adjacent insert/delete opcodes with the same gnx.
            if (
                kind0 == 'insert' and kind1 == 'delete' or
                kind0 == 'delete' and kind1 == 'insert'
            ):
                kind0, index0, gnxs0 = op0
                kind1, index1, gnxs1 = op1
                if gnxs0[0] == gnxs1[0]:
                    result.append(['move', index0, index1, gnxs0, gnxs1])
                    i += 2 # Don't scan either op again!
                    break
            # The default is to retain the opcode.
            result.append(op0)
            i += 1
        return result
    #@+node:ekr.20181129122147.1: *4* app.edit_headline & helper
    def edit_headline(self):
        '''Simulate editing the headline in the minibuffer.'''
        c, w = self.c, self.root.main_window
        mb = w.minibuffer
        g.trace(mb, c.p.h)
        mb.set_text('Enter Headline: ')
        mb.set_focus()
        
    def edit_headline_completer(self, headline):
        g.trace(headline)
    #@+node:ekr.20181105091545.1: *4* app.open_bridge
    def open_bridge(self):
        '''Can't be in JS.'''
        bridge = leoBridge.controller(gui = None,
            loadPlugins = False,
            readSettings = True, # Required to get bindings!
            silent = False,
            tracePlugins = False,
            verbose = False, # True: prints log messages.
        )
        if not bridge.isOpen():
            flx.logger.error('Error opening leoBridge')
            return
        g = bridge.globals()
        path = g.os_path_finalize_join(g.app.loadDir, '..', 'test', 'unitTest.leo')
        if not g.os_path_exists(path):
            flx.logger.error('open_bridge: does not exist: %r' % path)
            return
        c = bridge.openLeoFile(path)
        return c, g
    #@+node:ekr.20181124095316.1: *4* app.Selecting...
    #@+node:ekr.20181111204659.1: *5* app.p_to_ap (updates app.gnx_to_vnode)
    def p_to_ap(self, p):
        '''
        Convert a true Leo position to a serializable archived position.
        '''
        if not p.v:
            banner('app.p_to_ap: no p.v: %r %s' % (p, g.callers()))
            assert False, g.callers()
        p_gnx = p.v.gnx
        if p_gnx not in self.gnx_to_vnode:
            # print('=== update gnx_to_vnode', p_gnx, p.h)
                # len(list(self.gnx_to_vnode.keys())
            self.gnx_to_vnode [p_gnx] = p.v
        return {
            'childIndex': p._childIndex,
            'cloned': p.isCloned(),
            'expanded': p.isExpanded(),
            'gnx': p.v.gnx,
            'level': p.level(),
            'headline': p.h,
            'marked': p.isMarked(),
            'stack': [{
                'gnx': stack_v.gnx,
                'childIndex': stack_childIndex,
                'headline': stack_v.h,
            } for (stack_v, stack_childIndex) in p.stack ],
        }
    #@+node:ekr.20181118061020.1: *5* app.action.select_p
    @flx.action
    def select_p(self, p):
        '''
        Select the position in the tree.
        
        Called from LeoBrowserTree.select, so do *not* call c.frame.tree.select.
        '''
        trace = debug_select and not g.unitTesting
        w = self.main_window
        ap = self.p_to_ap(p)
        # Be careful during startup.
        if w and w.tree:
            if trace:
                print('%s: action.select_p: %s' % (self.tag, p.h))
            w.tree.set_ap(ap)
    #@+node:ekr.20181111202747.1: *5* app.action.select_ap
    @flx.action
    def select_ap(self, ap):
        '''
        Select the position in Leo's core corresponding to the archived position.
        Nothin in the flx.tree needs to be updated.
        '''
        trace = debug_select and not g.unitTesting
        assert ap, g.callers()
        c, w = self.c, self.main_window
        p = self.ap_to_p(ap)
        assert p, (repr(ap), g.callers())
        lt, rt = c.frame.statusLine.update()
        w.status_line.update(lt, rt)
        if trace: print('===== app.select_ap', repr(ap))
        w.tree.select_ap(ap)
        c.frame.tree.super_select(p)
            # call LeoTree.select, but not self.select_p.
    #@+node:ekr.20181122132009.1: *4* app.Testing...
    #@+node:ekr.20181111142921.1: *5* app.action: do_command
    @flx.action
    def do_command(self, command):
        w = self.main_window
        c = self.c
        
        #@+others # define test_log & test_select.
        #@+node:ekr.20181119103144.1: *6* app.tests
        def test_focus():
            old_debug = g.app.debug
            try:
                g.app.debug = ['focus', 'keys',]
                print('\ncalling c.set_focus(c.frame.miniBufferWidget.widget')
                c.set_focus(c.frame.miniBufferWidget.widget)
            finally:
                g.app.debug = old_debug

        def test_log():
            print('testing log...')
            w.log.put('Test message to LeoFlexxLog.put')
                # Test LeoFlexxLog.put.
            c.frame.log.put('Test message to LeoBrowserLog.put')
                # Test LeoBrowserLog.put.
                
        def test_positions():
            print('testing positions...')
            self.test_round_trip_positions()
                
        def test_redraw():
            print('testing redraw...')
            self.redraw(None)
                
        def test_select():
            print('testing select...')
            h = 'Active Unit Tests'
            p = g.findTopLevelNode(c, h, exact=True)
            if p:
                c.frame.tree.select(p)
                # LeoBrowserTree.select.
            else:
                g.trace('not found: %s' % h)
        #@-others

        if command == 'cls':
            g.cls()
        elif command == 'focus':
            test_focus()
        elif command == 'log':
            test_log()
        elif command == 'redraw':
            test_redraw()
        elif command.startswith('sel'):
            test_select()
        elif command == 'test': # All except unit tests.
            test_log()
            test_positions()
            test_redraw()
            test_select()
        elif command == 'unit':
            self.run_all_unit_tests()
        else:
            # g.trace('unknown command: %r' % command)
            self.execute_minibuffer_command(command)
    #@+node:ekr.20181127070903.1: *5* app.execute_minibuffer_command (to do: tab completion)
    def execute_minibuffer_command(self, commandName):
        '''Execute a minibuffer command.'''
        # This code is all a hack.
        # It is a copy of k.callAltXFunction
        g.trace('=====', commandName)
        c, k = self.c, self.c.k
        event = g.Bunch(c=c, widget=c.frame.miniBufferWidget) ####### Another hack.
        k.functionTail = None ### Changed.
        if commandName and commandName.isdigit():
            # The line number Easter Egg.
            def func(event=None):
                c.gotoCommands.find_file_line(n=int(commandName))
        else:
            func = c.commandsDict.get(commandName)
        k.newMinibufferWidget = None
        if func:
            # These must be done *after* getting the command.
            k.clearState()
            k.resetLabel()
            if commandName != 'repeat-complex-command':
                k.mb_history.insert(0, commandName)
            w = event and event.widget
            if hasattr(w, 'permanent') and not w.permanent:
                # In a headline that is being edited.
                # g.es('Can not execute commands from headlines')
                c.endEditing()
                c.bodyWantsFocusNow()
                # Change the event widget so we don't refer to the to-be-deleted headline widget.
                event.w = event.widget = c.frame.body.wrapper.widget
                c.executeAnyCommand(func, event)
            else:
                c.widgetWantsFocusNow(event and event.widget)
                    # Important, so cut-text works, e.g.
                c.executeAnyCommand(func, event)
            k.endCommand(commandName)
            return True
        if 0: ### Not ready yet
            # Show possible completions if the command does not exist.
            if 1: # Useful.
                k.doTabCompletion(list(c.commandsDict.keys()))
            else: # Annoying.
                k.keyboardQuit()
                k.setStatusLabel('Command does not exist: %s' % commandName)
                c.bodyWantsFocus()
        return False
    #@+node:ekr.20181112182636.1: *5* app.run_all_unit_tests
    def run_all_unit_tests (self):
        '''Run all unit tests from the bridge.'''
        c = self.c
        h = 'Active Unit Tests'
        p = g.findTopLevelNode(c, h, exact=True)
        if p:
            try:
                old_debug = g.app.debug
                g.app.failFast = False
                g.app.debug = [] # ['focus', 'keys',]
                c.frame.tree.select(p)
                tm = BrowserTestManager(c)
                # Run selected tests locallyk.
                tm.doTests(all=False, marked=False)
            finally:
                g.app.debug = old_debug
        else:
            print('do_command: select: not found: %s' % h)
    #@+node:ekr.20181126104843.1: *5* app.test_full_outline
    def test_full_outline(self, p):
        '''Exercise the new diff-based redraw code on a fully-expanded outline.'''
        c = self.c
        p = p.copy()
        # Don't call c.expandAllHeadlines: it calls c.redraw.
        for p2 in c.all_positions(copy=False):
            p2.expand()
        #
        # Test the code.
        self.make_redraw_dict(p)
            # Call this only for timing stats.
        new_flattened_outline = self.flatten_outline()
        redraw_instructions = self.make_redraw_list(
            self.old_flattened_outline, new_flattened_outline)
        assert redraw_instructions is not None # For pyflakes.
        #
        # Restore the tree.
        for p2 in c.all_positions(copy=False):
            p2.contract()
        c.expandAllAncestors(p)
            # Does not do a redraw.
    #@+node:ekr.20181113180246.1: *5* app.test_round_trip_positions
    def test_round_trip_positions(self):
        '''Test the round tripping of p_to_ap and ap_to_p.'''
        c = self.c
        # Bug fix: p_to_ap updates app.gnx_to_vnode. Save and restore it.
        old_d = self.gnx_to_vnode.copy()
        old_len = len(list(self.gnx_to_vnode.keys()))
        # t1 = time.clock()
        for p in c.all_positions():
            ap = self.p_to_ap(p)
            p2 = self.ap_to_p(ap)
            assert p == p2, (repr(p), repr(p2), repr(ap))
        self.gnx_to_vnode = old_d
        new_len = len(list(self.gnx_to_vnode.keys()))
        assert old_len == new_len, (old_len, new_len)
        # print('app.test_round_trip_positions: %5.3f sec' % (time.clock()-t1))
    #@+node:ekr.20181124054536.1: *4* app.Utils
    @flx.action
    def cls(self):
        '''Clear the console'''
        g.cls()

    # def message(self, s):
        # '''For testing.'''
        # print('app.message: %s' % s)
    #@-others
#@+node:ekr.20181115092337.3: *3* class LeoBrowserBody
class LeoBrowserBody(leoFrame.NullBody):
    
    attributes = set()
   
    def __init__(self, frame):
        super().__init__(frame, parentFrame=None)
        self.c = c = frame.c
        self.root = get_root()
        self.tag = '(body wrapper)'
        # Replace the StringTextWrapper with the ace wrapper.
        assert isinstance(self.wrapper, leoFrame.StringTextWrapper)
        self.wrapper = AceWrapper(c, 'body')
            
    # The Ace Wrapper does almost everything.
    def __getattr__ (self, attr):
        if self.root.inited:
            return getattr(self.wrapper, attr)
        raise AttributeError('app not inited')

    def getName(self):
        return 'body' # Required for proper pane bindings.

#@+node:ekr.20181115092337.6: *3* class LeoBrowserFrame
class LeoBrowserFrame(leoFrame.NullFrame):
    
    def __init__(self, c, title, gui):
        '''Ctor for the LeoBrowserFrame class.'''
        super().__init__(c, title, gui)
        assert self.c == c
        frame = self
        self.root = get_root()
        self.tag = '(frame wrapper)'
        #
        # Instantiate the other wrappers.
        self.body = LeoBrowserBody(frame)
        self.tree = LeoBrowserTree(frame)
        self.log = LeoBrowserLog(frame)
        self.menu = LeoBrowserMenu(frame)
        self.miniBufferWidget = LeoBrowserMinibuffer(c, frame)
        self.iconBar = LeoBrowserIconBar(c, frame)
        self.statusLine = LeoBrowserStatusLine(c, frame)
            # NullFrame does this in createStatusLine.
        self.top = g.NullObject()
            # This is the DynamicWindow object.
            # There is no need to implement its methods now.
        
    def finishCreate(self):
        '''Override NullFrame.finishCreate.'''
        pass # Do not call self.createFirstTreeNode.

    #@+others
    #@-others
#@+node:ekr.20181113041113.1: *3* class LeoBrowserGui
class LeoBrowserGui(leoGui.NullGui):

    def __init__ (self, guiName='nullGui'):
        super().__init__(guiName='browser')
            # leoTest.doTest special-cases the name "browser".
        self.root = get_root()
        self.tag = '(browser gui)'
        self.consoleOnly = False # Console is separate from the log.
        
    def insertKeyEvent(self, event, i):
        '''Insert the key given by event in location i of widget event.w.'''
        # Mysterious...
        assert False, g.callers()
        
    def alert(self, c, message):
        # pylint: disable=arguments-differ
            # This is the signature for QtGui.Alert.
            # The signature in NullGui is wrong.
        print('')
        print('Alert:', message)
        print('')

    #@+others
    #@+node:ekr.20181119141542.1: *4* gui.isTextWrapper
    def isTextWrapper(self, w):
        '''Return True if w is supposedly a text widget.'''
        # isinstance is much more pythonic than using getName.
        if isinstance(w, (
            LeoBrowserBody,
            LeoBrowserLog,
            LeoBrowserMinibuffer,
            # LeoFlexxTreeItem,
                # At present, Leo's core can not edit tree items.
            LeoBrowserStatusLine,
        )):
            return True
        if g.unitTesting and isinstance(w, leoFrame.StringTextWrapper):
            return True
        return False
    #@+node:ekr.20181119153936.1: *4* gui.focus...
    def get_focus(self, *args, **kwargs):
        trace = debug_focus and not g.unitTesting
        w = self.focusWidget
        if trace:
            w_tag = w.tag if w else "NO WIDGET"
            print('%s: get_focus: %s %s' % (self.tag, w_tag,  g.callers(2)))
        return w

    def set_focus(self, commander, widget):
        trace = debug_focus and not g.unitTesting
        c = self.root.c
        if isinstance(widget, (
            LeoBrowserBody,
            LeoBrowserFrame,
            LeoBrowserLog,
            LeoBrowserMinibuffer,
            LeoBrowserTree,
        )):
            if trace:
                print(self.tag, 'set_focus', widget.tag)
            if not g.unitTesting:
                widget.setFocus()
            self.focusWidget = widget
        elif isinstance(widget, AceWrapper):
            # This does not get executed.
            print('===== %s set_focus: redirect ace body wrapper to LeoBrowserBody')
            assert isinstance(c.frame.body, LeoBrowserBody), repr(c.frame.body)
            assert widget.name == 'body', repr(widget.name)
            if not g.unitTesting:
                c.frame.body.setFocus()
        elif not g.unitTesting:
            # This gets called when reloading the page (reopening the .leo file) after Ctrl-F.
            # It also gets called during unit tests.
            g.trace('(gui): unknown widget', repr(widget), g.callers(6))
    #@-others
#@+node:ekr.20181115092337.21: *3* class LeoBrowserIconBar
class LeoBrowserIconBar(leoFrame.NullIconBarClass):

    def __init__(self, c, parentFrame):
        super().__init__(c, parentFrame)
        assert self.c == c
        self.root = get_root()
        self.tag = '(icon bar wrapper)'
            
    #@+others
    #@-others
#@+node:ekr.20181115092337.22: *3* class LeoBrowserLog
class LeoBrowserLog(leoFrame.NullLog):
    
    def __init__(self, frame, parentFrame=None):
        super().__init__(frame, parentFrame)
        self.root = get_root()
        self.tag = '(log wrapper)'
        assert isinstance(self.widget, leoFrame.StringTextWrapper)
        self.logCtrl = self.widget
        self.wrapper = self.widget
        #
        # Monkey-patch self.wrapper, a StringTextWrapper.
        assert self.wrapper.getName().startswith('log')
        self.wrapper.setFocus = self.setFocus
        
    def getName(self):
        return 'log' # Required for proper pane bindings.

    #@+others
    #@+node:ekr.20181120063043.1: *4* log_wrapper.setFocus
    def setFocus(self):
        w = self.root.main_window
        # g.trace('(log wrapper)')
        w.log.set_focus()
    #@+node:ekr.20181120063111.1: *4* log_wrapper.put & putnl
    def put(self, s, color=None, tabName='Log', from_redirect=False, nodeLink=None):
        self.root.main_window.log.put(s)

    def putnl(self, tabName='Log'):
        self.root.main_window.log.put('')
    #@-others
#@+node:ekr.20181115092337.31: *3* class LeoBrowserMenu
class LeoBrowserMenu(leoMenu.NullMenu):
    '''Browser wrapper for menus.'''

    # def __init__(self, frame):
        # super().__init__(frame)
        # self.root = get_root()
        # self.tag = '(menu wrapper)'

    # @others
#@+node:ekr.20181115120317.1: *3* class LeoBrowserMinibuffer (StringTextWrapper)
# Leo's core doesn't define a NullMinibuffer class.

class LeoBrowserMinibuffer (leoFrame.StringTextWrapper):
    '''Browser wrapper for minibuffer.'''
    
    def __init__(self, c, frame):
        super().__init__(c, name='minibuffer')
            # Name must be minibuffer, for gui.isTextWrapper().
        assert self.c == c, repr(self.c)
        assert self.widget is None, repr(self.widget)
        assert self.getName() == 'minibuffer'
        self.frame = frame
        self.root = get_root()
        self.tag = '(minibuffer wrapper)'
        self.widget = self
        self.wrapper = self
        # Hook this class up to the key handler.
        c.k.w = self
    
    # Overrides.
    def setFocus(self):
        # g.trace('===== (minibuffer wrapper)')
        self.root.main_window.minibuffer.set_focus()
        
    # Override the methods called by k.minibuffer methods:
        
    ###  delete

    def setAllText(self, s):
        w = self.root.main_window
        # print('===== (minibuffer wrapper) setAllText:', s)
        super().setAllText(s)
        w.minibuffer.set_text(s)
        
    def setSelectionRange(self, i, j, insert=None):
        w = self.root.main_window
        # print('===== (minibuffer wrapper) setSelectionRange:', i, j, repr(insert))
        super().setSelectionRange(i, j, insert)
        w.minibuffer.set_selection(i,j)
        if insert is not None:
            w.minibuffer.set_insert(insert)
            
    def setStyleClass(self, name):
        w = self.root.main_window
        # print('===== (minibuffer wrapper) setStyleClass:', repr(name))
        w.minibuffer.set_style(name)

    #@+others
    #@-others
#@+node:ekr.20181115092337.32: *3* class LeoBrowserStatusLine
class LeoBrowserStatusLine(leoFrame.NullStatusLineClass):
    
    def __init__(self, c, parentFrame):
        super().__init__(c, parentFrame)
        self.root = get_root()
        self.tag = '(status line wrapper)'
        self.w = self # Required.
        
    #@+others
    #@+node:ekr.20181119045430.1: *4* status_line_wrapper.clear & get
    def clear(self):
        pass
        
    def get(self):
        g.trace('(LeoBrowserStatusLine): NOT READY')
        return ''
    #@+node:ekr.20181119045343.1: *4* status_line_wrapper.put and put1
    def put(self, s, bg=None, fg=None):
        w = self.root.main_window
        # Be careful during startup.
        if w and w.status_line:
            w.status_line.put(s, bg, fg)

    def put1(self, s, bg=None, fg=None):
        w = self.root.main_window
        # Be careful during startup.
        if w and w.status_line:
            w.status_line.put2(s, bg, fg)
    #@+node:ekr.20181119154422.1: *4* status_line_wrapper.setFocus
    def setFocus(self):
        # g.trace('(status_line)', g.callers())
        self.root.status_line.set_focus()
    #@+node:ekr.20181119042937.1: *4* status_line_wrapper.update
    def update(self, body_text='', insert_point=0):
        '''
        Update the status line, based on the contents of the body.
        
        Called from LeoTree.select.
        
        Returns (lt_part, rt_part) for LeoBrowserApp.init.
        '''
        # pylint: disable=arguments-differ
        if g.app.killed:
            return
        c, p = self.c, self.c.p
        if not p:
            return
        # Calculate lt_part
        row, col = g.convertPythonIndexToRowCol(body_text, insert_point)
        fcol = c.gotoCommands.find_node_start(p)
        lt_part = "line: %2d col: %2d fcol: %s" % (row, col, fcol or '')
        # Calculate rt_part.
        headlines = [v.h for (v, childIndex) in p.stack] + [p.h]
        rt_part = '%s#%s' % (g.shortFileName(c.fileName()), '->'.join(headlines))
        # Update the status area.
        self.put(lt_part)
        self.put1(rt_part)
        return lt_part, rt_part
    #@-others
#@+node:ekr.20181115092337.57: *3* class LeoBrowserTree
class LeoBrowserTree(leoFrame.NullTree):
    
    def __init__(self, frame):
        super().__init__(frame)
        self.root = get_root()
        self.tag = '(tree wrapper)'
        self.widget = self
        self.wrapper = self

    def getName(self):
        return 'canvas(tree)' # Required for proper pane bindings.

    #@+others
    #@+node:ekr.20181116081421.1: *4* tree_wrapper.select, super_select, endEditLabel
    def select(self, p):
        '''Override NullTree.select, which is actually LeoTree.select.'''
        super().select(p)
            # Call LeoTree.select.'''
        self.root.select_p(p)
            # Call app.select_position.

    def super_select(self, p):
        '''Call only LeoTree.select.'''
        super().select(p)

    # def endEditLabel(self):
        # # Called from super_select.
        # if 0: print(self.tag, 'endEditLabel', g.callers())
    #@+node:ekr.20181118052203.1: *4* tree_wrapper.redraw
    def redraw(self, p=None):
        '''This is c.frame.tree.redraw!'''
        trace = debug_redraw and not g.unitTesting
        if trace:
            print(self.tag, '(c.frame.tree) redraw')
        self.root.redraw(p)
    #@+node:ekr.20181120063844.1: *4* tree_wrapper.setFocus
    def setFocus(self):
        w = self.root.main_window
        # g.trace('(tree wrapper)', g.callers())
        w.tree.set_focus()
    #@-others
#@+node:ekr.20181119094122.1: *3* class TracingNullObject
#@@nobeautify

class TracingNullObject(object):
    '''A tracing version of g.NullObject.'''
    def __init__(self, *args, **keys):
        pass

    def __call__(self, *args, **keys):
        return self

    def __repr__(self):
        return "NullObject"

    def __str__(self):
        return "NullObject"

    def __bool__(self):
        return False

    def __delattr__(self, attr):
        banner('NullObject.__delattr__ %r %s' % (attr, g.callers()))
        return self

    def __getattr__(self, attr):
        banner('NullObject.__getattr__ %r %s' % (attr, g.callers()))
        return self

    def __setattr__(self, attr, val):
        banner('NullObject.__setattr__ %r %s' % (attr, g.callers()))
        return self
#@+node:ekr.20181107052700.1: ** Js side: flx.Widgets
#@+node:ekr.20181201125953.1: *3* class JSEditorWidget
class JSEditorWidget(flx.Widget):
    '''The base class for all classes using a JS editor.'''
    
    def init(self, name, flex=1):
        # pylint: disable=arguments-differ
        assert name in ('body', 'log', 'minibuffer'), repr(name)
        self.name = name
        self.tag = '(flx %s)' % name
        self.editor = self.make_editor()
    
    @flx.reaction('size')
    def __on_size(self, *events):
        if use_ace:
            self.editor.resize()
        else:
            self.editor.refresh()
    
    #@+others
    #@+node:ekr.20181121072246.1: *4* jse.Keys & clicks
    @flx.emitter
    def key_press(self, e):
        ev = self._create_key_event(e)
        if self.should_be_leo_key(ev):
            e.preventDefault()
        return ev

    @flx.reaction('key_press')
    def on_key_press(self, *events):
        # The JS editor has already** handled the key!
        trace = debug_keys and not g.unitTesting
        tag = self.name.upper()
        for ev in events:
            editor = self.editor
            selector = editor.selection if use_ace else editor
            text = editor.getValue()
            cursor = selector.getCursor()
            if use_ace:
                row, col = cursor['row'], cursor['column']
            else:
                row, col = cursor['line'], cursor['ch']
            if trace:
                print('')
                print(tag, ': on_key_press', repr(ev ['modifiers']), repr(ev['key']))
                print('  text:', repr(text))
                print('cursor:', row, col)
            if self.should_be_leo_key(ev):
                print('===== call app.do_key')
                self.root.do_key(ev, self.name)
            ### self.root.update_body(text, row, col)
            
    @flx.reaction('pointer_click')
    def on_click(self, *events):
        trace = debug_keys and not g.unitTesting
        tag = self.name.upper()
        for ev in events:
            editor = self.editor
            selector = editor.selection if use_ace else editor
            text = editor.getValue()
            cursor = selector.getCursor()
            if use_ace:
                row, col = cursor['row'], cursor['column']
            else:
                row, col = cursor['line'], cursor['ch']
            if trace:
                editor = self.editor
                selector = editor.selection if use_ace else editor
                print('')
                print(tag, ': on_click')
                print('  text:', repr(text))
                print('cursor:', row, col)
            ###
                # if self.name == 'body':
                    # self.root.update_body(text, row, col)
    #@+node:ekr.20181201081645.1: *4* jse.make_editor
    def make_editor(self):
        '''Instantiate the JS editor, either ace or CodeMirror'''
        # pylint: disable=undefined-variable
            # window looks undefined.
        global window 
        is_body = self.name == 'body'
        print('===== JSE.make_editor', self.name)
        if use_ace:
            ace = window.ace.edit(self.node, "editor")
            ace.navigateFileEnd()  # otherwise all lines highlighted
            ace.setTheme("ace/theme/solarized_dark")
            if self.name == 'body':
                ace.getSession().setMode("ace/mode/python")
                    # This sets soft tabs.
            return ace
        #
        # Use CodeMirror
        options = dict(
            value='',
            mode='python' if is_body else None,
            theme='solarized dark',
            autofocus=True,
            styleActiveLine=True,
            matchBrackets=True,
            indentUnit=4,
            smartIndent=True,
            lineWrapping=True,
            lineNumbers=True,
            firstLineNumber=1,
            readOnly=False,
        )
        return window.CodeMirror(self.node, options)
    #@+node:ekr.20181201081444.1: *4* jse.should_be_leo_key
    def should_be_leo_key(self, ev):
        trace = debug_keys and not g.unitTesting
        key, mods, tag = ev['key'], ev['modifiers'], 'JSE.should_be_leo_key:'
        #
        # The widget handles F-keys.
        if not mods and key.startswith('F'):
            if trace: print(tag, 'Send F-Keys to body', repr(key), repr(mods))
            return False
        mods2 = mods
        if 'Shift' in mods2:
            mods2.remove('Shift')
        #
        # Send only Ctrl-Arrow keys to body.
        if mods2 == ['Ctrl'] and key in ('RtArrow', 'LtArrow', 'UpArrow', 'DownArrow'):
            # This never fires: Neither editor widget emis Ctrl/Arrow keys or Alt-Arrow keys.
            if trace: print(tag, 'Arrow key: send to to body', repr(key), repr(mods))
            return False
        #
        # Leo should handle all other modified keys.
        if mods2:
            if trace: print(tag, '  modified: send to Leo', repr(key), repr(mods))
        else:
            if trace: print(tag, 'unmodified: send to Body', repr(key), repr(mods))
        return mods
    #@-others
#@+node:ekr.20181104082144.1: *3* class LeoFlexxBody
class LeoFlexxBody(JSEditorWidget):
    '''A CodeEditor widget based on Ace.'''

    #@+<< body css >>
    #@+node:ekr.20181120055046.1: *4* << body css >>
    CSS = """
    .flx-CodeEditor > .ace {
        width: 100%;
        height: 100%;
    }
    """
    #@-<< body css >>

    def init(self):
        # pylint: disable=arguments-differ
        super().init('body')
        ### self.name = name
        ### self.tag = '(flx %s)' % name
        ### self.editor = self.make_editor()

    #@+others
    #@+node:ekr.20181128061524.1: *4* flx_body setters (These may not be needed!)
    @flx.action
    def see_insert_point(self):
        if 0: print(self.tag, 'see_insert_point')
        
    @flx.action
    def insert(self, s):
        trace = debug_keys and not g.unitTesting
        if trace:
            print(self.tag, 'insert', repr(s))
        if use_ace:
            self.editor.insert(s)
        else:
            print('NOT READY')
            ### self.cm.insert(s) ##############

    @flx.action
    def select_all_text(self):
        if debug_body: print(self.tag, 'select_all_text')
        
    @flx.action
    def set_focus(self):
        trace = debug_focus and not g.unitTesting
        if trace: print(self.tag, 'set_focus')
        self.editor.focus()

    @flx.action
    def set_insert_point(self, i):
        if 0: # This would work, if i were correct.
            s = self.editor.getValue()
            row, col = g.convertPythonIndexToRowCol(s,i)
            if debug_body: print('%s: set_insert_point: i: %s len(s): %s row: %s col: %s' % (
                self.tag, i, len(s), row, col))
            if use_ace:
                self.editor.moveCursorTo(row, col)

    @flx.action
    def set_selection_range(self, i, j):
        if debug_body: print(self.tag, 'set_selection_range', i, j)
        ### print(self.editor.getSession()) ###

    @flx.action
    def set_text(self, s):
        '''Set the entire text'''
        if debug_body:
            print(self.tag, 'set_text', repr(g.truncate(s, 50)))
        self.editor.setValue(s)
    #@-others
#@+node:ekr.20181104082149.1: *3* class LeoFlexxLog
class LeoFlexxLog(JSEditorWidget):
    
    #@+<< log css >>
    #@+node:ekr.20181120060336.1: *4* << log css >>
    CSS = """
    .flx-CodeEditor > .ace {
        width: 100%;
        height: 100%;
    }
    """
    #@-<< log css >>
    
    def init(self):
        # pylint: disable=arguments-differ
        super().init('log')

    ### 
        # def init(self):
            # # pylint: disable=undefined-variable
                # # window
            # global window
            # self.tag = '(flx log)'
            # self.ace = window.ace.edit(self.node, "log editor")
            # self.ace.navigateFileEnd()  # otherwise all lines highlighted
            # self.ace.setTheme("ace/theme/solarized_dark")
    
        # @flx.reaction('size')
        # def __on_size(self, *events):
            # self.ace.resize()

    #@+others
    #@+node:ekr.20181120060348.1: *4* flx.log.put & set_focus
    @flx.action
    def put(self, s):
        self.editor.setValue(self.editor.getValue() + '\n' + s)
        
    @flx.action
    def set_focus(self):
        trace = debug_focus and not g.unitTesting
        if trace: print(self.tag, 'ace.focus()')
        self.editor.focus()
    #@-others
        
#@+node:ekr.20181104082130.1: *3* class LeoFlexxMainWindow
class LeoFlexxMainWindow(flx.Widget):
    
    '''
    Leo's main window, that is, root.main_window.
    
    Each property is accessible as root.main_window.x.
    '''
    body = flx.ComponentProp(settable=True)
    log = flx.ComponentProp(settable=True)
    minibuffer = flx.ComponentProp(settable=True)
    status_line = flx.ComponentProp(settable=True)
    tree = flx.ComponentProp(settable=True)
    
    do_init = flx.BoolProp(settable=True)
        # https://github.com/flexxui/flexx/issues/531

    def init(self):
        self.tag = '(flx main window)'
        ### with flx.TabLayout():
        with flx.VSplit():
            with flx.HSplit(flex=1):
                tree = LeoFlexxTree(flex=1)
                log = LeoFlexxLog(flex=1)
            body = LeoFlexxBody(flex=1)
            minibuffer = LeoFlexxMiniBuffer()
            status_line = LeoFlexxStatusLine()
        self._mutate('body', body)
        self._mutate('log', log)
        self._mutate('minibuffer', minibuffer)
        self._mutate('status_line', status_line)
        self._mutate('tree', tree)
        self._mutate('do_init', True)
        
    @flx.reaction('do_init', mode="greedy")
    def after_init(self):
        self.root.finish_create()

    #@+others
    #@-others
#@+node:ekr.20181104082154.1: *3* class LeoFlexxMiniBuffer
# class AceMinibuffer(flx.Widget):

    # def init(self):
        # # pylint: disable=undefined-variable
            # # window
        # global window
        # self.ace = window.ace.edit(self.node, "minibuffer")
        # self.ace.navigateFileEnd()  # otherwise all lines highlighted
        # self.ace.setTheme("ace/theme/solarized_dark")

class LeoFlexxMiniBuffer(JSEditorWidget):
    
    def init(self):
        # pylint: disable=arguments-differ
        super().init('minibuffer')

    # def init(self):
        # self.tag = '(flx minibuffer)'
        # with flx.HBox():
            # flx.Label(text='Minibuffer')
            # ### self.widget = AceMinibuffer(flex=1)
            # self.widget = JSEditorWidget('minibuffer')
            # self.editor = self.widget.editor

    #@+others
    #@+node:ekr.20181127060810.1: *4* flx_minibuffer.high-level interface
    # The high-level interface methods, called from LeoBrowserMinibuffer.
    # self.widget is a flx.LineEdit.

    @flx.action
    def set_focus(self):
        trace = debug_focus and not g.unitTesting
        if trace: print(self.tag, 'minibuffer.ace.focus()')
        self.editor.focus()
        
    @flx.action
    def set_insert(self, i):
        if 0: print('===== flx.minibuffer.set_insert', i)

    @flx.action
    def set_selection(self, i, j):
        if 0: print('===== flx.minibuffer.set_selection', i, j)
        
    @flx.action
    def set_style(self, style):
        trace = debug_focus and not g.unitTesting
        if trace: print(self.tag, 'set_style: minibuffer.ace.focus()')
        # A hack. Also set focus.
        self.editor.focus()
        
    @flx.action
    def set_text(self, s):
        if 0: print('===== flx.minibuffer.set_text')
        self.editor.setValue(s)
    #@+node:ekr.20181129174405.1: *4* flx_minibuffer.do_enter_key (Easter Eggs)
    def do_enter_key(self):
        '''
        Handle the enter key in the minibuffer.
        This will only be called if the user has entered the minibuffer via a click.
        '''
        command = self.editor.getValue()
        print('\nMinibuffer: key_press: Enter', repr(command))
        if command.strip():
            if command.startswith('full-command:'):
                command = command[len('full-command:'):].strip()
                self.root.do_command(command)
            elif command.startswith('Enter Headline:'):
                headline = command[len('Enter Headline:'):].strip()
                self.root.edit_headline_completer(headline)
            else:
                self.root.do_command(command)
            self.set_text('')
    #@-others
#@+node:ekr.20181104082201.1: *3* class LeoFlexxStatusLine
class LeoFlexxStatusLine(flx.Widget):
    
    def init(self):
        self.tag = '(flx status line)'
        with flx.HBox():
            flx.Label(text='Status Line')
            self.widget = flx.LineEdit(flex=1)
            self.widget2 = flx.LineEdit(flex=1)
        self.widget.apply_style('background: green')
        self.widget2.apply_style('background: green')

    #@+others
    #@+node:ekr.20181123043015.1: *4* flx.status_line.action.update
    @flx.action
    def update(self, lt, rt):
        self.put(lt)
        self.put2(rt)
    #@+node:ekr.20181120060957.1: *4* flx_status_line.action.put & put2
    @flx.action
    def put(self, s, bg=None, fg=None):
        self.widget.set_text(s)
        
    @flx.action
    def put2(self, s, bg=None, fg=None):
        self.widget2.set_text(s)
    #@+node:ekr.20181120060950.1: *4* flx_status_line.Key handling
    @flx.emitter
    def key_press(self, e):
        trace = debug_keys and not g.unitTesting
        ev = self._create_key_event(e)
        if trace: print('\nStatus Line: key_press', repr(ev))
        mods = ev ['modifiers']
        if 'Shift' in mods:
            mods.remove('Shift')
        if mods:
            e.preventDefault()
        #### F12 does not work in the status line.
        return ev
        
    @flx.reaction('key_press')
    def on_key_press(self, *events):
        trace = debug_keys and not g.unitTesting
        for ev in events:
            key, mods = ev['key'], ev ['modifiers']
            if trace: print('\nSTATUS LINE: on_key_press', repr(mods), repr(key))
            if 'Shift' in mods:
                mods.remove('Shift')
            if mods:
                self.root.do_key(ev, 'statusLine')
    #@-others
#@+node:ekr.20181104082138.1: *3* class LeoFlexxTree
class LeoFlexxTree(flx.Widget):
    
    #@+<< tree css >>
    #@+node:ekr.20181120061118.1: *4*  << tree css >>

    CSS = '''
    .flx-TreeWidget {
        background: #000;
        color: white;
        /* background: #ffffec; */
        /* Leo Yellow */
        /* color: #afa; */
    }
    '''
    #@-<< tree css >>

    def init(self):
        self.widget = self
        self.wrapper = self
        self.tag = '(flx tree)'
        # Init local ivars...
        self.populated_items_dict = {}
            # Keys are ap **keys**, values are True.
        self.populating_tree_item = None
            # The LeoTreeItem whose children are to be populated.
        self.selected_ap = {}
            # The ap of the presently selected node.
        self.tree_items_dict = {}
            # Keys are ap's. Values are LeoTreeItems.
        # Init the widget.
        self.tree = flx.TreeWidget(flex=1, max_selected=1)
            # The max_selected property does not seem to work.

    def assert_exists(self, obj):
        # pylint: disable=undefined-variable
            # undefined
        global undefined
        assert obj not in (undefined, None, {}), repr(obj)

    #@+others
    #@+node:ekr.20181121073246.1: *4* flx_tree.Drawing...
    #@+node:ekr.20181112163252.1: *5* flx_tree.action.clear_tree
    @flx.action
    def clear_tree(self):
        '''
        Completely clear the tree, preparing to recreate it.
        
        Important: we do *not* clear self.tree itself!
        '''
        # pylint: disable=access-member-before-definition
        trace = debug_redraw and not g.unitTesting
        items = list(self.tree_items_dict.values())
        if trace:
            print('===== flx.tree.clear_tree: %s items' % (len(items)))
        # Clear all tree items.
        for item in items:
            # print(repr(item))
            item.dispose()
        self.tree_items_dict = {}
    #@+node:ekr.20181113043004.1: *5* flx_tree.action.redraw_with_dict & helper
    @flx.action
    def redraw_with_dict(self, redraw_dict, redraw_instructions):
        '''
        Clear the present tree and redraw using the **recursive** redraw_list.
        d has the form:
            {
                'c.p': self.p_to_ap(p),
                'items': [
                    self.make_dict_for_position(p)
                        for p in c.rootPosition().self_and_siblings()
                ],
            }
        '''
        trace_redraw = debug_redraw and not g.unitTesting
        trace_select = debug_select and not g.unitTesting
        tag = '%s: redraw_with_dict' % self.tag
        assert redraw_dict
        self.clear_tree()
        items = redraw_dict ['items']
        if trace_redraw:
            print('%s: %s direct children' % (tag, len(items)))
        for item in items:
            self.create_item_with_parent(item, self.tree)
        # Select c.p.
        if trace_select:
            print('%s: select: %s' % (tag, redraw_dict['c.p']['headline']))
        self.select_ap(redraw_dict['c.p'])
    #@+node:ekr.20181124194248.1: *6* tree.create_item_with_parent
    def create_item_with_parent(self, item, parent):
        '''Create a tree item for item and all its visible children.'''
        # pylint: disable=no-member
            # set_collapsed is in the base class.
        trace = debug_tree and verbose_debug_tree and not g.unitTesting
        verbose = True
        ap = item ['ap']
        if trace and verbose: # An effective, lengthy, trace.
            print('%s%s' % ('  '*ap ['level'], ap['headline']))
        #
        # Create the node.
        with parent:
            tree_item = LeoFlexxTreeItem(ap, text=ap['headline'], checked=None, collapsed=True)
        tree_item.set_collapsed(not ap['expanded'])
        #
        # Set the data.
        key = self.ap_to_key(ap)
        self.tree_items_dict [key] = tree_item
        # Children are *not* necessarily sent, so set the populated 'bit' only if they are.
        if item['children']:
            if trace: print('create_item_with_parent: **populated**', ap['headline'])
            self.populated_items_dict[key] = True
        if hasattr(parent, 'leo_children'):
            # print('create_item_with_parent', parent.leo_ap['headline'], ap['headline'])
            parent.leo_children.append(tree_item)
        #
        # Create the children.
        for child in item ['children']:
            self.create_item_with_parent(child, tree_item)
    #@+node:ekr.20181114072307.1: *5* flx_tree.ap_to_key
    def ap_to_key(self, ap):
        '''Produce a key for the given ap.'''
        self.assert_exists(ap)
        childIndex = ap ['childIndex']
        gnx = ap ['gnx']
        headline = ap ['headline']
        stack = ap ['stack']
        stack_s = '::'.join([
            'childIndex: %s, gnx: %s' % (z ['childIndex'], z ['gnx'])
                for z in stack
        ])
        key = 'Tree key<childIndex: %s, gnx: %s, %s <stack: %s>>' % (
            childIndex, gnx, headline, stack_s or '[]')
        return key
    #@+node:ekr.20181113085722.1: *5* flx_tree.dump_ap
    def dump_ap (self, ap, padding, tag):
        '''Print an archived position fully.'''
        stack = ap ['stack']
        if not padding:
            padding = ''
        padding = padding + ' '*4 
        if stack:
            print('%s%s:...' % (padding, tag or 'ap'))
            padding = padding + ' '*4
            print('%schildIndex: %s v: %s %s stack: [' % (
                padding,
                str(ap ['childIndex']),
                ap['gnx'],
                ap['headline'],
            ))
            padding = padding + ' '*4
            for d in ap ['stack']:
                print('%s%s %s %s' % (
                    padding,
                    str(d ['childIndex']).ljust(3),
                    d ['gnx'],
                    d ['headline'],
                ))
            padding = padding [:-4]
            print(']')
        else:
            print('%s%s: childIndex: %s v: %s stack: [] %s' % (
                padding, tag or 'ap',
                str(ap ['childIndex']).ljust(3),
                ap['gnx'],
                ap['headline'],
            ))
    #@+node:ekr.20181104080854.3: *5* flx_tree.reaction: on_tree_event
    # actions: set_checked, set_collapsed, set_parent, set_selected, set_text, set_visible
    @flx.reaction(
        'tree.children**.checked',
        'tree.children**.collapsed',
        'tree.children**.visible', # Never seems to fire.
    )
    def on_tree_event(self, *events):
        for ev in events:
            trace = False and (debug_tree or debug_redraw) and not g.unitTesting
            expand = not ev.new_value
            if expand:
                # Don't redraw if the LeoTreeItem has children.
                tree_item = ev.source
                ap = tree_item.leo_ap
                if ap['expanded']:
                    if trace: print('===== flx.tree.on_tree_event: already expanded', ap['headline'])
                else:
                    ap['expanded'] = True
                    ### self.root.expand_and_redraw(ap)
                    self.start_populating_children(ap, tree_item)
                    # Populate children, if necessary.
    #@+node:ekr.20181120063735.1: *4* flx_tree.Focus
    @flx.action
    def set_focus(self):
        trace = debug_focus and not g.unitTesting
        if trace: print(self.tag, 'self.node.ace.focus()')
        self.node.focus()
    #@+node:ekr.20181123165819.1: *4* flx_tree.Incremental Drawing...
    # This are not used, at present, but they may come back.
    #@+node:ekr.20181125051244.1: *5* flx_tree.populate_children
    def populate_children(self, children, parent_ap):
        '''
        Populate the children of the given parent.
        
        self.populating_tree_item is the LeoFlexxTreeItem to be populated.

        children is a list of ap's.
        '''
        trace = False and debug_tree and not g.unitTesting
        parent = self.populating_tree_item
        assert parent
        assert parent_ap == parent.leo_ap
            # The expansion bit may have changed?
        if trace:
            print('flx.tree.populate_children: parent: %r %s children' % (parent, len(children)))
        for child_ap in children:
            self.create_item_with_parent(child_ap, parent)
        self.populating_tree_item = False
    #@+node:ekr.20181111011928.1: *5* flx_tree.start_populating_children
    def start_populating_children(self, parent_ap, parent_tree_item):
        '''
        Populate the parent tree item with the children if necessary.
        
        app.send_children_to_tree should send an empty list
        '''
        trace = False and debug_tree and not g.unitTesting
        if trace:
            headline = parent_tree_item.leo_ap ['headline']
            tag = 'flx.tree.start_populating_children'
        self.assert_exists(parent_ap)
        self.assert_exists(parent_tree_item)
        headline = parent_ap ['headline']
        key = self.ap_to_key(parent_ap)
        if key in self.populated_items_dict:
            # if trace: print('%s: already populated: %s' % (tag, headline))
            return
        if trace: print(tag, headline)
        assert isinstance(parent_tree_item, LeoFlexxTreeItem)
        # Remember the parent_tree_item.
        self.populating_tree_item = parent_tree_item
        #
        # Ask for the items.
        if trace: print('%s: calling app.send_children_to_tree' % (tag))
        self.root.send_children_to_tree(parent_ap)
    #@+node:ekr.20181110175222.1: *5* flx_tree.action.receive_children
    @flx.action
    def receive_children(self, d):
        '''
        Populate the direct descendants of ap. d is compatible with make_redraw_dict:
            {
                'parent_ap': parent_ap,
                'items': [
                    self.make_dict_for_position(p)
                        for p in for p in p.children()
                ],
            }
        '''
        trace = False and debug_tree and not g.unitTesting
        parent_ap = d ['parent_ap']
        children = d ['items']
        if trace:
            print('===== flx.tree.receive_children: %s children' % (len(children)))
        self.populate_children(children, parent_ap)
    #@+node:ekr.20181120061140.1: *4* flx_tree.Key handling
    @flx.emitter
    def key_press(self, e):
        trace = debug_keys and not g.unitTesting
        ev = self._create_key_event(e)
        f_key = not ev['modifiers'] and ev['key'].startswith('F')
        if trace: print('\nTREE: key_press', repr(ev), 'preventDefault', not f_key)
        if not f_key:
            e.preventDefault()
        return ev

    @flx.reaction('tree.key_press')
    def on_key_press(self, *events):
        trace = debug_keys and not g.unitTesting
        if trace: print('===== flx.TREE.key_press')
        for ev in events:
            self.root.do_key(ev, 'tree')
    #@+node:ekr.20181121195235.1: *4* flx_tree.Selecting...
    #@+node:ekr.20181123171958.1: *5* flx_tree.action.set_ap
    # This must exist so app.select_p can call it.

    @flx.action
    def set_ap(self, ap):
        '''self.selected_ap. Called from app.select_ap.'''
        assert ap
        self.selected_ap = ap
        self.select_ap(self.selected_ap)
    #@+node:ekr.20181116083916.1: *5* flx_tree.select_ap
    @flx.action
    def select_ap(self, ap):
        '''
        Select the tree item corresponding to the given ap.
        
        Called from the mutator, and also on_selected_event.
        '''
        # print('===== flx.tree.select_ap', repr(ap), ap ['headline'])
        key = self.ap_to_key(ap)
        item = self.tree_items_dict.get(key)
        if item:
            item.set_selected(True)
            self.selected_ap = ap
                # Set the item's selected property.
        else:
            pass # We may be in the middle of a redraw.
    #@+node:ekr.20181109083659.1: *5* flx_tree.reaction.on_selected_event
    @flx.reaction('tree.children**.selected') # don't use mode="greedy" here!
    def on_selected_event(self, *events):
        '''
        Update c.p and c.p.b when the user selects a new tree node.
        
        This also gets fired on *unselection* events, which causes problems.
        '''
        trace = False and debug_tree and not g.unitTesting
        #
        # Reselect the present ap if there are no selection events.
        # This ensures that clicking a headline twice has no effect.
        if not any([ev.new_value for ev in events]):
            ev = events[0]
            self.assert_exists(ev)
            ap = ev.source.leo_ap
            self.assert_exists(ap)
            self.select_ap(ap)
            return
        #
        # handle selection events.
        if trace: print('='*20)
        for ev in events:
            if ev.new_value: # A selection event.
                ap = ev.source.leo_ap
                if trace: print('on_selected_event: select:', ap['headline'])
                # self.dump_ap(ap)
                self.root.select_ap(ap)
                    # This *only* sets c.p. and updated c.p.b.
                self.select_ap(ap)
                    # Selects the corresponding LeoTreeItem.
                self.set_ap(ap)
                    # Sets self.selected_ap.
                self.root.set_body_text()
                    # Update the body text.
                self.root.set_status()
                    # Update the status line.
    #@-others
#@+node:ekr.20181108233657.1: *3* class LeoFlexxTreeItem
class LeoFlexxTreeItem(flx.TreeItem):

    def init(self, leo_ap):
        # pylint: disable=arguments-differ
        self.leo_ap = leo_ap
            # Immutable: Gives access to cloned, marked, expanded fields.
        self.leo_children = []

    def getName(self):
        return 'head' # Required, for proper pane bindings.

    #@+others
    #@-others
#@+node:ekr.20181121031304.1: ** class BrowserTestManager
class BrowserTestManager (leoTest.TestManager):
    '''Run tests using the browser gui.'''
    
    def instantiate_gui(self):
        assert isinstance(g.app.gui, LeoBrowserGui)
        return g.app.gui
#@-others
if __name__ == '__main__':
    flx.launch(LeoBrowserApp)
    flx.logger.info('LeoApp: after flx.launch')
    flx.set_log_level('ERROR' if warnings_only and use_ace else 'INFO')
        # Debug produces too many messages, in general.
    flx.run()
#@-leo
