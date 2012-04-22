#@+leo-ver=5-thin
#@+node:ekr.20110605121601.17954: * @file ../plugins/nested_splitter.py
#@@language python
#@@tabwidth -4

#@+<< imports >>
#@+node:ekr.20110605121601.17955: ** << imports >> (nested_splitter.py)
try:
    import leo.core.leoGlobals as g
except ImportError:
    pass  # this import should be removed anyway

import sys

from inspect import isclass

from PyQt4 import QtGui, QtCore, Qt

from PyQt4.QtCore import Qt as QtConst
#@-<< imports >>

#@+others
#@+node:ekr.20110605121601.17956: ** init
def init():
    
    # Allow this to be imported as a plugin,
    # but it should never be necessary to do so.
    
    return True
#@+node:ekr.20110605121601.17957: ** class DemoWidget
class DemoWidget(QtGui.QWidget):

    count = 0

    #@+others
    #@+node:ekr.20110605121601.17958: *3* __init__(DemoWidget)
    def __init__(self, parent=None, color=None):

        QtGui.QWidget.__init__(self, parent)

        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(QtCore.QMargins(0,0,0,0))
        self.layout().setSpacing(0)

        text = QtGui.QTextEdit()
        self.layout().addWidget(text)
        DemoWidget.count += 1
        text.setPlainText("#%d" % DemoWidget.count)

        button_layout = QtGui.QHBoxLayout()
        button_layout.setContentsMargins(QtCore.QMargins(5,5,5,5))
        self.layout().addLayout(button_layout)


        button_layout.addWidget(QtGui.QPushButton("Go"))
        button_layout.addWidget(QtGui.QPushButton("Stop"))

        if color:
            self.setStyleSheet("background-color: %s;"%color)
    #@-others
#@+node:ekr.20110605121601.17959: ** class NestedSplitterChoice (QWidget)
class NestedSplitterChoice(QtGui.QWidget):
    """When a new pane is opened in a nested splitter layout, this widget
    presents a button, labled 'Action', which provides a popup menu
    for the user to select what to do in the new pane"""
    #@+others
    #@+node:ekr.20110605121601.17960: *3* __init__ (NestedSplitterChoice)
    def __init__(self,parent=None):

        QtGui.QWidget.__init__(self, parent)

        self.setLayout(QtGui.QVBoxLayout())
        
        button = QtGui.QPushButton("Action",self) # EKR: 2011/03/15
        self.layout().addWidget(button)

        button.setContextMenuPolicy(QtConst.CustomContextMenu)
        
        button.connect(button,
            Qt.SIGNAL('customContextMenuRequested(QPoint)'),
            lambda pnt: self.parent().choice_menu(self,
                button.mapToParent(pnt)))

        button.connect(button,
            Qt.SIGNAL('clicked()'),
            lambda: self.parent().choice_menu(self,button.pos()))
    #@-others
