#@+leo-ver=5-thin
#@+node:ekr.20170530024520.2: * @file importers/lua.py
'''
The @auto importer for the lua language.

Created 2017/05/30 by the `importer;;` abbreviation.
'''
import leo.core.leoGlobals as g
import leo.plugins.importers.linescanner as linescanner
Importer = linescanner.Importer
#@+others
#@+node:ekr.20170530024520.3: ** class Lua_Importer
class Lua_Importer(Importer):
    '''The importer for the lua lanuage.'''

    def __init__(self, importCommands):
        '''Lua_Importer.__init__'''
        # Init the base class.
        Importer.__init__(self,
            importCommands,
            language = 'lua',
            state_class = Lua_ScanState,
            strict = False,
        )
        self.start_stack = []
            # Contains entries for all constructs that end with 'end'.
        
    # Define necessary overrides.
    #@+others
    #@+node:ekr.20170530024520.5: *3* lua_i.clean_headline
    def clean_headline(self, s):
        '''Return a cleaned up headline s.'''
        s = s.strip()
        tag = 'function'
        if s.startswith(tag):
            s = s[len(tag):]
        i = s.find('(')
        if i > -1:
            s = s[:i]
        return s.strip()
    #@+node:ekr.20170530085347.1: *3* lua_i.cut_stack
    def cut_stack(self, new_state, stack):
        '''Cut back the stack until stack[-1] matches new_state.'''
        trace = False # and g.unitTesting
        if trace:
            g.trace(new_state)
            g.printList(stack)
        assert len(stack) > 1 # Fail on entry.
        # function/end's are strictly nested, so this suffices.
        stack.pop()
        # Restore the guard entry if necessary.
        if len(stack) == 1:
            if trace: g.trace('RECOPY:', stack)
            stack.append(stack[-1])
        assert len(stack) > 1 # Fail on exit.
        if trace: g.trace('new target.p:', stack[-1].p.h)
    #@+node:ekr.20170530040554.1: *3* lua_i.ends_block
    def ends_block(self, line, new_state, prev_state, stack):
        '''True if line ends the block.'''
        if prev_state.context:
            return False
        if line.strip().startswith('end'):
            if self.start_stack:
                top = self.start_stack.pop()
                return top == 'function'
            else:
                g.trace('too many "end" statements')
        return False
    #@+node:ekr.20170530031729.1: *3* lua_i.get_new_dict
    #@@nobeautify

    def get_new_dict(self, context):
        '''The scan dict for the lua language.'''
        trace = False and g.unitTesting
        comment, block1, block2 = self.single_comment, self.block1, self.block2
        assert comment
        
        def add_key(d, pattern, data):
            key = pattern[0]
            aList = d.get(key,[])
            aList.append(data)
            d[key] = aList

        if context:
            d = {
                # key    kind   pattern  ends?
                '\\':   [('len+1', '\\', None),],
                '"':    [('len', '"',    context == '"'),],
                "'":    [('len', "'",    context == "'"),],
            }
            # End Lua long brackets.
            for i in range(10):
                open_pattern = '[%s[' % ('='*i)
                pattern = ']%s]' % ('='*i)
                add_key(d, pattern, ('len', pattern, context==open_pattern))
            if block1 and block2:
                add_key(d, block2, ('len', block2, True))
        else:
            # Not in any context.
            d = {
                # key    kind pattern new-ctx  deltas
                '\\':[('len+1', '\\', context, None),],
                '"':    [('len', '"', '"',     None),],
                "'":    [('len', "'", "'",     None),],
                '{':    [('len', '{', context, (1,0,0)),],
                '}':    [('len', '}', context, (-1,0,0)),],
                '(':    [('len', '(', context, (0,1,0)),],
                ')':    [('len', ')', context, (0,-1,0)),],
                '[':    [('len', '[', context, (0,0,1)),],
                ']':    [('len', ']', context, (0,0,-1)),],
            }
            # Start Lua long brackets.
            for i in range(10):
                pattern = '[%s[' % ('='*i)
                add_key(d, pattern, ('len', pattern, pattern, None))
            if comment:
                add_key(d, comment, ('all', comment, '', None))
            if block1 and block2:
                add_key(d, block1, ('len', block1, block1, None))
        if trace: g.trace('created %s dict for %4r state ' % (self.name, context))
        return d
    #@+node:ekr.20170530035601.1: *3* lua_i.starts_block
    def starts_block(self, i, lines, new_state, prev_state):
        '''True if the new state starts a block.'''
        if prev_state.context:
            return False
        line = lines[i].strip()
        table = ('do', 'for', 'function', 'if')
        for z in table:
            if line.startswith(z):
                self.start_stack.append(z)
                break
        return line.startswith('function')
    #@-others
#@+node:ekr.20170530024520.7: ** class class Lua_ScanState
class Lua_ScanState:
    '''A class representing the state of the lua line-oriented scan.'''
    
    def __init__(self, d=None):
        if d:
            prev = d.get('prev')
            self.context = prev.context
        else:
            self.context = ''

    def __repr__(self):
        return "Lua_ScanState context: %r " % (self.context)
    __str__ = __repr__

    #@+others
    #@+node:ekr.20170530024520.8: *3* lua_state.level
    def level(self):
        '''Lua_ScanState.level.'''
        return 0
            # Never used.
    #@+node:ekr.20170530024520.9: *3* lua_state.update
    def update(self, data):
        '''
        Lua_ScanState.update

        Update the state using the 6-tuple returned by v2_scan_line.
        Return i = data[1]
        '''
        context, i, delta_c, delta_p, delta_s, bs_nl = data
        # All ScanState classes must have a context ivar.
        self.context = context
        # self.curlies += delta_c  
        # self.bs_nl = bs_nl
        # self.parens += delta_p
        # self.squares += delta_s
        return i
    #@-others

#@-others
importer_dict = {
    'class': Lua_Importer,
    'extensions': ['.lua',],
}
#@@language python
#@@tabwidth -4


#@-leo