#@+node:ekr.20110605121601.17961: ** class NestedSplitterHandle
class NestedSplitterHandle(QtGui.QSplitterHandle):
    """Show the context menu on a NestedSplitter splitter-handle to access
    NestedSplitter's special features"""
    #@+others
    #@+node:ekr.20110605121601.17962: *3* __init__ (NestedSplitterHandle)
    def __init__(self, owner):
        
        # g.trace('NestedSplitterHandle')
        
        QtGui.QSplitterHandle.__init__(self, owner.orientation(), owner)

        self.setStyleSheet("background-color: green;")

        self.setContextMenuPolicy(QtConst.CustomContextMenu)

        self.connect(self,
            Qt.SIGNAL('customContextMenuRequested(QPoint)'),
            self.splitter_menu)
    #@+node:ekr.20110605121601.17963: *3* __repr__
    def __repr__ (self):
        
        return '(NestedSplitterHandle) at: %s' % (id(self))
        
    __str__ = __repr__
    #@+node:ekr.20110605121601.17964: *3* add_item
    def add_item (self,func,menu,name):
        """helper for splitter_menu menu building"""
        act = QtGui.QAction(name, self)
        act.setObjectName(name.lower().replace(' ','-'))
        act.connect(act, Qt.SIGNAL('triggered()'),func)
        menu.addAction(act)
    #@+node:ekr.20110605121601.17965: *3* splitter_menu
    def splitter_menu(self, pos):
        """build the context menu for NestedSplitter"""

        splitter = self.splitter()

        if not splitter.enabled:
            g.trace('splitter not enabled')
            return

        index = splitter.indexOf(self)

        widget, neighbour, count = splitter.handle_context(index)

        lr = 'Left', 'Right'
        ab = 'Above', 'Below'
        split_dir = 'Vertically'
        if self.orientation() == QtConst.Vertical:
            lr, ab = ab, lr
            split_dir = 'Horizontally'

        # blue/orange - color-blind friendly
        color = '#729fcf', '#f57900'
        sheet = []
        for i in 0,1:
            sheet.append(widget[i].styleSheet())
            widget[i].setStyleSheet(sheet[-1]+"\nborder: 2px solid %s;"%color[i])

        menu = QtGui.QMenu()
        
        # Insert.
        def insert_callback(index=index):
            splitter.insert(index)
        self.add_item(insert_callback,menu,'Insert')

        # Swap.
        def swap_callback(index=index):
            splitter.swap(index)
        self.add_item(swap_callback,menu,
            "Swap %d %s %d %s" % (count[0], lr[0], count[1], lr[1]))
        
        # Rotate All.
        self.add_item(splitter.rotate,menu,'Rotate All')

        # Remove, +0/-1 reversed, we need to test the one that remains

        # First see if a parent has more than two splits
        # (we could be a sole surviving child).
        max_parent_splits = 0
        up = splitter.parent()
        while isinstance(up,NestedSplitter):
            max_parent_splits = max(max_parent_splits, up.count())
            up = up.parent()
            if max_parent_splits >= 2:
                break  # two is enough

        for i in 0,1:
            keep = splitter.widget(index)
            cull = splitter.widget(index-1)
            if (max_parent_splits >= 2 or  # more splits upstream
                splitter.count() > 2 or    # 3+ splits here, or 2+ downstream
                neighbour[not i] and neighbour[not i].max_count() >= 2
            ):
                def remove_callback(i=i,index=index):
                    splitter.remove(index,i)
                self.add_item(remove_callback,menu,'Remove %d %s' % (count[i], lr[i]))

        # Split: only if not already split.
        for i in 0,1:
            if not neighbour[i] or neighbour[i].count() == 1:
                def split_callback(i=i,index=index,splitter=splitter):
                    splitter.split(index,i)
                self.add_item(split_callback,menu,'Split %s %s' % (lr[i], split_dir))

        for i in 0,1:
            def mark_callback(i=i,index=index):
                splitter.mark(index, i)
            self.add_item(mark_callback,menu,'Mark %d %s' % (count[i], lr[i]))
           
        # Swap With Marked.
        if splitter.root.marked:
            for i in 0,1:
                if not splitter.invalid_swap(widget[i],splitter.root.marked[2]):
                    def swap_mark_callback(i=i,index=index,splitter=splitter):
                        splitter.swap_with_marked(index, i)
                    self.add_item(swap_mark_callback,menu,
                        'Swap %d %s With Marked' % (count[i], lr[i]))
        # Add.
        for i in 0,1:
            if (not isinstance(splitter.parent(), NestedSplitter) or
                splitter.parent().indexOf(splitter) == [0,splitter.parent().count()-1][i]
            ):
                def add_callback(i=i,splitter=splitter):
                    splitter.add(i)
                self.add_item(add_callback,menu,'Add %s' % (ab[i]))

        # equalize panes
        def eq(splitter=splitter.top()):
            splitter.equalize_sizes(recurse=True)
        self.add_item(eq, menu, 'Equalize all')

        if True:
            submenu = menu.addMenu('Debug')
            act = QtGui.QAction("Print splitter layout", self)
            def cb(splitter=splitter):
                print("\n%s\n" % 
                    splitter.layout_to_text(splitter.top().get_layout()))
            act.connect(act, Qt.SIGNAL('triggered()'), cb)
            submenu.addAction(act)  

        def load_items(menu, items):
            for i in items:
                if isinstance(i, dict):
                    for k in i:
                        load_items(menu.addMenu(k), i[k])
                else:
                    title, id_ = i
                    def cb(id_=id_):
                        splitter.context_cb(id_, index)
                    act = QtGui.QAction(title, self)
                    act.connect(act, Qt.SIGNAL('triggered()'), cb)
                    menu.addAction(act)              

        for provider in splitter.root.providers:
            if hasattr(provider, 'ns_context'):
                load_items(menu, provider.ns_context())

        menu.exec_(self.mapToGlobal(pos))

        for i in 0,1:
            widget[i].setStyleSheet(sheet[i])
    #@-others
#@+node:ekr.20110605121601.17966: ** class NestedSplitter (QSplitter)
class NestedSplitter(QtGui.QSplitter): 

    enabled = True
        # allow special behavior to be turned of at import stage
        # useful if other code must run to set up callbacks, that
        # other code can re-enable

    other_orientation = {
        QtConst.Vertical: QtConst.Horizontal,
        QtConst.Horizontal: QtConst.Vertical
    }

    #@+others
    #@+node:ekr.20110605121601.17967: *3* __init__ (NestedSplitter)
    def __init__(self,parent=None,orientation=QtConst.Horizontal,root=None):
        
        QtGui.QSplitter.__init__(self,orientation,parent)
            # This creates a NestedSplitterHandle.
            
        # g.trace('(NestedSplitter)')

        if root is None:
            root = self.top()
            if root == self:
                root.marked = None # Tuple: self,index,side-1,widget
                root.providers = []
                root.holders = {}

        self.root = root
    #@+node:ekr.20110605121601.17968: *3* __repr__
    def __repr__ (self):
        
        # parent = self.parent()
        # name = parent and parent.objectName() or '<no parent>'
        
        name = self.objectName() or '<no name>'
        
        return '(NestedSplitter) %s at %s' % (name,id(self))

    __str__ = __repr__
    #@+node:ekr.20110605121601.17969: *3* overrides of QSplitter methods
    #@+node:ekr.20110605121601.17970: *4* createHandle
    def createHandle(self, *args, **kargs):
        
        return NestedSplitterHandle(self)
    #@+node:tbrown.20110729101912.30820: *4* childEvent
    def childEvent(self, event):
        """If a panel client is closed not by us, there may be zero
        splitter handles left, so add an Action button"""
                    
        QtGui.QSplitter.childEvent(self, event)
        
        if not event.removed():
            return

        # don't leave a one widget splitter
        if self.count() == 1 and self.top() != self:
            self.parent().addWidget(self.widget(0))
            self.deleteLater()
            
        if self.count() == 1 and self.top() == self:
            self.insert(0)
    #@+node:ekr.20110605121601.17971: *3* add
    def add(self,side,w=None):

        orientation = self.other_orientation[self.orientation()]
        
        layout = self.parent().layout()

        if isinstance(self.parent(), NestedSplitter):
            # don't add new splitter if not needed, i.e. we're the
            # only child of a previosly more populated splitter
            self.parent().insertWidget(
                self.parent().indexOf(self) + side,
                NestedSplitterChoice(self.parent()))

        elif layout:
            new = NestedSplitter(None,orientation=orientation,
                root=self.root)
            # parent set by layout.insertWidget() below
            old = self
            pos = layout.indexOf(old)
            
            new.addWidget(old)
            if w is None:
                w = NestedSplitterChoice(new)
            new.insertWidget(side,w)

            layout.insertWidget(pos, new)
            
        else:
            # fail - parent is not NestedSplitter and has no layout
            pass
    #@+node:tbrown.20110621120042.22675: *3* add_adjacent
    def add_adjacent(self, what, widget_id, side='right-of'):
        
        layout = self.top().get_layout()
        
        def hunter(layout, id_):
            """Recursively look for this widget"""
            for n,i in enumerate(layout['content']):
                if (i == id_ or
                    (isinstance(i, QtGui.QWidget) and
                     (i.objectName() == id_ or i.__class__.__name__ == id_)
                    )
                   ):
                    return layout, n
                    
                if not isinstance(i, QtGui.QWidget):
                    # then it must be a layout dict
                    x = hunter(i, id_)
                    if x:
                        return x
            return None
        
        # find the layout containing widget_id
        l = hunter(layout, widget_id)
        
        if l is None:
            return False
        
        layout, pos = l
        
        if (layout['orientation'] == QtConst.Horizontal and
            side in ('right-of', 'left-of')
            or
            layout['orientation'] == QtConst.Vertical and
            side in ('above', 'below')):
            # put it in existing splitter
                
            if side in ('right-of', 'below'):
                pos += 1
            
            layout['splitter'].insert(pos, what)
            
        else:  # put it in a new splitter
        
            if side in ('right-of', 'left-of'):
                ns = NestedSplitter(root=self.root)
            else:
                ns = NestedSplitter(orientation=QtConst.Vertical,
                    root=self.root)
                
            old = layout['content'][pos]
            if not isinstance(old, QtGui.QWidget):  # see get_layout()
                old = layout['splitter']
                
            ns.insert(0, old)
            ns.insert(1 if side in ('right-of', 'below') else 0, what)
            
            layout['splitter'].insert(pos, ns)
            
        return True
    #@+node:ekr.20110605121601.17972: *3* choice_menu
    def choice_menu(self, button, pos):

        menu = QtGui.QMenu()
        
        index=self.indexOf(button)

        if (self.root.marked and 
            not self.invalid_swap(button, self.root.marked[3]) and
            self.top().max_count() > 2):
            act = QtGui.QAction("Move marked here", self)
            act.connect(act, Qt.SIGNAL('triggered()'), 
                lambda: self.replace_widget(button, self.root.marked[3]))
            menu.addAction(act)        

        for provider in self.root.providers:
            if hasattr(provider, 'ns_provides'):
                for title, id_ in provider.ns_provides():
                    def cb(id_=id_):
                        self.place_provided(id_, index)
                    act = QtGui.QAction(title, self)
                    act.connect(act, Qt.SIGNAL('triggered()'), cb)
                    menu.addAction(act)        

        if menu.isEmpty():
            act = QtGui.QAction("Nothing marked, and no options", self)
            menu.addAction(act)

        menu.exec_(button.mapToGlobal(pos))
    #@+node:tbrown.20110628083641.11723: *3* place_provided
    def place_provided(self, id_, index):
        
        provided = self.get_provided(id_)
        
        if provided is None:
            return
        
        self.replace_widget_at_index(index, provided)
        self.top().prune_empty()
        
        # user can set up one widget pane plus one Action pane, then move the
        # widget into the action pane, level 1 pane and no handles
        if self.top().max_count() < 2:
            print('Adding Action widget to maintain at least one handle')
            self.top().insert(0, NestedSplitterChoice(self.top()))
    #@+node:tbrown.20110628083641.11729: *3* context_cb
    def context_cb(self, id_, index):

        for provider in self.root.providers:
            if hasattr(provider, 'ns_do_context'):
                provided = provider.ns_do_context(id_, self, index)
                break
    #@+node:ekr.20110605121601.17973: *3* contains
    def contains(self, widget):

        """check if widget is a descendent of self"""

        for i in range(self.count()):
            if widget == self.widget(i):
                return True
            if isinstance(self.widget(i), NestedSplitter):
                if self.widget(i).contains(widget):
                    return True

        return False
    #@+node:ekr.20110605121601.17974: *3* handle_context
    def handle_context(self, index):

        widget = [
            self.widget(index-1),
            self.widget(index),
        ]

        neighbour = [ (i if isinstance(i, NestedSplitter) else None)
            for i in widget ]

        count = []
        for i in 0,1:
            if neighbour[i]:
                l = [ii.count() for ii in neighbour[i].self_and_descendants()]
                n = sum(l) - len(l) + 1  # count leaves, not splitters
                count.append(n)
            else:
                count.append(1)

        return widget, neighbour, count
    #@+node:tbrown.20110621120042.22920: *3* equalize_sizes
    def equalize_sizes(self, recurse=False):
        if not self.count():
            return
            
        for i in range(self.count()):
            self.widget(i).setHidden(False)
            
        size = sum(self.sizes()) / self.count()
        self.setSizes([size]*self.count())
        
        if recurse:
            for i in range(self.count()):
                if isinstance(self.widget(i), NestedSplitter):
                    self.widget(i).equalize_sizes(recurse=True)
    #@+node:ekr.20110605121601.17975: *3* insert
    def insert(self,index,w=None):
        
        if w is None:  # do NOT use 'not w', fails in PyQt 4.8
            w = NestedSplitterChoice(self)
            # A QWidget, with self as parent.
            # This creates the menu.

        self.insertWidget(index,w)
        
        self.equalize_sizes()
        
        return w
    #@+node:ekr.20110605121601.17976: *3* invalid_swap
    def invalid_swap(self,w0,w1):
        
        return (
            w0 == w1 or
            isinstance(w0,NestedSplitter) and w0.contains(w1) or
            isinstance(w1,NestedSplitter) and w1.contains(w0))
    #@+node:ekr.20110605121601.17977: *3* mark
    def mark(self, index, side):

        self.root.marked = (self, index, side-1,
            self.widget(index+side-1))
    #@+node:ekr.20110605121601.17978: *3* max_count
    def max_count(self):

        """find max widgets in this and child splitters"""

        counts = []
        count = 0
        for i in range(self.count()):
            count += 1
            if isinstance(self.widget(i), NestedSplitter):
                counts.append(self.widget(i).max_count())
                
        counts.append(count)

        return max(counts)

    #@+node:tbrown.20110627201141.11744: *3* register_provider
    def register_provider(self, provider):
        
        self.root.providers.append(provider)
    #@+node:ekr.20110605121601.17980: *3* remove & helper
    def remove(self, index, side):

        widget = self.widget(index+side-1)

        # clear marked if it's going to be deleted
        if (self.root.marked and (self.root.marked[3] == widget or
            isinstance(self.root.marked[3], NestedSplitter) and
            self.root.marked[3].contains(widget))):
            self.root.marked = None

        # send close signal to all children
        if isinstance(widget, NestedSplitter):
            
            count = widget.count()
            all_ok = True

            for splitter in widget.self_and_descendants():
                for i in range(splitter.count()-1, -1, -1):
                    all_ok &= (self.close_or_keep(splitter.widget(i)) is not False)

            if all_ok or count <= 0:
                widget.setParent(None)

        else:
            self.close_or_keep(widget)
    #@+node:ekr.20110605121601.17981: *4* close_or_keep
    def close_or_keep(self, widget, other_top=None):
        """when called from a closing secondary window, self.top() would
        be the top splitter in the closing window, and we need the client
        to specify the top of the primary window for us, in other_top"""

        if widget is None:
            return True

        for k in self.root.holders:
            if hasattr(widget, k):
                holder = self.root.holders[k]
                
                if holder == 'TOP':
                    holder = other_top or self.top()
                if hasattr(holder, "addTab"):
                    holder.addTab(widget, getattr(widget,k))
                else:
                    holder.addWidget(widget)
                return True
        else:
            if widget.close():
                widget.setParent(None)
                return True
        
        return False
                
    #@+node:ekr.20110605121601.17982: *3* replace_widget & replace_widget_at_index
    def replace_widget(self, old, new):

        self.insertWidget(self.indexOf(old), new)
        old.setParent(None)

        self.equalize_sizes()
           
    def replace_widget_at_index(self,index,new):
        
        '''Replace the widget at index with w.'''
        
        old = self.widget(index)
        if old != new:
            self.insertWidget(index,new)
            old.setParent(None)

        self.equalize_sizes()
    #@+node:ekr.20110605121601.17983: *3* rotate
    def rotate(self, descending=False):

        """Change orientation - current rotates entire hierachy, doing less
        is visually confusing because you end up with nested splitters with
        the same orientation - avoiding that would mean doing rotation by
        inserting out widgets into our ancestors, etc.
        """

        for i in self.top().self_and_descendants():
            if i.orientation() == QtConst.Vertical:
                i.setOrientation(QtConst.Horizontal)
            else:
                i.setOrientation(QtConst.Vertical)
    #@+node:ekr.20110605121601.17984: *3* self_and_descendants
    def self_and_descendants(self):

        """Yield self and all **NestedSplitter** descendants"""

        for i in range(self.count()):
            if isinstance(self.widget(i), NestedSplitter):
                for w in self.widget(i).self_and_descendants():
                    yield w
        yield self
    #@+node:ekr.20110605121601.17985: *3* split (NestedSplitter)
    def split(self,index,side,w=None,name=None):

        sizes = self.sizes()

        old = self.widget(index+side-1)
        #X old_name = old and old.objectName() or '<no name>'
        #X splitter_name = self.objectName() or '<no name>'
        
        if w is None:
            w = NestedSplitterChoice(self)

        if isinstance(old, NestedSplitter):
            old.addWidget(w)
            old.equalize_sizes()
            #X index = old.indexOf(w)
            #X return old,index # For viewrendered plugin.
        else:
            orientation = self.other_orientation[self.orientation()]
            new = NestedSplitter(self, orientation=orientation, root=self.root)
            #X if name: new.setObjectName(name)
            self.insertWidget(index+side-1, new)
            new.addWidget(old)
            new.addWidget(w)
            new.equalize_sizes()
            #X index = new.indexOf(w)
            #X return new,index # For viewrendered plugin.
            
        self.setSizes(sizes)
    #@+node:ekr.20110605121601.17986: *3* swap
    def swap(self, index):

        self.insertWidget(index-1, self.widget(index))
    #@+node:ekr.20110605121601.17987: *3* swap_with_marked
    def swap_with_marked(self, index, side):

        osplitter, oidx, oside, ow = self.root.marked

        idx = index+side-1
        # convert from handle index to widget index
        # 1 already subtracted from oside in mark()
        w = self.widget(idx)

        if self.invalid_swap(w, ow):
            return

        self.insertWidget(idx, ow)
        osplitter.insertWidget(oidx, w)

        self.root.marked = self, self.indexOf(ow), 0, ow
        self.equalize_sizes()
        osplitter.equalize_sizes()
    #@+node:ekr.20110605121601.17988: *3* top
    def top(self):

        """find top (outer) widget, which is not necessarily root"""

        top = self
        while isinstance(top.parent(), NestedSplitter):
            top = top.parent()

        return top
    #@+node:ekr.20110605121601.17989: *3* get_layout
    def get_layout(self, _saveable=False):
        """return {'orientation':QOrientation, 'content':[], 'splitter':ns}
        
        Where content is a list of widgets, or if a widget is a NestedSplitter, the
        result of that splitters call to get_layout().  splitter is the splitter
        which generated the dict.
        
        Usually you would call ns.top().get_layout()
        
        With _saveable==True (via get_saveable_layour()) content entry for
        non-NestedSplitter items is the provider ID string for the item, or
        'UNKNOWN', and the splitter entry is omitted.
        """
        
        ans = {
            'orientation': self.orientation(),
            'content': []
        }
        
        if not _saveable:
            ans['splitter'] = self
            
        ans['sizes'] = self.sizes()
        
        for i in range(self.count()):
            w = self.widget(i)
            if isinstance(w, NestedSplitter):
                ans['content'].append(w.get_layout(_saveable=_saveable))
            else:
                if _saveable:
                    ans['content'].append(getattr(w, '_ns_id', 'UNKNOWN'))
                else:
                    ans['content'].append(w)
                
        return ans
    #@+node:tbrown.20110628083641.11733: *3* get_saveable_layout
    def get_saveable_layout(self):
        
        return self.get_layout(_saveable=True)
    #@+node:tbrown.20110628083641.21154: *3* load_layout
    def load_layout(self, layout, level=0):
         
        self.setOrientation(layout['orientation'])
        found = 0
        
        if level == 0:
            for i in self.self_and_descendants():
                for n in range(i.count()):
                    i.widget(n)._in_layout = False
        
        for i in layout['content']:
            if isinstance(i, dict):
                new = NestedSplitter(root=self.root, parent=self)
                new._in_layout = True
                self.insert(found, new)
                found += 1
                new.load_layout(i, level+1)
            else:
                provided = self.get_provided(i)
                if provided:
                    self.insert(found, provided)
                    provided._in_layout = True
                    found += 1
                else:
                    print('NO %s'%i)
                 
        self.prune_empty()
        
        if self.count() != len(layout['sizes']):
            
            not_in_layout = set()
            
            for i in self.self_and_descendants():
                for n in range(i.count()):
                    c = i.widget(n)
                    if not (hasattr(c, '_in_layout') and c._in_layout):
                        not_in_layout.add(c)
                        
            for i in not_in_layout:
                self.close_or_keep(i)
        
            self.prune_empty()
        
        if self.count() == len(layout['sizes']):
            self.setSizes(layout['sizes'])
        else:
            print('Wrong pane count at level %d, count:%d, sizes:%d'%(
                level, self.count(), len(layout['sizes'])))
            self.equalize_sizes()
    #@+node:tbrown.20110628083641.21156: *3* prune_empty
    def prune_empty(self):
        
        for i in range(self.count()-1, -1, -1):
            w = self.widget(i)
            if isinstance(w, NestedSplitter):
                if w.max_count() == 0:
                    w.setParent(None)
                    # w.deleteLater()
    #@+node:tbrown.20110628083641.21155: *3* get_provided
    def find_by_id(self, id_):
        for s in self.self_and_descendants():                  
            for i in range(s.count()):
                if getattr(s.widget(i), '_ns_id', None) == id_:
                    return s.widget(i)
        return None

    def get_provided(self, id_):
        """IMPORTANT: nested_splitter should set the _ns_id attribute *only*
        if the provider doesn't do it itself.  That allows the provider to
        encode state information in the id.
        
        Also IMPORTANT: nested_splitter should call all providers for each id_, not
        just providers which previously advertised the id_.  E.g. a provider which
        advertises leo_bookmarks_show may also be the correct provider for
        leo_bookmarks_show:4532.234 - let the providers decide in ns_provide().
        """
        for provider in self.root.providers:
            if hasattr(provider, 'ns_provide'):
                provided = provider.ns_provide(id_)
                if provided:
                    if provided == 'USE_EXISTING':
                        # provider claiming responsibility, and saying
                        # we already have it, i.e. it's a singleton
                        w = self.top().find_by_id(id_)
                        if w:
                            if not hasattr(w, '_ns_id'):
                                # IMPORTANT: see docstring
                                w._ns_id = id_
                            return w
                    else:
                        if not hasattr(provided, '_ns_id'):
                            # IMPORTANT: see docstring
                            provided._ns_id = id_
                        return provided
        return None
    #@+node:ekr.20110605121601.17990: *3* layout_to_text
    def layout_to_text(self, layout, _depth=0, _ans=[]):
        """convert the output from get_layout to indented human readable text
        for development/debugging"""
        
        if _depth == 0:
            _ans = []
        
        orientation = 'vertical'
        if layout['orientation'] == QtConst.Horizontal:
             orientation = 'horizontal'
             
        _ans.append("%s%s (%s) - %s" % (
            '   '*_depth,
            layout['splitter'].__class__.__name__,
            layout['splitter'].objectName(),
            orientation,
        ))
        
        _depth += 1
        for n,i in enumerate(layout['content']):
            if isinstance(i, dict):
                self.layout_to_text(i, _depth, _ans)
            else:
                _ans.append("%s%s (%s) from %s" % (
                   '   '*_depth,
                   i.__class__.__name__,
                   str(i.objectName()),  # not QString
                   getattr(i, '_ns_id', 'UNKNOWN')
                ))
                
        if _depth == 1:
            return '\n'.join(_ans)
    #@-others
#@+node:ekr.20110605121601.17991: ** main
def main():
    
    app = Qt.QApplication(sys.argv)

    wdg = DemoWidget()
    wdg2 = DemoWidget()

    splitter = NestedSplitter()
    splitter.addWidget(wdg)
    splitter.addWidget(wdg2)

    class DemoProvider:
        def ns_provides(self):
            return[('Add demo widget', '_add_demo_widget')] 
        def ns_provide(seld, id_):
            if id_ == '_add_demo_widget':
                return DemoWidget()

    splitter.register_provider(DemoProvider())

    holder = QtGui.QWidget()
    holder.setLayout(QtGui.QVBoxLayout())
    holder.layout().setContentsMargins(QtCore.QMargins(0,0,0,0))
    holder.layout().addWidget(splitter)
    holder.show()

    app.exec_()
#@-others

if __name__ == "__main__":
    main()
#@-leo
