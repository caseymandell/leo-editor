#@+leo-ver=5-thin
#@+node:ekr.20150521115018.1: * @file leoBeautify.py
"""Leo's beautification classes."""
#@+<< leoBeautify imports >>
#@+node:ekr.20150530081336.1: **   << leoBeautify imports >>
try:
    import leo.core.leoGlobals as g
    import leo.core.leoAst as leoAst
except ImportError:
    # Allow main() to run in any folder containing leoGlobals.py
    # pylint: disable=relative-import
    import leoGlobals as g

    # Create a dummy decorator.

    def command(func):
        return func

    g.command = command

import ast
import io
import optparse
import os
import re
import sys
import time
import token as token_module
import tokenize

try:
    # pylint: disable=import-error
        # We can't assume the user has this.
    import black
except Exception:
    black = None
#@-<< leoBeautify imports >>
#@+others
#@+node:ekr.20191104201534.1: **   Top-level functions
#@+node:ekr.20150528131012.1: *3* Beautify:commands
#@+node:ekr.20191025084338.1: *4* beautify commands
#@+node:ekr.20150528131012.3: *5* beautify-c
@g.command('beautify-c')
@g.command('pretty-print-c')
def beautifyCCode(event):
    """Beautify all C code in the selected tree."""
    c = event.get('c')
    if c:
        CPrettyPrinter(c).pretty_print_tree(c.p)
#@+node:ekr.20150528131012.4: *5* beautify-node
@g.command('beautify-node')
@g.command('pretty-print-node')
def prettyPrintPythonNode(event):
    """Beautify a single Python node."""
    c = event.get('c')
    if c:
        PythonTokenBeautifier(c).beautify_node(c.p)
    
    
#@+node:ekr.20150528131012.5: *5* beautify-tree
@g.command('beautify-tree')
@g.command('pretty-print-tree')
def beautifyPythonTree(event):
    """Beautify all python files in the selected outline."""
    c = event.get('c')
    if c:
        PythonTokenBeautifier(c).beautify_tree(c.p)
#@+node:ekr.20191025084349.1: *4* blacken commands
#@+node:ekr.20190830043650.1: *5* blacken-check-tree
@g.command('blkc')
@g.command('blacken-check-tree')
def blacken_check_tree(event):
    """
    Run black on all nodes of the selected tree, reporting only errors.
    """
    c = event.get('c')
    if not c:
        return
    if black:
        BlackCommand(c).blacken_tree(c.p, diff_flag=False, check_flag=True)
    else:
        g.es_print('can not import black')
#@+node:ekr.20190829163640.1: *5* blacken-diff-node
@g.command('blacken-diff-node')
def blacken_diff_node(event):
    """
    Run black on the selected node.
    """
    c = event.get('c')
    if not c:
        return
    if black:
        BlackCommand(c).blacken_node(c.p, diff_flag=True)
    else:
        g.es_print('can not import black')
#@+node:ekr.20190829163652.1: *5* blacken-diff-tree
@g.command('blkd')
@g.command('blacken-diff-tree')
def blacken_diff_tree(event):
    """
    Run black on all nodes of the selected tree,
    or the first @<file> node in an ancestor.
    """
    c = event.get('c')
    if not c:
        return
    if black:
        BlackCommand(c).blacken_tree(c.p, diff_flag=True)
    else:
        g.es_print('can not import black')
#@+node:ekr.20190725155006.1: *5* blacken-node
@g.command('blacken-node')
def blacken_node(event):
    """
    Run black on the selected node.
    """
    c = event.get('c')
    if not c:
        return
    if black:
        BlackCommand(c).blacken_node(c.p, diff_flag=False)
    else:
        g.es_print('can not import black')
#@+node:ekr.20190729105252.1: *5* blacken-tree
@g.command('blk')
@g.command('blacken-tree')
def blacken_tree(event):
    """
    Run black on all nodes of the selected tree,
    or the first @<file> node in an ancestor.
    """
    c = event.get('c')
    if not c:
        return
    if black:
        BlackCommand(c).blacken_tree(c.p, diff_flag=False)
    else:
        g.es_print('can not import black')
#@+node:ekr.20191025084403.1: *4* fstringify commands
#@+node:ekr.20191025072511.1: *5* fstringify-file
@g.command('fstringify-file')
def fstringify_file(event):
    """fstringify the nearest @<file> node."""
    c = event.get('c')
    if c:
        FstringifyTokens(c).fstringify_file()
#@+node:ekr.20191025084230.1: *5* fstringify-node
@g.command('fstringify-node')
def fstringity_node(event):
    """fstringity the selected node."""
    c = event.get('c')
    if c:
        FstringifyTokens(c).fstringify_node(c.p)
#@+node:ekr.20191025084237.1: *5* fstringify-tree
@g.command('fstringify-tree')
def fstringify_tree(event):
    """
    fstringify all nodes of the selected tree,
    or the first @<file> node in an ancestor.
    """
    c = event.get('c')
    if c:
        FstringifyTokens(c).fstringify_tree(c.p)
#@+node:ekr.20191028140926.1: *3* Beautify:test functions
#@+node:ekr.20191101150059.1: *4* function: check_roundtrip 
import unittest
# from tokenize import tokenize, untokenize

def check_roundtrip(f, expect_failure=False):
    """
    Called from unit tests in unitTest.leo.
    
    Test python's token.untokenize method and Leo's Untokenize class.
    """
    check_python_roundtrip(f, expect_failure)
    check_leo_roundtrip(f)

def check_leo_roundtrip(code, trace=False):
    """Check Leo's Untokenize class"""
    # pylint: disable=import-self
    import leo.core.leoBeautify as leoBeautify
    assert isinstance(code, str), repr(code)
    tokens = tokenize.tokenize(io.BytesIO(code.encode('utf-8')).readline)
    u = leoBeautify.InputTokenizer()
    u.trace=False and not g.unitTesting
    result_tokens = u.create_input_tokens(code, tokens)
    result = ''.join([z.to_string() for z in result_tokens])
    unittest.TestCase().assertEqual(code, result)

def check_python_roundtrip(f, expect_failure):
    """
    This is tokenize.TestRoundtrip.check_roundtrip, without the wretched fudges.
    """
    if isinstance(f, str):
        code = f.encode('utf-8')
    else:
        code = f.read()
        f.close()
    readline = iter(code.splitlines(keepends=True)).__next__
    tokens = list(tokenize.tokenize(readline))
    bytes = tokenize.untokenize(tokens)
    readline5 = iter(bytes.splitlines(keepends=True)).__next__
    result_tokens = list(tokenize.tokenize(readline5))
    if expect_failure:
        unittest.TestCase().assertNotEqual(result_tokens, tokens)
    else:
        unittest.TestCase().assertEqual(result_tokens, tokens)
#@+node:ekr.20191029184103.1: *4* function: show
def show(obj, tag, dump):
    print(f"{tag}...\n")
    if dump:
        g.printObj(obj)
    else:
        print(obj)
#@+node:ekr.20191028141311.1: *4* test_FstringifyTokens
def test_FstringifyTokens(c, contents,
    dump=True,
    dump_input_tokens=False,
    dump_output_tokens=False,
):
    # pylint: disable=import-self
    import tokenize
    import leo.core.leoBeautify as leoBeautify
    # Tokenize.
    tokens = list(tokenize.tokenize(io.BytesIO(contents.encode('utf-8')).readline))
    # Create a list of input tokens (BeautifierTokens).
    x = leoBeautify.FstringifyTokens(c)
    x.dump_input_tokens = dump_input_tokens
    x.dump_output_tokens = dump_output_tokens
    # Scan the input tokens, creating, a string.
    results = x.scan_all_tokens(contents, tokens)
    # Show results.
    print('')
    show(contents, 'Contents', dump=dump)
    print('')
    show(results, 'Results', dump=dump)
#@+node:ekr.20191028140946.1: *4* test_NullTokenBeautifier
def test_NullTokenBeautifier(c, contents,
    dump=True,
    dump_input_tokens=False,
    dump_output_tokens=False,
):

    # pylint: disable=import-self
    import tokenize
    import leo.core.leoBeautify as leoBeautify
    # Tokenize.
    tokens = list(tokenize.tokenize(io.BytesIO(contents.encode('utf-8')).readline))
    # Untokenize.
    x = leoBeautify.NullTokenBeautifier(c)
    x.dump_input_tokens = dump_input_tokens
    x.dump_output_tokens = dump_output_tokens
    results = x.scan_all_tokens(contents, tokens)
    # Show results.
    show(contents, 'Contents', dump=dump)
    print('')
    show(results, 'Results', dump=dump)
    return contents == results
#@+node:ekr.20191029184028.1: *4* test_PythonTokenBeautifier
def test_PythonTokenBeautifier(c, contents,
    dump=True,
    dump_input_tokens=False,
    dump_output_tokens=False,
):

    # pylint: disable=import-self
    import tokenize
    import leo.core.leoBeautify as leoBeautify
    # Create 5-tuples.
    tokens = list(tokenize.tokenize(io.BytesIO(contents.encode('utf-8')).readline))
    # Beautify.
    x = leoBeautify.PythonTokenBeautifier(c)
    x.dump_input_tokens = dump_input_tokens
    x.dump_output_tokens = dump_output_tokens
    results = x.scan_all_tokens(contents, tokens)
    # Show results.
    print('')
    show(contents, 'Contents', dump)
    print('')
    show(results, 'Results', dump)
    return results.strip() == contents.strip()
#@+node:ekr.20150530061745.1: *3* function: main & helpers
def main():
    """External entry point for Leo's beautifier."""
    t1 = time.process_time()
    base = g.os_path_abspath(os.curdir)
    files, options = scan_options()
    for path in files:
        path = g.os_path_finalize_join(base, path)
        beautify(options, path)
    print(f'beautified {len(files)} files in {time.process_time()-t1:4.2f} sec.')
#@+node:ekr.20150601170125.1: *4* beautify (stand alone)
def beautify(options, path):
    """Beautify the file with the given path."""
    fn = g.shortFileName(path)
    s, e = g.readFileIntoString(path)
    if not s:
        return
    print(f"beautifying {fn}")
    try:
        s1 = g.toEncodedString(s)
        node1 = ast.parse(s1, filename='before', mode='exec')
    except IndentationError:
        g.warning(f"IndentationError: can't check {fn}")
        return
    except SyntaxError:
        g.warning(f"SyntaxError: can't check {fn}")
        return
    readlines = g.ReadLinesClass(s).next
    tokens = list(tokenize.generate_tokens(readlines))
    x = PythonTokenBeautifier(c=None)
    # Compute the tokens.
    s2 = x.scan_all_tokens(s, tokens)
    try:
        s2_e = g.toEncodedString(s2)
        node2 = ast.parse(s2_e, filename='before', mode='exec')
    except IndentationError:
        g.warning(f"{fn}: IndentationError in result")
        g.es_print(f"{fn} will not be changed")
        g.printObj(s2, tag='RESULT')
        return
    except SyntaxError:
        g.warning(f"{fn}: Syntax error in result")
        g.es_print(f"{fn} will not be changed")
        g.printObj(s2, tag='RESULT')
        return
    except Exception:
        g.warning(f"{fn}: Unexpected exception creating the \"after\" parse tree")
        g.es_print(f"{fn} will not be changed")
        g.es_exception()
        g.printObj(s2, tag='RESULT')
        return
    ok = leoAst.compare_asts(node1, node2)
    if not ok:
        print(f"failed to beautify {fn}")
        return
    with open(path, 'wb') as f:
        f.write(s2_e)
#@+node:ekr.20150601162203.1: *4* scan_options (stand alone)
def scan_options():
    """Handle all options. Return a list of files."""
    # This automatically implements the --help option.
    usage = "usage: python -m leo.core.leoBeautify file1, file2, ..."
    parser = optparse.OptionParser(usage=usage)
    add = parser.add_option
    add(
        '-d',
        '--debug',
        action='store_true',
        dest='debug',
        help='print the list of files and exit',
    )
    # add('-k', '--keep-blank-lines', action='store_true', dest='keep',
        # help='keep-blank-lines')
    # Parse the options.
    options, files = parser.parse_args()
    if options.debug:
        # Print the list of files and exit.
        g.trace('files...', files)
        sys.exit(0)
    return files, options
#@+node:ekr.20150602154951.1: *3* function: should_beautify
def should_beautify(p):
    """
    Return True if @beautify is in effect for node p.
    Ambiguous directives have no effect.
    """
    for p2 in p.self_and_parents(copy=False):
        d = g.get_directives_dict(p2)
        if 'killbeautify' in d:
            return False
        if 'beautify' in d and 'nobeautify' in d:
            if p == p2:
                # honor whichever comes first.
                for line in g.splitLines(p2.b):
                    if line.startswith('@beautify'):
                        return True
                    if line.startswith('@nobeautify'):
                        return False
                g.trace('can not happen', p2.h)
                return False
            # The ambiguous node has no effect.
            # Look up the tree.
            pass
        elif 'beautify' in d:
            return True
        if 'nobeautify' in d:
            # This message would quickly become annoying.
            # g.warning(f"{p.h}: @nobeautify")
            return False
    # The default is to beautify.
    return True
#@+node:ekr.20150602204440.1: *3* function: should_kill_beautify
def should_kill_beautify(p):
    """Return True if p.b contains @killbeautify"""
    return 'killbeautify' in g.get_directives_dict(p)
#@+node:ekr.20191027164507.1: **  class NullTokenBeautifier
class NullTokenBeautifier:
    """
    A token-based beautifier that should leave source code unchanged.
    
    This class is based on the Untokenizer class in python's tokenize
    module.
    """

    undo_type = "Null Undo Type"  # Should be overridden in subclasses if undoable.
    
    dump_on_error = False  # True dump tokens on any ast errors.
    dump_input_tokens = False  # True: scan_all_tokens dumps input tokens.
    dump_output_tokens = False  # True: scan_all_tokens dumps output tokens.
    
    #@+others
    #@+node:ekr.20191101044034.1: *3*  null_tok_b: Birth
    #@+node:ekr.20191029014023.2: *4* null_tok_b.ctor
    def __init__(self, c):
        self.c = c
        self.changed = None
        self.code_list = []
        self.kind = None
        self.prev_input_token = None
        self.prev_output_token = None
        self.tab_width = None
        self.tokens = []
        # Statistics...
        # Only ptb.prettyPrintNode updates the stats.
        self.errors = 0
        self.n_changed_nodes = 0
        self.n_input_tokens = 0
        self.n_output_tokens = 0
        self.n_strings = 0
        self.parse_time = 0.0
        self.tokenize_time = 0.0
        self.beautify_time = 0.0
        self.check_time = 0.0
        self.total_time = 0.0
        # Update per-commander settings.
        self.reload_settings()
    #@+node:ekr.20191029014023.3: *4* null_tok_b.reload_settings
    def reload_settings(self):
        c = self.c
        self.tab_width = abs(c.tab_width) if c else 4
    #@+node:ekr.20191028074723.1: *3*  null_tok_b: May be overridden in subclasses...
    #@+node:ekr.20191028020116.1: *4* null_tok_b.do_token
    def do_token(self, token):
        """
        Handle one input token. Should be overridden in subclasses.
        
        This NullTokenBeautifier method just copies the token to the output list.
        """
        self.code_list.append(token)
    #@+node:ekr.20191028072954.1: *4* null_tok_b.file_end
    def file_end(self):
        """
        Do any end-of file processing.
        
        May be overridden in subclasses.
        """
        # Subclasses may ensure that the file ends with a newline.
        # self.add_token('line-end', '\n')
        self.add_token('file-end')
    #@+node:ekr.20191028075123.1: *4* null_tok_b.file_start
    def file_start(self):
        """
        Do any start-of-file processing.
        
        May be overridden in subclasses.
        
        The file-start token has already been added to self.code_list.
        """
        pass
    #@+node:ekr.20191029014023.9: *3*  null_tok_b: Utils...
    #@+node:ekr.20191029014023.10: *4* null_tok_b.end_undo
    def end_undo(self):
        """Complete undo processing."""
        c, u = self.c, self.c.undoer
        if self.changed:
            # Tag the end of the command.
            u.afterChangeGroup(c.p, self.undo_type, dirtyVnodeList=self.dirtyVnodeList)
    #@+node:ekr.20191029014023.11: *4* null_tok_b.find_root
    def find_root(self):
        """
        Return the nearest ancestor @<file> node, or None.
        Issue error messages if necessary.
        """
        c, p = self.c, self.c.p

        def predicate(p):
            return p.isAnyAtFileNode() and p.h.strip().endswith('.py')

        for p in p.self_and_parents():
            if predicate(p):
                break
        else:
            g.es_print(f"not in any @<file> tree: {c.p.h}")
            return None
        filename = p.anyAtFileNodeName()
        basedir = g.os_path_finalize(os.path.dirname(c.fileName()))
        path = g.os_path_finalize_join(basedir, filename)
        if os.path.exists(path):
            return path
        g.es_print(f"file not found: {filename} in {basedir}")
        return None
    #@+node:ekr.20191029014023.12: *4* null_tok_b.print_stats
    def print_stats(self):
        print(
            f"{'='*10} stats\n\n"
            f"changed nodes  {self.n_changed_nodes:4}\n"
            f"tokens         {self.n_input_tokens:4}\n"
            f"len(code_list) {self.n_output_tokens:4}\n"
            f"len(s)         {self.n_strings:4}\n"
            f"\ntimes (seconds)...\n"
            f"parse          {self.parse_time:4.2f}\n"
            f"tokenize       {self.tokenize_time:4.2f}\n"
            f"format         {self.beautify_time:4.2f}\n"
            f"check          {self.check_time:4.2f}\n"
            f"total          {self.total_time:4.2f}"
        )
    #@+node:ekr.20191029014023.13: *4* null_tok_b.replace_body
    def replace_body(self, p, s):
        """Undoably replace the body."""
        c, u = self.c, self.c.undoer
        undoType = self.undo_type
        if p.b == s:
            return
        self.n_changed_nodes += 1
        if not self.changed:
            # Start the group.
            u.beforeChangeGroup(p, undoType)
            self.changed = True
            self.dirtyVnodeList = []
        undoData = u.beforeChangeNodeContents(p)
        c.setBodyString(p, s)
        dirtyVnodeList2 = p.setDirty()
        self.dirtyVnodeList.extend(dirtyVnodeList2)
        u.afterChangeNodeContents(p, undoType, undoData, dirtyVnodeList=self.dirtyVnodeList)
    #@+node:ekr.20191029014023.14: *4* null_tok_b.token_description
    def token_description(self, token):
        """Return a summary of token's kind & value"""
        t1, t2, t3, t4, t5 = token
        kind = token_module.tok_name[t1].lower()
        val = g.toUnicode(t2)
        return f"{kind:>15} {val}"
    #@+node:ekr.20191029014023.15: *4* null_tok_b.tokenize_string
    def tokenize_string(self, contents, filename):
        """
        Return (ast_node, tokens) from the contents of the given file.
        """
        t1 = time.process_time()
        # Generate the tokens.
        readlines = g.ReadLinesClass(contents).next
        tokens = list(tokenize.generate_tokens(readlines))
        # Update stats.
        t2 = time.process_time()
        self.tokenize_time += t2 - t1
        return tokens
    #@+node:ekr.20191028072257.1: *3* null_tok_b.add_input_token
    def add_input_token(self, kind, value=''):
        """
        Add a token to the input list.
        
        The blank-lines token is the only token whose value isn't a string.
        BeautifierToken.to_string() ignores such tokens.
        """
        if kind != 'blank-lines':
            assert isinstance(value, str), g.callers()
        tok = BeautifierToken(kind, value)
        self.tokens.append(tok)
        self.prev_input_token = self.tokens[-1]
    #@+node:ekr.20191029014023.7: *3* null_tok_b.add_token
    def add_token(self, kind, value=''):
        """Add a token to the code list."""
        tok = BeautifierToken(kind, value)
        self.code_list.append(tok)
        self.prev_output_token = self.code_list[-1]
    #@+node:ekr.20191028070535.1: *3* null_tok_b.scan_all_tokens
    def scan_all_tokens(self, contents, tokens):
        """
        Use two *distinct* passes to convert tokens (an iterable of 5-tuples)
        to a result.
            
        Pass 1: Create self.tokens, a *list* (not generator) of InputTokens.
                The look_ahead method look aheads in this list.
                
        Pass 2: Call self.do_token(token) for each token in input_list.
                Subclasses may delete tokens from input_list.
                
        Returns the string created from the output list.
        
        Sub-classes should *not* need to override this method.
        """
        # Init state. (was in ctor).
        self.prev_row = 1
        self.prev_col = 0
        self.encoding = None  # Not used!
        # Init the input_list,
        self.prev_input_token = None
        self.tokens = []
        # Convert 5-tuples to a list (not a generator) of BeautifierTokens.
        self.tokens = InputTokenizer().create_input_tokens(contents, tokens)
        if self.dump_input_tokens:
            g.printObj(self.tokens, tag='INPUT TOKENS')
        # Init the output list.
        self.code_list = []
        self.prev_output_token = None
        self.add_token('file-start')
        # Allow subclasses to init state.
        self.file_start()
        # Generate output tokens.
        # Important: self.tokens may *mutate* in this loop.
        while self.tokens:
            token = self.tokens.pop(0)
            self.do_token(token)
        # Allow last-minute adjustments.
        self.file_end()
        if self.dump_output_tokens:
            g.printObj(self.code_list, tag='OUTPUT TOKENS')
        # Return the string result.
        return ''.join([z.to_string() for z in self.code_list])
    #@-others
#@+node:ekr.20150523132558.1: ** class BeautifierToken
class BeautifierToken:
    """A class representing both input and output tokens"""

    def __init__(self, kind, value):
        self.kind = kind
        self.value = value
        self.line = ''
            # The entire line containing the token. Same as token.line.
        self.line_number = 0
            # The line number, for errors. Same as token.start[0]

    def __repr__(self):
        # g.printObj calls repr.
        val = len(self.value) if self.kind == 'line-indent' else repr(self.value)
        return f"{self.kind:12} {val}"

    def __str__(self):
        val = len(self.value) if self.kind == 'line-indent' else repr(self.value)
        return f"{self.kind} {val}"

    def to_string(self):
        """
        Convert an output token to a string.
        Note: repr shows the length of line-indent string.
        """
        return self.value if isinstance(self.value, str) else ''
#@+node:ekr.20190725154916.1: ** class BlackCommand
class BlackCommand:
    """A class to run black on all Python @<file> nodes in c.p's tree."""

    # tag1 must be executable, and can't be pass.
    tag1 = "if 1: print('') # black-tag1:::"
    tag2 = ":::black-tag2"
    tag3 = "# black-tag3:::"

    def __init__(self, c):
        self.c = c
        self.wrapper = c.frame.body.wrapper
        self.reloadSettings()

    #@+others
    #@+node:ekr.20190926105124.1: *3* black.reloadSettings
    #@@nobeautify

    def reloadSettings(self):
        c = self.c
        keep_comments = c.config.getBool('black-keep-comment-indentation', default=True)
        self.sanitizer = SyntaxSanitizer(c, keep_comments)
        self.line_length = c.config.getInt("black-line-length") or 88
        # This should be on a single line,
        # so the check-settings script in leoSettings.leo will see them.
        self.normalize_strings = c.config.getBool("black-string-normalization", default=False)
    #@+node:ekr.20190725154916.7: *3* black.blacken_node
    def blacken_node(self, root, diff_flag, check_flag=False):
        """Run black on all Python @<file> nodes in root's tree."""
        c = self.c
        if not black or not root:
            return
        t1 = time.process_time()
        self.changed, self.errors, self.total = 0, 0, 0
        self.undo_type = 'blacken-node'
        self.blacken_node_helper(root, check_flag, diff_flag)
        t2 = time.process_time()
        if not g.unitTesting:
            print(
                f'{root.h}: scanned {self.total} node{g.plural(self.total)}, '
                f'changed {self.changed} node{g.plural(self.changed)}, '
                f'{self.errors} error{g.plural(self.errors)} '
                f'in {t2-t1:5.2f} sec.'
            )
        if self.changed or self.errors:
            c.redraw()
    #@+node:ekr.20190729065756.1: *3* black.blacken_tree
    def blacken_tree(self, root, diff_flag, check_flag=False):
        """Run black on all Python @<file> nodes in root's tree."""
        c = self.c
        if not black or not root:
            return
        t1 = time.process_time()
        self.changed, self.errors, self.total = 0, 0, 0
        undo_type = 'blacken-tree'
        bunch = c.undoer.beforeChangeTree(root)
        # Blacken *only* the selected tree.
        changed = False
        for p in root.self_and_subtree():
            if self.blacken_node_helper(p, check_flag, diff_flag):
                changed = True
        if changed:
            c.setChanged(True)
            c.undoer.afterChangeTree(root, undo_type, bunch)
        t2 = time.process_time()
        if not g.unitTesting:
            print(
                f'{root.h}: scanned {self.total} node{g.plural(self.total)}, '
                f'changed {self.changed} node{g.plural(self.changed)}, '
                f'{self.errors} error{g.plural(self.errors)} '
                f'in {t2-t1:5.2f} sec.'
            )
        if self.changed and not c.changed:
            c.setChanged(True)
        if self.changed or self.errors:
            c.redraw()
    #@+node:ekr.20190726013924.1: *3* black.blacken_node_helper (changed)
    def blacken_node_helper(self, p, check_flag, diff_flag):
        """
        blacken p.b, incrementing counts and stripping unnecessary blank lines.
        
        Return True if p.b was actually changed.
        """
        trace = 'black' in g.app.debug and not g.unitTesting
        if not should_beautify(p):
            return False
        c = self.c
        self.total += 1
        language = g.findLanguageDirectives(c, p)
        if language != 'python':
            g.trace(f"skipping node: {p.h}")
            return False
        body = p.b.rstrip() + '\n'
        comment_string, body2 = self.sanitizer.comment_leo_lines(p=p)
        try:
            # Support black, version 19.3b0.
            mode = black.FileMode()
            mode.line_length = self.line_length
            mode.string_normalization = self.normalize_strings
            # Note: format_str does not check parse trees,
            #       so in effect, it already runs in fast mode.
            body3 = black.format_str(body2, mode=mode)
        except IndentationError:
            g.warning(f"IndentationError: Can't blacken {p.h}")
            g.es_print(f"{p.h} will not be changed")
            g.printObj(body2, tag='Sanitized syntax')
            if g.unitTesting:
                raise
            p.v.setMarked()
            return False
        except(SyntaxError, black.InvalidInput):
            g.warning(f"SyntaxError: Can't blacken {p.h}")
            g.es_print(f"{p.h} will not be changed")
            g.printObj(body2, tag='Sanitized syntax')
            if g.unitTesting:
                raise
            p.v.setMarked()
            return False
        except Exception:
            g.warning(f"Unexpected exception: {p.h}")
            g.es_print(f"{p.h} will not be changed")
            g.printObj(body2, tag='Sanitized syntax')
            g.es_exception()
            if g.unitTesting:
                raise
            p.v.setMarked()
            return False
        if trace:
            g.printObj(body2, tag='Sanitized syntax')
        result = self.sanitizer.uncomment_leo_lines(comment_string, p, body3)
        if check_flag or result == body:
            if not g.unitTesting:
                return False
        if diff_flag:
            print('=====', p.h)
            print(black.diff(body, result, "old", "new")[16:].rstrip()+'\n')
            return False
        # Update p.b and set undo params.
        self.changed += 1
        p.b = result
        c.frame.body.updateEditors()
        p.v.contentModified()
        c.undoer.setUndoTypingParams(p, 'blacken-node', oldText=body, newText=result)
        if not p.v.isDirty():
            p.setDirty()  # Was p.v.setDirty.
        return True
    #@-others
#@+node:ekr.20110917174948.6903: ** class CPrettyPrinter
class CPrettyPrinter:
    #@+others
    #@+node:ekr.20110917174948.6904: *3* cpp.__init__
    def __init__(self, c):
        """Ctor for CPrettyPrinter class."""
        self.c = c
        self.brackets = 0
            # The brackets indentation level.
        self.p = None
            # Set in indent.
        self.parens = 0
            # The parenthesis nesting level.
        self.result = []
            # The list of tokens that form the final result.
        self.tab_width = 4
            # The number of spaces in each unit of leading indentation.
    #@+node:ekr.20191104195610.1: *3* cpp.pretty_print_tree (new)
    def pretty_print_tree(self, p):
        
        c = self.c
        if should_kill_beautify(p):
            return
        u, undoType = c.undoer, 'beautify-c'
        u.beforeChangeGroup(c.p, undoType)
        dirtyVnodeList = []
        changed = False
        for p in c.p.self_and_subtree():
            if g.scanForAtLanguage(c, p) == "c":
                bunch = u.beforeChangeNodeContents(p)
                s = self.indent(p)
                if p.b != s:
                    p.b = s
                    dirtyVnodeList2 = p.setDirty()
                    dirtyVnodeList.extend(dirtyVnodeList2)
                    u.afterChangeNodeContents(p, undoType, bunch)
                    changed = True
        if changed:
            u.afterChangeGroup(
                c.p, undoType, reportFlag=False, dirtyVnodeList=dirtyVnodeList
            )
        c.bodyWantsFocus()
    #@+node:ekr.20110917174948.6911: *3* cpp.indent & helpers
    def indent(self, p, toList=False, giveWarnings=True):
        """Beautify a node with @language C in effect."""
        if not should_beautify(p):
            return None
        if not p.b:
            return None
        self.p = p.copy()
        aList = self.tokenize(p.b)
        assert ''.join(aList) == p.b
        aList = self.add_statement_braces(aList, giveWarnings=giveWarnings)
        self.bracketLevel = 0
        self.parens = 0
        self.result = []
        for s in aList:
            self.put_token(s)
        if toList:
            return self.result
        return ''.join(self.result)
    #@+node:ekr.20110918225821.6815: *4* add_statement_braces
    def add_statement_braces(self, s, giveWarnings=False):
        p = self.p

        def oops(message, i, j):
            # This can be called from c-to-python, in which case warnings should be suppressed.
            if giveWarnings:
                g.error('** changed ', p.h)
                g.es_print(f'{message} after\n{repr("".join(s[i:j]))}')

        i, n, result = 0, len(s), []
        while i < n:
            token = s[i]
            progress = i
            if token in ('if', 'for', 'while'):
                j = self.skip_ws_and_comments(s, i+1)
                if self.match(s, j, '('):
                    j = self.skip_parens(s, j)
                    if self.match(s, j, ')'):
                        old_j = j + 1
                        j = self.skip_ws_and_comments(s, j+1)
                        if self.match(s, j, ';'):
                            # Example: while (*++prefix);
                            result.extend(s[i : j])
                        elif self.match(s, j, '{'):
                            result.extend(s[i : j])
                        else:
                            oops("insert '{'", i, j)
                            # Back up, and don't go past a newline or comment.
                            j = self.skip_ws(s, old_j)
                            result.extend(s[i : j])
                            result.append(' ')
                            result.append('{')
                            result.append('\n')
                            i = j
                            j = self.skip_statement(s, i)
                            result.extend(s[i : j])
                            result.append('\n')
                            result.append('}')
                            oops("insert '}'", i, j)
                    else:
                        oops("missing ')'", i, j)
                        result.extend(s[i : j])
                else:
                    oops("missing '('", i, j)
                    result.extend(s[i : j])
                i = j
            else:
                result.append(token)
                i += 1
            assert progress < i
        return result
    #@+node:ekr.20110919184022.6903: *5* skip_ws
    def skip_ws(self, s, i):
        while i < len(s):
            token = s[i]
            if token.startswith(' ') or token.startswith('\t'):
                i += 1
            else:
                break
        return i
    #@+node:ekr.20110918225821.6820: *5* skip_ws_and_comments
    def skip_ws_and_comments(self, s, i):
        while i < len(s):
            token = s[i]
            if token.isspace():
                i += 1
            elif token.startswith('//') or token.startswith('/*'):
                i += 1
            else:
                break
        return i
    #@+node:ekr.20110918225821.6817: *5* skip_parens
    def skip_parens(self, s, i):
        """Skips from the opening ( to the matching ).

        If no matching is found i is set to len(s)"""
        assert self.match(s, i, '(')
        level = 0
        while i < len(s):
            ch = s[i]
            if ch == '(':
                level += 1
                i += 1
            elif ch == ')':
                level -= 1
                if level <= 0:
                    return i
                i += 1
            else:
                i += 1
        return i
    #@+node:ekr.20110918225821.6818: *5* skip_statement
    def skip_statement(self, s, i):
        """Skip to the next ';' or '}' token."""
        while i < len(s):
            if s[i] in ';}':
                i += 1
                break
            else:
                i += 1
        return i
    #@+node:ekr.20110917204542.6967: *4* put_token & helpers
    def put_token(self, s):
        """Append token s to self.result as is,
        *except* for adjusting leading whitespace and comments.

        '{' tokens bump self.brackets or self.ignored_brackets.
        self.brackets determines leading whitespace.
        """
        if s == '{':
            self.brackets += 1
        elif s == '}':
            self.brackets -= 1
            self.remove_indent()
        elif s == '(':
            self.parens += 1
        elif s == ')':
            self.parens -= 1
        elif s.startswith('\n'):
            if self.parens <= 0:
                s = f'\n{" "*self.brackets*self.tab_width}'
            else:
                pass  # Use the existing indentation.
        elif s.isspace():
            if self.parens <= 0 and self.result and self.result[-1].startswith('\n'):
                # Kill the whitespace.
                s = ''
            else:
                pass  # Keep the whitespace.
        elif s.startswith('/*'):
            s = self.reformat_block_comment(s)
        else:
            pass  # put s as it is.
        if s:
            self.result.append(s)
    #@+node:ekr.20110917204542.6968: *5* prev_token
    def prev_token(self, s):
        """Return the previous token, ignoring whitespace and comments."""
        i = len(self.result) - 1
        while i >= 0:
            s2 = self.result[i]
            if s == s2:
                return True
            if s.isspace() or s.startswith('//') or s.startswith('/*'):
                i -= 1
            else:
                return False
    #@+node:ekr.20110918184425.6916: *5* reformat_block_comment
    def reformat_block_comment(self, s):
        return s
    #@+node:ekr.20110917204542.6969: *5* remove_indent
    def remove_indent(self):
        """Remove one tab-width of blanks from the previous token."""
        w = abs(self.tab_width)
        if self.result:
            s = self.result[-1]
            if s.isspace():
                self.result.pop()
                s = s.replace('\t', ' '*w)
                if s.startswith('\n'):
                    s2 = s[1:]
                    self.result.append('\n'+s2[:-w])
                else:
                    self.result.append(s[:-w])
    #@+node:ekr.20110918225821.6819: *3* cpp.match
    def match(self, s, i, pat):
        return i < len(s) and s[i] == pat
    #@+node:ekr.20110917174948.6930: *3* cpp.tokenize & helper
    def tokenize(self, s):
        """Tokenize comments, strings, identifiers, whitespace and operators."""
        i, result = 0, []
        while i < len(s):
            # Loop invariant: at end: j > i and s[i:j] is the new token.
            j = i
            ch = s[i]
            if ch in '@\n':  # Make *sure* these are separate tokens.
                j += 1
            elif ch == '#':  # Preprocessor directive.
                j = g.skip_to_end_of_line(s, i)
            elif ch in ' \t':
                j = g.skip_ws(s, i)
            elif ch.isalpha() or ch == '_':
                j = g.skip_c_id(s, i)
            elif g.match(s, i, '//'):
                j = g.skip_line(s, i)
            elif g.match(s, i, '/*'):
                j = self.skip_block_comment(s, i)
            elif ch in "'\"":
                j = g.skip_string(s, i)
            else:
                j += 1
            assert j > i
            result.append(''.join(s[i : j]))
            i = j  # Advance.
        return result


    #@+at The following could be added to the 'else' clause::
    #     # Accumulate everything else.
    #     while (
    #         j < n and
    #         not s[j].isspace() and
    #         not s[j].isalpha() and
    #         not s[j] in '"\'_@' and
    #             # start of strings, identifiers, and single-character tokens.
    #         not g.match(s,j,'//') and
    #         not g.match(s,j,'/*') and
    #         not g.match(s,j,'-->')
    #     ):
    #         j += 1
    #@+node:ekr.20110917193725.6974: *4* cpp.skip_block_comment
    def skip_block_comment(self, s, i):
        assert g.match(s, i, "/*")
        j = s.find("*/", i)
        if j == -1:
            return len(s)
        return j + 2
    #@-others
#@+node:ekr.20191024035716.1: ** class FStringifyTokens(NullTokenBeautifier)
class FstringifyTokens(NullTokenBeautifier):
    """A token-based tool that converts strings containing % to f-strings."""

    undo_type = "Fstringify"

    def __init__(self, c):
        super().__init__(c)
        self.ws = ''
        self.sanitizer = SyntaxSanitizer(c, keep_comments=True)

    #@+others
    #@+node:ekr.20191107014726.1: *3* fstring.error
    def error(self, message):

        g.es_print('')
        g.es_print(f"line {self.line_number}: {message}:")
        g.es_print(self.line.strip())
    #@+node:ekr.20191024051733.11: *3* fstring: Conversion
    #@+node:ekr.20191106065904.1: *4* fstring.compute_result
    def compute_result(self, string_val, results):
        """
        Create the final result as follows:
            
        1. Flatten the results array.
        
        2. Using string_val (the original string) compute whether to use single
           or double quotes for the outer fstring.
        
        3. Beautify the result using the PythonTokenBeautifier class.
        
        Return the result string, or None if there are errors.
        """
        trace = False and not g.unitTesting
        # pylint: disable=import-self
        import leo.core.leoBeautify as leoBeautify
        c = self.c
        #
        # Flatten the token list.
        if trace: g.printObj(results, tag='TOKENS 1')
        tokens = []
        for z in results:
            if isinstance(z, (list, tuple)):
                tokens.extend(z)
            else:
                tokens.append(z)
        if trace: g.printObj(tokens, tag='TOKENS: before ptb')
        #
        # Fail if the result would include a backslash of any kind.
        if any(['\\' in z.value for z in tokens]):
            if not g.unitTesting:
                self.error('string contains backslashes')
                ###
                    # g.es_print('Can not fstringify expressions containing backslashes')
                    # g.es_print(''.join([z.to_string() for z in tokens]))
                    # g.es_print(f"{self.line_number:2}: {self.line.strip()}")
            return None
        #
        # Ensure consistent quotes.
        ok = self.change_quotes(string_val, tokens)
        if not ok:
            if not g.unitTesting:
                self.error('string contains backslashes')
                ###
                    # g.es_print('Can not fstringify expression containing mixed quotes')
                    # g.es_print(''.join([z.to_string() for z in tokens]))
            return None
        #
        # Use ptb to clean up inter-token whitespace.
        x = leoBeautify.PythonTokenBeautifier(c)
        x.dump_input_tokens = True
        x.dump_output_tokens = True
        ### We can do this only if the previous token was a name.
        ### tokens.append(self.new_token('blank', ' '))
        result_tokens = x.scan_all_beautifier_tokens(tokens)
        #
        # Create the result.
        if trace: g.printObj(result_tokens, tag='TOKENS: after ptb')
        result = ''.join([z.to_string() for z in result_tokens])
        # Ensure a space between the new fstring and a previous name.
        if self.prev_token.kind == 'name':
            result = ' ' + result
        return result
    #@+node:ekr.20191024102832.1: *4* fstring.convert_fstring
    def convert_fstring(self):
        """
        Scan a string, converting it to an f-string.
        The 'string' token has already been consumed.
        """
        new_token = self.new_token
        string_val = self.val
        specs = self.scan_format_string(string_val)
        values, tokens = self.scan_for_values()
        if len(specs) != len(values):
            self.error('Scanning error')
            g.trace('\nMISMATCH\n')
            g.trace('specs:', len(specs), 'values', len(values))
            g.printObj(specs, tag='SPECS')
            g.printObj(values, tag='VALUES')
            # Punt, without popping any more tokens.
            self.add_token('string', string_val)
            return
        # Substitute the values.
        i, results = 0, [new_token('fstringify', 'f')]
        for spec_i, m in enumerate(specs):
            value = values[spec_i]
            start, end, spec = m.start(0), m.end(0), m.group(1)
            if start > i:
                results.append(new_token('fstringify', string_val[i : start]))
            head, tail = self.munge_spec(spec)
            results.append(new_token('op', '{'))
            results.append(new_token('fstringify', value))
            if head:
                results.append(new_token('fstringify', '!'))
                results.append(new_token('fstringify', head))
            if tail:
                results.append(new_token('fstringify', ':'))
                results.append(new_token('fstringify', tail))
            results.append(new_token('op', '}'))
            i = end
        # Add the tail.
        tail = string_val[i:]
        if tail:
            results.append(new_token('fstringify', tail))
        result = self.compute_result(string_val, results)
        if result:
            # Actually consume the scanned tokens.
            for token in tokens:
                self.tokens.pop(0)
            self.add_token('string', result)
        else:
            # Punt, without popping any more tokens.
            self.add_token('string', string_val)
    #@+node:ekr.20191025043607.1: *4* fstring.munge_spec
    def munge_spec(self, spec):
        """
        Return (head, tail).
        
        The format is spec !head:tail or :tail
        
        Example specs: s2, r3
        """
        ### To do: handle more specs.
        head, tail = [], []
        if spec.startswith('+'):
            spec = spec[1:]
        elif spec.startswith('-'):
            tail.append('>')
            spec = spec[1:]
        if spec.endswith('s'):
            spec = spec[:-1]
        if spec.endswith('r'):
            head.append('r')
            spec = spec[:-1]
        tail = ''.join(tail) + spec
        head = ''.join(head)
        return head, tail
    #@+node:ekr.20191025034715.1: *4* fstring.change_quotes
    def change_quotes(self, string_val, aList):
        """
        Carefully change quotes in all "inner" tokens as necessary.
        
        Return True if all went well.
        
        We expect the following "outer" tokens.
            
        aList[0]:  ('fstringify', 'f')
        aList[1]:  ('fstringify', a string starting with a quote)
        aList[-1]: ('fstringify', a string ending with a quote that matches aList[1])
        """
        # Sanity checks.
        if len(aList) < 4:
            return True
        if not string_val:
            g.es_print('no string_val!')
            return False
        delim = string_val[0]
        delim2 = '"' if delim == "'" else '"'
        #
        # Check tokens 0, 1 and -1.
        token0 = aList[0]
        token1 = aList[1]
        token_last = aList[-1]
        for token in token0, token1, token_last:
            if token.kind != 'fstringify':
                g.es_print(f"unexpected token: {token!r}")
                return False
        if token0.value != 'f':
            g.es_print('token[0] error!', repr(token0))
            return False
        val1 = token1.value and token1.value[0]
        if delim != val1:
            g.es_print('token[1] error!', delim, val1, repr(token1))
            return False
        val_last = token_last.value and token_last.value[-1]
        if delim != val_last:
            g.es_print('token[-1] error!', delim, val_last, repr(token_last))
            return False
        #
        # Replace delim by delim2 in all inner tokens.
        for z in aList[2:-1]:
            if not isinstance(z, BeautifierToken):
                g.es_print('Bad token:', repr(z))
                return False
            z.value = z.value.replace(delim, delim2)
        return True
    #@+node:ekr.20191024132557.1: *4* fstring.scan_for_values
    def scan_for_values(self):
        """
        Return a list of possibly parenthesized values for the format string.
        
        This method never actually consumes tokens.
        
        If all goes well, we'll skip all tokens in the tokens list.
        """
        # Skip the '%'
        new_token = self.new_token
        assert self.look_ahead(0) == ('op', '%')
        token_i, tokens = self.skip_ahead(0, 'op', '%')
        # Skip '(' if it's next
        include_paren = self.look_ahead(token_i) == ('op', '(')
        if include_paren:
            token_i, skipped_tokens = self.skip_ahead(token_i, 'op', '(')
            tokens.extend(skipped_tokens)
        # Find all tokens up to the first ')' or 'for'
        values, value_list = [], []
        while token_i < len(self.tokens):
            # Don't use look_ahead here: handle each token exactly once.
            token = self.tokens[token_i]
            token_i += 1
            tokens.append(token)
            kind, val = token.kind, token.value
            if kind == 'ws':
                continue
            if kind in ('newline', 'nl'):
                if include_paren or val.endswith('\\\n'):
                    # Continue scanning, ignoring the newline.
                    continue
                else:
                    # The newline ends the scan.
                    values.append(value_list)
                        # Retain the tokens!
                    if not include_paren: # Bug fix.
                        tokens.pop()  # Rescan the ')'
                    break
            if (kind, val) == ('op', ')'):
                values.append(value_list)
                if not include_paren:
                    tokens.pop()  # Rescan the ')'
                break
            if (kind, val) == ('name', 'for'):
                tokens.pop()  # Rescan the 'for'
                values.append(value_list)
                break
            if (kind, val) == ('op', ','):
                values.append(value_list)
                value_list = []
            elif kind == 'op' and val in '([{':
                values_list2, token_i2 = self.scan_to_matching(token_i-1, val)
                value_list.extend(values_list2)
                tokens.extend(self.tokens[token_i : token_i2])
                token_i = token_i2
            elif kind == 'name':
                # Ensure separation of names.
                value_list.append(new_token(kind, val))
                value_list.append(new_token('ws', ' '))
            else:
                value_list.append(new_token(kind, val))
        return values, tokens
    #@+node:ekr.20191024110603.1: *4* fstring.scan_format_string
    # format_spec ::=  [[fill]align][sign][#][0][width][,][.precision][type]
    # fill        ::=  <any character>
    # align       ::=  "<" | ">" | "=" | "^"
    # sign        ::=  "+" | "-" | " "
    # width       ::=  integer
    # precision   ::=  integer
    # type        ::=  "b" | "c" | "d" | "e" | "E" | "f" | "F" | "g" | "G" | "n" | "o" | "s" | "x" | "X" | "%"

    format_pat = re.compile(r'%(([+-]?[0-9]*(\.)?[0.9]*)*[bcdeEfFgGnoxrsX]?)')

    def scan_format_string(self, s):
        """Scan the format string s, returning a list match objects."""
        result = list(re.finditer(self.format_pat, s))
        return result
    #@+node:ekr.20191025022207.1: *4* fstring.scan_to_matching
    def scan_to_matching(self, token_i, val):
        """
        self.tokens[token_i] represents an open (, [ or {.
        
        Return (values_list, token_i) of all tokens to the matching closing delim.
        """
        trace = False and not g.unitTesting
        new_token = self.new_token
        if trace:
            g.trace('=====', token_i, repr(val))
            g.trace(''.join([z.value for z in self.tokens[token_i:]]))
        values_list = []
        kind0, val0 = self.look_ahead(token_i)
        assert kind0 == 'op' and val0 == val and val in '([{', (kind0, val0)
        levels = [0, 0, 0]
        level_index = '([{'.index(val)
        levels[level_index] += 1
        # Move past the opening delim.
        values_list.append(new_token('op', val0))
        token_i += 1
        while token_i < len(self.tokens):
            # Don't use look_ahead here: handle each token exactly once.
            progress = token_i
            token = self.tokens[token_i]
            token_i += 1
            kind, val = token.kind, token.value
            if kind == 'ws':
                continue
            if kind in ('nl', 'newline'):
                continue
            if kind == 'op' and val in ')]}':
                values_list.append(new_token('op', val))
                level_index = ')]}'.index(val)
                levels[level_index] -= 1
                if levels == [0, 0, 0]:
                    if trace:
                        g.printObj(values_list, tag=f"scan_to_matching {val!r}")
                    return values_list, token_i
            elif kind == 'op' and val in '([{':
                # Recurse.
                values_list2, token_i = self.scan_to_matching(token_i-1, val)
                values_list.extend(values_list2)
            elif kind == 'name':
                # Ensure separation of names.
                values_list.append(new_token('name', val))
                values_list.append(new_token('ws', '  '))
            else:
                values_list.append(new_token(kind, val))
            assert token_i > progress, (kind, val)
        # Should never happen.
        g.trace(f"\nFAIL {token_i} {''.join(values_list)}\n")
        return [], token_i
    #@+node:ekr.20191025084714.1: *3* fstring: Entries
    #@+node:ekr.20191024044254.1: *4* fstring.fstringify_file
    def fstringify_file(self):
        """
        Find the nearest @<file> node and convert % to fstrings within it.
        
        There is no need to sanitize code when converting an external file.
        """
        trace = True and not g.unitTesting
        verbose = False
        filename = self.find_root()
        if not filename:
            return
        # Open the file.
        with open(filename, 'r') as f:
            contents = f.read()
        if trace:
            g.trace(f"Contents...\n\n{contents}")
        # Generate tokens.
        tokens = self.tokenize_string(contents, filename)
        # Handle all tokens, creating the raw result.
        result = self.scan_all_tokens(contents, tokens)
        # Trace the results.
        changed = contents.rstrip() != result.rstrip()
        if trace and verbose:
            g.printObj(f"Code List...\n\n{self.code_list}")
        if trace:
            g.trace(f"Result...\n\n{result}")
        if not changed:
            return
        # Write the file.
        with open(filename, 'w') as f:
            f.write(result)
    #@+node:ekr.20191024081033.1: *4* fstring.fstringify_node
    def fstringify_node(self, p):
        """
        fstringify node p.  Return True if the node has been changed.
        """
        trace = False and not g.unitTesting
        verbose = False
        c = self.c
        if should_kill_beautify(p):
            return False
        contents = p.b
        if not contents.strip():
            return False
        # Unlike with external files, we must sanitize the text!
        comment_string, contents2 = self.sanitizer.comment_leo_lines(p=p)
        # Generate tokens.
        tokens = self.tokenize_string(contents2, p.h)
        # Handle all tokens, creating the raw result.
        raw_result = self.scan_all_tokens(contents2, tokens)
        # Undo the munging of the sources.
        result = self.sanitizer.uncomment_leo_lines(comment_string, c.p, raw_result)
        changed = contents.rstrip() != result.rstrip()
        if changed:
            p.b = result
            p.setDirty()
        # Trace the results.
        if trace and changed and verbose:
            g.trace(f"Contents...\n\n{contents}\n")
            g.trace(f"code list...\n\n{g.objToString(self.code_list)}\n")
            g.trace(f"raw result...\n\n{raw_result}\n")
            g.trace(f"Result...\n\n{result}\n")
        if trace:
            g.trace('Changed!' if changed else 'No change:', p.h)
        return changed
    #@+node:ekr.20191025084750.1: *4* fstring.fstringify_tree
    def fstringify_tree(self, p):
        """fstringify node p."""
        c = self.c
        if should_kill_beautify(p):
            return
        t1 = time.process_time()
        changed = total = 0
        for p in p.self_and_subtree():
            if g.scanForAtLanguage(c, p) == "python":
                total += 1
                if self.fstringify_node(p):
                    changed += 1
        self.end_undo()
        if g.unitTesting:
            return
        t2 = time.process_time()
        g.es_print(
            f"scanned {total} node{g.plural(total)}, "
            f"changed {changed} node{g.plural(changed)}, "
            # f"{errors} error{g.plural(errors)} "
            f"in {t2-t1:4.2f} sec."
        )
    #@+node:ekr.20191106065637.1: *3* fstring: Tokens
    #@+node:ekr.20191106095910.1: *4* fstring.new_token
    def new_token(self, kind, value):
        """Return a new token"""

        def item_kind(z):
            return 'string' if isinstance(z, str) else z.kind

        def val(z):
            return z if isinstance(z, str) else z.value
            
        if isinstance(value, (list, tuple)):
            return [BeautifierToken(item_kind(z), val(z)) for z in value]    
        return BeautifierToken(kind, value)
    #@+node:ekr.20191028091917.1: *4* fstring.blank
    def blank(self):
        """Add a blank request to the code list."""
        # Same as ptb.blank, but there is no common base class.
        prev = self.code_list[-1]
        if prev.kind not in (
            'blank',
            'blank-lines',
            'file-start',
            'line-end',
            'line-indent',
            'lt',
            'op-no-blanks',
            'unary-op',
        ):
            self.add_token('blank', ' ')
    #@+node:ekr.20191106065455.1: *4* fstring.do_string
    def do_string(self):
        """Handle a 'string' token."""
        # See whether a conversion is possible.
        if (
            not self.val.lower().startswith(('f', 'r'))
            and '%' in self.val
            and self.look_ahead(0) == ('op', '%')
        ):
            # Not an f or r string, and a conversion is possible.
            self.convert_fstring()
        else:
            # Just put the string
            self.add_token('string', self.val) 
    #@+node:ekr.20191028085402.1: *4* fstring.do_token (override)
    def do_token(self, token):
        """
        Override NullTokenBeautifier.do_token.

        Handle one input token, a BeautifierToken.
        """
        # Only the string handler is overridden.
        if token.kind == 'string':
            self.kind = token.kind
            self.val = token.value
            # Set these for error messages.
            self.line = token.line
            self.line_number = token.line_number
            self.do_string()
        else:
            # Same as super().do_token(token)
            self.code_list.append(token)
        self.prev_token = token
    #@+node:ekr.20191029014023.6: *4* fstring.look_ahead & skip_ahead
    def look_ahead(self, n):
        """
        Look ahead n tokens, skipping ws tokens  n >= 0.
        Return (token.kind, token.value)
        """
        while n < len(self.tokens):
            token = self.tokens[n]
            n += 1
            assert isinstance(token, BeautifierToken), (repr(token), g.callers())
            if token.kind != 'ws':
                return token.kind, token.value
        return None, None
            # Strip trailing whitespace from the token value.

    def skip_ahead(self, n, target_kind, target_val):
        """
        Skip to the target token.  Only ws tokens should intervene.

        Return (n, tokens):
        """
        tokens = []
        while n < len(self.tokens):
            token = self.tokens[n]
            tokens.append(token)
            n += 1
            if (token.kind, token.value) == (target_kind, target_val):
                return n, tokens
            assert token.kind == 'ws', (token.kind, token.value)
        # Should never happen.
        return n, []
    #@+node:ekr.20191106105311.1: *4* null_tok_b.scan_all_beautifier_tokens


    #@-others
#@+node:ekr.20150527113020.1: ** class ParseState
class ParseState:
    """
    A class representing items in the parse state stack.
    
    The present states:
        
    'file-start': Ensures the stack stack is never empty.
        
    'decorator': The last '@' was a decorator.
        
        do_op():    push_state('decorator')
        do_name():  pops the stack if state.kind == 'decorator'.
                    
    'indent': The indentation level for 'class' and 'def' names.
    
        do_name():      push_state('indent', self.level)
        do_dendent():   pops the stack once or twice if state.value == self.level.

    """

    def __init__(self, kind, value):
        self.kind = kind
        self.value = value

    def __repr__(self):
        return f"State: {self.kind} {self.value!r}"

    __str__ = __repr__
#@+node:ekr.20150519111457.1: ** class PythonTokenBeautifier(NullTokenBeautifier)
class PythonTokenBeautifier(NullTokenBeautifier):
    """A token-based Python beautifier."""

    undo_type = "Pretty Print"

    #@+others
    #@+node:ekr.20150519111713.1: *3* ptb.ctor
    #@@nobeautify

    def __init__(self, c):
        """Ctor for PythonPrettyPrinter class."""
        super().__init__(c)
        #
        # Globals...
        self.orange = False
            # Split or join lines only if orange is True.
        self.val = None
            # The string containing the input token's value.
        #
        # State vars...
        self.decorator_seen = False
            # Set by do_name as a flag to do_op.
        self.in_arg_list = 0
            # > 0 if in an argument list of a function definition.
        self.level = 0
            # indentation level. Set only by do_indent and do_dedent.
            # do_name calls: push_state('indent', self.level)
        self.lws = ''
            # Leading whitespace.
            # Typically ' '*self.tab_width*self.level,
            # but may be changed for continued lines.
        self.state_stack = []
            # Stack of ParseState objects.
        #
        # Counts of unmatched brackets and parentheses.
        self.paren_level = 0
            # Number of unmatched '(' tokens.
        self.square_brackets_level = 0
            # Number of unmatched '[' tokens.
        self.curly_brackets_level = 0
            # Number of unmatched '{' tokens.
        #
        # Undo vars...
        self.changed = False
        self.dirtyVnodeList = []
        #
        # Complete the init.
        self.sanitizer = None  # For pylint.
        self.reloadSettings()
    #@+node:ekr.20191028091748.1: *3* ptb.reload_settings
    def reloadSettings(self):
        c = self.c
        if c:
            # These should be on the same line,
            # so the check-settings script in leoSettings.leo will see them.
            keep_comments = c.config.getBool('beautify-keep-comment-indentation', default=True)
            self.delete_blank_lines = not c.config.getBool('beautify-keep-blank-lines', default=True)
            # Join.
            n = c.config.getInt('beautify-max-join-line-length')
            self.max_join_line_length = 88 if n is None else n
            # Split
            n = c.config.getInt('beautify-max-split-line-length')
            self.max_split_line_length = 88 if n is None else n
            # Join <= Split.
            if self.max_join_line_length > self.max_split_line_length:
                self.max_join_line_length = self.max_split_line_length
            self.tab_width = abs(c.tab_width)
        else:
            keep_comments = True
            self.delete_blank_lines = True
            self.max_join_line_length = 88
            self.max_split_line_length = 88
            self.tab_width = 4
        self.sanitizer = SyntaxSanitizer(c, keep_comments)
    #@+node:ekr.20191030035440.1: *3* ptb: Overrides
    # These override methods of the NullTokenBeautifier class.
    #@+node:ekr.20191024071243.1: *4* ptb.do_token (override)
    def oops(self):
        g.trace('unknown kind', self.kind)

    def do_token(self, token):
        """
        Handle one token.
        
        Token handlers may call this method to do look-ahead processing.
        """
        assert isinstance(token, BeautifierToken), (repr(token), g.callers())
        # Remembering token.line is necessary, because dedent tokens
        # can happen *after* comment lines that should be dedented!
        self.kind, self.val, self.line = token.kind, token.value, token.line
        func = getattr(self, f"do_{token.kind}", self.oops)
        func()
    #@+node:ekr.20191027172407.1: *4* ptb.file_end (override)
    def file_end(self):
        """
        Add a file-end token to the code list.
        Retain exactly one line-end token.
        """
        self.clean_blank_lines()
        self.add_token('line-end', '\n')
        self.add_token('line-end', '\n')
        self.add_token('file-end')
    #@+node:ekr.20191030035233.1: *4* ptb.file_start (override)
    def file_start(self):
        """
        Do any start-of-file processing.
        
        May be overridden in subclasses.
        
        The file-start *token* has already been added to self.code_list.
        """
        self.push_state('file-start')
    #@+node:ekr.20150530072449.1: *3* ptb: Entries
    #@+node:ekr.20191104194524.1: *4* ptb.beautify_tree (new)
    def beautify_tree(self, p):

        c = self.c
        if should_kill_beautify(p):
            return
        t1 = time.process_time()
        self.errors = 0
        changed = errors = total = 0
        for p in p.self_and_subtree():
            if g.scanForAtLanguage(c, p) == "python":
                total += 1
                if self.prettyPrintNode(p):
                    changed += 1
                errors += self.errors
                self.errors = 0
        self.end_undo()
        if g.unitTesting:
            return
        t2 = time.process_time()
        g.es_print(
            f"scanned {total} node{g.plural(total)}, "
            f"changed {changed} node{g.plural(changed)}, "
            f"{errors} error{g.plural(errors)} "
            f"in {t2-t1:4.2f} sec."
        )
    #@+node:ekr.20191104194924.1: *4* ptb.beautify_node (new)
    def beautify_node(self, p):

        t1 = time.process_time()
        c = self.c
        self.errors = 0
        changed = 0
        if g.scanForAtLanguage(c, c.p) != "python":
            g.es_print(f"{p.h} does not contain python code")
            return
        if self.prettyPrintNode(c.p):
            changed += 1
            self.end_undo()
        if g.unitTesting:
            return
        t2 = time.process_time()
        g.es_print(
            f"changed {changed} node{g.plural(changed)}, "
            f"{self.errors} error{g.plural(self.errors)} "
            f"in {t2-t1:4.2f} sec."
        )
    #@+node:ekr.20150528171137.1: *4* ptb.prettyPrintNode (sets stats)
    def prettyPrintNode(self, p):
        """
        The driver for beautification: beautify a single node.
        Return True if the node was actually changed.
        """
        if not should_beautify(p):
            # @nobeautify is in effect.
            return False
        if not p.b:
            # Pretty printing might add text!
            return False
        if not p.b.strip():
            # Do this *after* we are sure @beautify is in effect.
            self.replace_body(p, '')
            return False
        t1 = time.process_time()
        # Replace Leonine syntax with special comments.
        comment_string, s0 = self.sanitizer.comment_leo_lines(p=p)
        check_result = True
        node1 = leoAst.parse_ast(s0, headline=p.h)
        if not node1:
            self.errors += 1
            if g.unitTesting:
                tag = f"parse_ast FAIL 1: {repr(p and p.h)}"
                if self.dump_on_error:
                    g.printObj(s0, tag=tag)
                else:
                    print(s0)
                raise AssertionError(tag)
            p.v.setMarked()
            g.es_print(f"{p.h} will not be changed")
            return False
        t2 = time.process_time()
        # Generate the tokens.
        readlines = g.ReadLinesClass(s0).next
        tokens = list(tokenize.generate_tokens(readlines))
        # Beautify into s2.
        t3 = time.process_time()
        s2 = self.scan_all_tokens(s0, tokens)
        assert isinstance(s2, str), s2.__class__.__name__
        t4 = time.process_time()
        if check_result:
            node2 = leoAst.parse_ast(s2, headline='result')
            if not node2:
                self.errors += 1
                if g.unitTesting:
                    tag = f"parse_ast FAIL 2: {repr(p and p.h)}"
                    if self.dump_on_error:
                        g.printObj(s2, tag=tag)
                    else:
                        print(tag, '\n')
                        print(s2)
                    raise AssertionError(tag)
                p.v.setMarked()
                g.es_print(f"{p.h} will not be changed")
                return False
            # Compare the two parse trees.
            ok = leoAst.compare_asts(node1, node2)
            if not ok:
                g.warning(f"{p.h}: The beautify command did not preserve meaning!")
                if self.dump_on_error:
                    g.printObj(s2, tag='RESULT')
                else:
                    print(s2)
                self.errors += 1
                p.v.setMarked()
                return False
        if 'beauty' in g.app.debug:
            g.printObj(self.code_list, tag="Code List")
        t5 = time.process_time()
        # Restore the tags after the compare
        s3 = self.sanitizer.uncomment_leo_lines(comment_string, p, s2)
        changed = p.b.strip() != s3.strip()
            # Important: ignore leading/trailing whitespace.
        if changed:
            if 0:
                g.trace('*** changed', p.h)
                import difflib  #, pprint
                g.printObj(list(difflib.ndiff(g.splitLines(p.b), g.splitLines(s3))))
            self.replace_body(p, s3)
            p.setDirty()
        # Update the stats
        self.n_input_tokens += len(tokens)
        self.n_output_tokens += len(self.code_list)
        self.n_strings += len(s3)
        self.parse_time += t2 - t1
        self.tokenize_time += t3 - t2
        self.beautify_time += t4 - t3
        self.check_time += t5 - t4
        self.total_time += t5 - t1
        # self.print_stats()
        return changed
    #@+node:ekr.20191106105540.1: *4* ptb.scan_all_beautifier_tokens
    def scan_all_beautifier_tokens(self, tokens):
        """
        A helper for the fstringify class, similar to null_b.scan_all_tokens.
        
        Differences:
            
        1. tokens is a list of BeautifierTokens, not a list of 5-tuples.
        2. This method adds no end-of-file tokens.
        3. This method returns a list of BeautifierTokens, not a string.
        """
        self.tokens = tokens
        self.code_list = []
        self.add_token('file-start')
        self.push_state('file-start')
        while self.tokens:
            token = self.tokens.pop(0)
            self.do_token(token)
        return self.code_list
    #@+node:ekr.20150526194736.1: *3* ptb: Input token Handlers
    #@+node:ekr.20150526203605.1: *4* ptb.do_comment
    def do_comment(self):
        """Handle a comment token."""
        self.clean('blank')
        entire_line = self.line.lstrip().startswith('#')
        if entire_line:
            self.clean('line-indent')
            val = self.line.rstrip()
        else:
            # Exactly two spaces before trailing comments.
            val = '  ' + self.val.rstrip()
        self.add_token('comment', val)
    #@+node:ekr.20191105094430.1: *4* pdb.do_encoding
    def do_encoding(self):
        """
        Handle the encoding token.
        """
        pass
    #@+node:ekr.20041021102938: *4* ptb.do_endmarker
    def do_endmarker(self):
        """Handle an endmarker token."""
        pass
    #@+node:ekr.20041021102340.1: *4* ptb.do_errortoken
    def do_errortoken(self):
        """Handle an errortoken token."""
        # This code is executed for versions of Python earlier than 2.4
        if self.val == '@':
            self.op(self.val)
    #@+node:ekr.20041021102340.2: *4* ptb.do_indent & do_dedent
    def do_dedent(self):
        """Handle dedent token."""
        self.level -= 1
        self.lws = self.level * self.tab_width * ' '
        self.line_indent()
        state = self.state_stack[-1]
        if state.kind == 'indent' and state.value == self.level:
            self.state_stack.pop()
            state = self.state_stack[-1]
            if state.kind in ('class', 'def'):
                self.state_stack.pop()
                self.blank_lines(1)
                    # Most Leo nodes aren't at the top level of the file.
                    # self.blank_lines(2 if self.level == 0 else 1)

    def do_indent(self):
        """Handle indent token."""
        new_indent = self.val
        old_indent = self.level * self.tab_width * ' '
        if new_indent > old_indent:
            self.level += 1
        elif new_indent < old_indent:
            g.trace('\n===== can not happen', repr(new_indent), repr(old_indent))
        self.lws = new_indent
        self.line_indent()
    #@+node:ekr.20191106121141.1: *4* ptb.do_fstringify
    def do_fstringify(self):
        """
        A helper for the FstringifyTokens class.
        
        This class creates synthetic "fstringify" tokens.
        """
        self.add_token('fstringify', self.val)
    #@+node:ekr.20041021101911.5: *4* ptb.do_name
    def do_name(self):
        """Handle a name token."""
        name = self.val
        if name in ('class', 'def'):
            self.decorator_seen = False
            state = self.state_stack[-1]
            if state.kind == 'decorator':
                self.clean_blank_lines()
                self.line_end()
                self.state_stack.pop()
            else:
                self.blank_lines(1)
                # self.blank_lines(2 if self.level == 0 else 1)
            self.push_state(name)
            self.push_state('indent', self.level)
                # For trailing lines after inner classes/defs.
            self.word(name)
        elif name in ('and', 'in', 'not', 'not in', 'or', 'for'):
            self.word_op(name)
        else:
            self.word(name)
    #@+node:ekr.20041021101911.3: *4* ptb.do_newline & do_nl
    def do_newline(self):
        """Handle a regular newline."""
        # Retain any sidecar ws in the newline.
        self.line_end(self.val)

    def do_nl(self):
        """Handle a continuation line."""
        # Retain any sidecar ws in the newline.
        self.line_end(self.val)
    #@+node:ekr.20041021101911.6: *4* ptb.do_number
    def do_number(self):
        """Handle a number token."""
        assert isinstance(self.val, str), repr(self.val)
        self.add_token('number', self.val)
    #@+node:ekr.20040711135244.11: *4* ptb.do_op
    def do_op(self):
        """Handle an op token."""
        val = self.val
        if val == '.':
            self.op_no_blanks(val)
        elif val == '@':
            if not self.decorator_seen:
                self.blank_lines(1)
                self.decorator_seen = True
            self.op_no_blanks(val)
            self.push_state('decorator')
        elif val == ':':
            # Treat slices differently.
            self.colon(val)
        elif val in ',;':
            # Pep 8: Avoid extraneous whitespace immediately before
            # comma, semicolon, or colon.
            self.op_blank(val)
        elif val in '([{':
            # Pep 8: Avoid extraneous whitespace immediately inside
            # parentheses, brackets or braces.
            self.lt(val)
        elif val in ')]}':
            # Ditto.
            self.rt(val)
        elif val == '=':
            # Pep 8: Don't use spaces around the = sign when used to indicate
            # a keyword argument or a default parameter value.
            if self.paren_level:
                self.op_no_blanks(val)
            else:
                self.op(val)
        elif val in '~+-':
            self.possible_unary_op(val)
        elif val == '*':
            self.star_op()
        elif val == '**':
            self.star_star_op()
        else:
            # Pep 8: always surround binary operators with a single space.
            # '==','+=','-=','*=','**=','/=','//=','%=','!=','<=','>=','<','>',
            # '^','~','*','**','&','|','/','//',
            # Pep 8: If operators with different priorities are used,
            # consider adding whitespace around the operators with the lowest priority(ies).
            self.op(val)
    #@+node:ekr.20150526204248.1: *4* ptb.do_string (sets backslash_seen)
    def do_string(self):
        """Handle a 'string' token."""
        self.add_token('string', self.val)
        self.blank()
    #@+node:ekr.20191105081403.1: *4* ptb.do_ws
    def do_ws(self):
        """
        Handle the "ws" pseudo-token.
        
        Put the whitespace only if if ends with backslash-newline.
        """
        # Short-circuit if there is no ws to add.
        if not self.val:
            return
        #
        # Handle backslash-newline.
        if '\\\n' in self.val:
            # Prepend a *real* blank, so later code won't add any more ws.
            self.clean('blank')
            self.add_token('blank', ' ')
            self.add_token('ws', self.val.lstrip())
            if self.val.endswith((' ', '\t')):
                # Add a *empty* blank, so later code won't add any more ws.
                self.add_token('blank', '')
            return
        #
        # Handle start-of-line whitespace.
        prev = self.code_list[-1]
        inner = self.paren_level or self.square_brackets_level or self.curly_brackets_level
        if prev.kind == 'line-indent' and inner:
            # Retain the indent that won't be cleaned away.
            self.clean('line-indent')
            self.add_token('hard-blank', self.val)
    #@+node:ekr.20150526201902.1: *3* ptb: Output token generators
    #@+node:ekr.20150526201701.4: *4* ptb.blank
    def blank(self):
        """Add a blank request to the code list."""
        prev = self.code_list[-1]
        if prev.kind not in (
            'blank',
            'blank-lines',
            'file-start',
            'hard-blank', # Unique to ptb.
            'line-end',
            'line-indent',
            'lt',
            'op-no-blanks',
            'unary-op',
        ):
            self.add_token('blank', ' ')
    #@+node:ekr.20190915083748.1: *4* ptb.blank_before_end_line_comment
    def blank_before_end_line_comment(self):
        """Add two blanks before an end-of-line comment."""
        prev = self.code_list[-1]
        self.clean('blank')
        if prev.kind not in ('blank-lines', 'file-start', 'line-end', 'line-indent'):
            self.add_token('blank', ' ')
            self.add_token('blank', ' ')
    #@+node:ekr.20150526201701.5: *4* ptb.blank_lines
    def blank_lines(self, n):
        """
        Add a request for n blank lines to the code list.
        Multiple blank-lines request yield at least the maximum of all requests.
        """
        self.clean_blank_lines()
        kind = self.code_list[-1].kind
        if kind == 'file-start':
            self.add_token('blank-lines', n)
            return
        for i in range(0, n+1):
            self.add_token('line-end', '\n')
        # Retain the token (intention) for debugging.
        self.add_token('blank-lines', n)
        self.line_indent()
    #@+node:ekr.20150526201701.6: *4* ptb.clean
    def clean(self, kind):
        """Remove the last item of token list if it has the given kind."""
        prev = self.code_list[-1]
        if prev.kind == kind:
            self.code_list.pop()
    #@+node:ekr.20150527175750.1: *4* ptb.clean_blank_lines
    def clean_blank_lines(self):
        """Remove all vestiges of previous lines."""
        table = ('blank-lines', 'line-end', 'line-indent')
        while self.code_list[-1].kind in table:
            self.code_list.pop()
    #@+node:ekr.20190915120431.1: *4* ptb.colon
    def colon(self, val):
        """Handle a colon."""
        if self.square_brackets_level > 0:
            # Put blanks on either side of the colon,
            # but not between commas, and not next to [.
            self.clean('blank')
            prev = self.code_list[-1]
            if prev.value == '[':
                # Never put a blank after "[:"
                self.add_token('op', val)
            elif prev.value == ':':
                self.add_token('op', val)
                self.blank()
            else:
                self.op(val)
        else:
            self.op_blank(val)
    #@+node:ekr.20150526201701.9: *4* ptb.line_end & split/join helpers
    def line_end(self, ws=''):
        """Add a line-end request to the code list."""
        prev = self.code_list[-1]
        if prev.kind == 'file-start':
            return
        self.clean('blank')  # Important!
        if self.delete_blank_lines:
            self.clean_blank_lines()
        self.clean('line-indent')
        self.add_token('line-end', '\n')
        if self.orange:
            allow_join = True
            if self.max_split_line_length > 0:
                allow_join = not self.break_line()
            if allow_join and self.max_join_line_length > 0:
                self.join_lines()
        self.line_indent()
            # Add the indentation for all lines
            # until the next indent or unindent token.
    #@+node:ekr.20190908054807.1: *5* ptb.break_line (new) & helpers
    def break_line(self):
        """
        Break the preceding line, if necessary.
        
        Return True if the line was broken into two or more lines.
        """
        assert self.code_list[-1].kind == 'line-end', repr(self.code_list[-1])
            # Must be called just after inserting the line-end token.
        #
        # Find the tokens of the previous lines.
        line_tokens = self.find_prev_line()
        # g.printObj(line_tokens, tag='PREV LINE')
        line_s = ''.join([z.to_string() for z in line_tokens])
        if self.max_split_line_length == 0 or len(line_s) < self.max_split_line_length:
            return False
        #
        # Return if the previous line has no opening delim: (, [ or {.
        if not any([z.kind == 'lt' for z in line_tokens]):
            return False
        prefix = self.find_line_prefix(line_tokens)
        #
        # Calculate the tail before cleaning the prefix.
        tail = line_tokens[len(prefix):]
        if prefix[0].kind == 'line-indent':
            prefix = prefix[1:]
        # g.printObj(prefix, tag='PREFIX')
        # g.printObj(tail, tag='TAIL')
        #
        # Cut back the token list
        self.code_list = self.code_list[: len(self.code_list) - len(line_tokens) - 1]
            # -1 for the trailing line-end.
        # g.printObj(self.code_list, tag='CUT CODE LIST')
        #
        # Append the tail, splitting it further, as needed.
        self.append_tail(prefix, tail)
        #
        # Add the line-end token deleted by find_line_prefix.
        self.add_token('line-end', '\n')
        return True
    #@+node:ekr.20190908065154.1: *6* ptb.append_tail
    def append_tail(self, prefix, tail):
        """Append the tail tokens, splitting the line further as necessary."""
        g.trace('='*20)
        tail_s = ''.join([z.to_string() for z in tail])
        if len(tail_s) < self.max_split_line_length:
            # Add the prefix.
            self.code_list.extend(prefix)
            # Start a new line and increase the indentation.
            self.add_token('line-end', '\n')
            self.add_token('line-indent', self.lws+' '*4)
            self.code_list.extend(tail)
            return
        #
        # Still too long.  Split the line at commas.
        self.code_list.extend(prefix)
        # Start a new line and increase the indentation.
        self.add_token('line-end', '\n')
        self.add_token('line-indent', self.lws+' '*4)
        open_delim = BeautifierToken(kind='lt', value=prefix[-1].value)
        close_delim = BeautifierToken(
            kind='rt',
            value=open_delim.value.replace('(', ')').replace('[', ']').replace('{', '}'),
        )
        delim_count = 1
        lws = self.lws + ' ' * 4
        for i, t in enumerate(tail):
            # g.trace(delim_count, str(t))
            if t.kind == 'op' and t.value == ',':
                if delim_count == 1:
                    # Start a new line.
                    self.add_token('op-no-blanks', ',')
                    self.add_token('line-end', '\n')
                    self.add_token('line-indent', lws)
                    # Kill a following blank.
                    if i + 1 < len(tail):
                        next_t = tail[i + 1]
                        if next_t.kind == 'blank':
                            next_t.kind = 'no-op'
                            next_t.value = ''
                else:
                    self.code_list.append(t)
            elif t.kind == close_delim.kind and t.value == close_delim.value:
                # Done if the delims match.
                delim_count -= 1
                if delim_count == 0:
                    if 0:
                        # Create an error, on purpose.
                        # This test passes: proper dumps are created,
                        # and the body is not updated.
                        self.add_token('line-end', '\n')
                        self.add_token('op', ',')
                        self.add_token('number', '666')
                    # Start a new line
                    self.add_token('op-no-blanks', ',')
                    self.add_token('line-end', '\n')
                    self.add_token('line-indent', self.lws)
                    self.code_list.extend(tail[i:])
                    return
                lws = lws[:-4]
                self.code_list.append(t)
            elif t.kind == open_delim.kind and t.value == open_delim.value:
                delim_count += 1
                lws = lws + ' ' * 4
                self.code_list.append(t)
            else:
                self.code_list.append(t)
        g.trace('BAD DELIMS', delim_count)
    #@+node:ekr.20190908050434.1: *6* ptb.find_prev_line (new)
    def find_prev_line(self):
        """Return the previous line, as a list of tokens."""
        line = []
        for t in reversed(self.code_list[:-1]):
            if t.kind == 'line-end':
                break
            line.append(t)
        return list(reversed(line))
    #@+node:ekr.20190908061659.1: *6* ptb.find_line_prefix (new)
    def find_line_prefix(self, token_list):
        """
        Return all tokens up to and including the first lt token.
        Also add all lt tokens directly following the first lt token.
        """
        result = []
        for i, t in enumerate(token_list):
            result.append(t)
            if t.kind == 'lt':
                for t in token_list[i + 1:]:
                    if t.kind == 'blank' or self.is_any_lt(t):
                    # if t.kind in ('lt', 'blank'):
                        result.append(t)
                    else:
                        break
                break
        return result
    #@+node:ekr.20190908072548.1: *6* ptb.is_any_lt
    def is_any_lt(self, output_token):
        """Return True if the given token is any lt token"""
        return (
            output_token == 'lt'
            or output_token.kind == 'op-no-blanks'
            and output_token.value in "{[("
        )
    #@+node:ekr.20190909020458.1: *5* ptb.join_lines (new) & helpers
    def join_lines(self):
        """
        Join preceding lines, if the result would be short enough.
        Should be called only at the end of a line.
        """
        # Must be called just after inserting the line-end token.
        trace = False and not g.unitTesting
        assert self.code_list[-1].kind == 'line-end', repr(self.code_list[-1])
        line_tokens = self.find_prev_line()
        line_s = ''.join([z.to_string() for z in line_tokens])
        if trace:
            g.trace(line_s)
        # Don't bother trying if the line is already long.
        if self.max_join_line_length == 0 or len(line_s) > self.max_join_line_length:
            return
        # Terminating long lines must have ), ] or }
        if not any([z.kind == 'rt' for z in line_tokens]):
            return
        # To do...
        #   Scan back, looking for the first line with all balanced delims.
        #   Do nothing if it is this line.
    #@+node:ekr.20150530190758.1: *4* ptb.line_indent
    def line_indent(self):
        """Add a line-indent token."""
        self.clean('line-indent')
            # Defensive. Should never happen.
        self.add_token('line-indent', self.lws)
    #@+node:ekr.20150526201701.11: *4* ptb.lt & rt
    #@+node:ekr.20190915070456.1: *5* ptb.lt
    def lt(self, s):
        """Generate code for a left paren or curly/square bracket."""
        assert s in '([{', repr(s)
        if s == '(':
            self.paren_level += 1
        elif s == '[':
            self.square_brackets_level += 1
        else:
            self.curly_brackets_level += 1
        self.clean('blank')
        prev = self.code_list[-1]
        if prev.kind in ('op', 'word-op'):
            self.blank()
            self.add_token('lt', s)
        elif prev.kind == 'word':
            # Only suppress blanks before '(' or '[' for non-keyworks.
            if s == '{' or prev.value in ('if', 'else', 'return', 'for'):
                self.blank()
            elif s == '(':
                self.in_arg_list += 1
            self.add_token('lt', s)
        elif prev.kind == 'op':
            self.op(s)
        else:
            self.op_no_blanks(s)
    #@+node:ekr.20190915070502.1: *5* ptb.rt
    def rt(self, s):
        """Generate code for a right paren or curly/square bracket."""
        assert s in ')]}', repr(s)
        if s == ')':
            self.paren_level -= 1
            self.in_arg_list = max(0, self.in_arg_list-1)
        elif s == ']':
            self.square_brackets_level -= 1
        else:
            self.curly_brackets_level -= 1
        self.clean('blank')
        prev = self.code_list[-1]
        if prev.kind == 'arg-end' or (prev.kind, prev.value) == ('op', ':'):
            # # Remove a blank token preceding the arg-end or ')' token.
            prev = self.code_list.pop()
            self.clean('blank')
            self.code_list.append(prev)
        self.add_token('rt', s)
    #@+node:ekr.20150526201701.12: *4* ptb.op*
    def op(self, s):
        """Add op token to code list."""
        assert s and isinstance(s, str), repr(s)
        if self.in_arg_list > 0 and (s in '+-/*' or s == '//'):
            # Treat arithmetic ops differently.
            self.clean('blank')
            self.add_token('op', s)
        else:
            self.blank()
            self.add_token('op', s)
            self.blank()

    def op_blank(self, s):
        """Remove a preceding blank token, then add op and blank tokens."""
        assert s and isinstance(s, str), repr(s)
        self.clean('blank')
        if self.in_arg_list > 0 and s in ('+-/*' or s == '//'):
            self.add_token('op', s)
        else:
            self.add_token('op', s)
            self.blank()

    def op_no_blanks(self, s):
        """Add an operator *not* surrounded by blanks."""
        self.clean('blank')
        self.add_token('op-no-blanks', s)
    #@+node:ekr.20150527213419.1: *4* ptb.possible_unary_op & unary_op
    def possible_unary_op(self, s):
        """Add a unary or binary op to the token list."""
        self.clean('blank')
        prev = self.code_list[-1]
        if prev.kind in ('lt', 'op', 'op-no-blanks', 'word-op'):
            self.unary_op(s)
        elif prev.kind == 'word' and prev.value in (
            'elif', 'else', 'if', 'return', 'while',
        ):
            self.unary_op(s)
        else:
            self.op(s)

    def unary_op(self, s):
        """Add an operator request to the code list."""
        assert s and isinstance(s, str), repr(s)
        self.clean('blank')
        prev = self.code_list[-1]
        prev2 = self.code_list[-2]
        if prev.kind == 'lt':
            self.add_token('unary-op', s)
            return
        if prev2.kind == 'lt' and (prev.kind, prev.value) == ('op', ':'):
            self.add_token('unary-op', s)
            return
        self.blank()
        self.add_token('unary-op', s)
    #@+node:ekr.20150531051827.1: *4* ptb.star_op (no change)
    def star_op(self):
        """Put a '*' op, with special cases for *args."""
        val = '*'
        if self.paren_level > 0:
            i = len(self.code_list) - 1
            if self.code_list[i].kind == 'blank':
                i -= 1
            token = self.code_list[i]
            if token.kind == 'lt':
                self.op_no_blanks(val)
            elif token.value == ',':
                self.blank()
                self.add_token('op-no-blanks', val)
            else:
                self.op(val)
        else:
            self.op(val)
    #@+node:ekr.20150531053417.1: *4* ptb.star_star_op (no changed)
    def star_star_op(self):
        """Put a ** operator, with a special case for **kwargs."""
        val = '**'
        if self.paren_level > 0:
            i = len(self.code_list) - 1
            if self.code_list[i].kind == 'blank':
                i -= 1
            token = self.code_list[i]
            if token.value == ',':
                self.blank()
                self.add_token('op-no-blanks', val)
            else:
                self.op(val)
        else:
            self.op(val)
    #@+node:ekr.20150526201701.13: *4* ptb.word & word_op
    def word(self, s):
        """Add a word request to the code list."""
        assert s and isinstance(s, str), repr(s)
        if self.in_arg_list > 0:
            pass
        else:
            self.blank()
        self.add_token('word', s)
        self.blank()

    def word_op(self, s):
        """Add a word-op request to the code list."""
        assert s and isinstance(s, str), repr(s)
        self.blank()
        self.add_token('word-op', s)
        self.blank()
    #@+node:ekr.20150530064617.1: *3* ptb: Utils
    #@+node:ekr.20190909072007.1: *4* ptb.find_delims (new)
    def find_delims(self, tokens):
        """
        Compute the net number of each kind of delim in the given range of tokens.
        
        Return (curlies, parens, squares)
        """
        parens, curlies, squares = 0, 0, 0
        for token in tokens:
            value = token.value
            if token.kind == 'lt':
                assert value in '([{', f"Bad lt value: {token.kind} {value}"
                if value == '{':
                    curlies += 1
                elif value == '(':
                    parens += 1
                elif value == '[':
                    squares += 1
            elif token.kind == 'rt':
                assert value in ')]}', f"Bad rt value: {token.kind} {value}"
                if value == ')':
                    parens -= 1
                elif value == ']':
                    squares -= 1
                elif value == '}':
                    curlies += 1
        return curlies, parens, squares
    #@+node:ekr.20150528084644.1: *4* ptb.push_state
    def push_state(self, kind, value=None):
        """Append a state to the state stack."""
        state = ParseState(kind, value)
        self.state_stack.append(state)
    #@-others
#@+node:ekr.20190910081550.1: ** class SyntaxSanitizer
class SyntaxSanitizer:

    #@+<< SyntaxSanitizer docstring >>
    #@+node:ekr.20190910093739.1: *3* << SyntaxSanitizer docstring >>
    r"""
    This class converts section references, @others and Leo directives to
    comments. This allows ast.parse to handle the result.

    Within section references, these comments must *usually* be executable:
        
    BEFORE:
        if condition:
            <\< do something >\>
    AFTER:
        if condition:
            pass # do something
            
    Alas, sanitation can result in a syntax error. For example, leoTips.py contains:
        
    BEFORE:
        tips = [
            <\< define tips >\>
            ]

    AFTER:
        tips = [
            pass # define tips
        ]
        
    This fails because tips = [pass] is a SyntaxError.

    The beautify* and black* commands clearly report such failures.
    """
    #@-<< SyntaxSanitizer docstring >>

    def __init__(self, c, keep_comments):
        self.c = c
        self.keep_comments = keep_comments

    #@+others
    #@+node:ekr.20190910022637.2: *3* sanitize.comment_leo_lines
    def comment_leo_lines(self, p=None, s0=None):
        """
        Replace lines containing Leonine syntax with **special comment lines** of the form:
            
            {lws}#{lws}{marker}{line}
            
        where: 
        - lws is the leading whitespace of the original line
        - marker appears nowhere in p.b
        - line is the original line, unchanged.
        
        This convention allows uncomment_special_lines to restore these lines.
        """
        # Choose a marker that appears nowhere in s.
        if p:
            s0 = p.b
        n = 5
        while('#'+ ('!'*n)) in s0:
            n += 1
        comment = '#' + ('!' * n)
        # Create a dict of directives.
        d = {z: True for z in g.globalDirectiveList}
        # Convert all Leonine lines to special comments.
        i, lines, result = 0, g.splitLines(s0), []
        while i < len(lines):
            progress = i
            s = lines[i]
            s_lstrip = s.lstrip()
            # Comment out any containing a section reference.
            j = s.find('<<')
            k = s.find('>>') if j > -1 else -1
            if -1 < j < k:
                result.append(comment+s)
                # Generate a properly-indented pass line.
                j2 = g.skip_ws(s, 0)
                result.append(f'{" "*j2}pass\n')
            elif s_lstrip.startswith('@'):
                # Comment out all other Leonine constructs.
                if self.starts_doc_part(s):
                    # Comment the entire doc part, until @c or @code.
                    result.append(comment+s)
                    i += 1
                    while i < len(lines):
                        s = lines[i]
                        result.append(comment+s)
                        i += 1
                        if self.ends_doc_part(s):
                            break
                else:
                    j = g.skip_ws(s, 0)
                    assert s[j] == '@'
                    j += 1
                    k = g.skip_id(s, j, chars='-')
                    if k > j:
                        word = s[j : k]
                        if word == 'others':
                            # Remember the original @others line.
                            result.append(comment+s)
                            # Generate a properly-indented pass line.
                            result.append(f'{" "*(j-1)}pass\n')
                        else:
                            # Comment only Leo directives, not decorators.
                            result.append(comment+s if word in d else s)
                    else:
                        result.append(s)
            elif s_lstrip.startswith('#') and self.keep_comments:
                # A leading comment.
                # Bug fix: Preserve lws in comments, too.
                j2 = g.skip_ws(s, 0)
                result.append(" "*j2+comment+s)
            else:
                # A plain line.
                result.append(s)
            if i == progress:
                i += 1
        return comment, ''.join(result)
    #@+node:ekr.20190910022637.3: *3* sanitize.starts_doc_part & ends_doc_part
    def starts_doc_part(self, s):
        """Return True if s word matches @ or @doc."""
        return s.startswith(('@\n', '@doc\n', '@ ', '@doc '))

    def ends_doc_part(self, s):
        """Return True if s word matches @c or @code."""
        return s.startswith(('@c\n', '@code\n', '@c ', '@code '))
    #@+node:ekr.20190910022637.4: *3* sanitize.uncomment_leo_lines
    def uncomment_leo_lines(self, comment, p, s0):
        """Reverse the effect of comment_leo_lines."""
        lines = g.splitLines(s0)
        i, result = 0, []
        while i < len(lines):
            progress = i
            s = lines[i]
            i += 1
            if comment in s:
                # One or more special lines.
                i = self.uncomment_special_lines(comment, i, lines, p, result, s)
            else:
                # A regular line.
                result.append(s)
            assert progress < i
        return ''.join(result).rstrip() + '\n'
    #@+node:ekr.20190910022637.5: *3* sanitize.uncomment_special_line & helpers
    def uncomment_special_lines(self, comment, i, lines, p, result, s):
        """
        This method restores original lines from the special comment lines
        created by comment_leo_lines. These lines have the form:
            
            {lws}#{marker}{line}
            
        where: 
        - lws is the leading whitespace of the original line
        - marker appears nowhere in p.b
        - line is the original line, unchanged.
        
        s is a line containing the comment delim.
        i points at the *next* line.
        Handle one or more lines, appending stripped lines to result.
        """
        #
        # Delete the lws before the comment.
        # This works because the tail contains the original whitespace.
        assert comment in s
        s = s.lstrip().replace(comment, '')
        #
        # Here, s is the original line.
        if comment in s:
            g.trace(f"can not happen: {s!r}")
            return i
        if self.starts_doc_part(s):
            result.append(s)
            while i < len(lines):
                s = lines[i].lstrip().replace(comment, '')
                i += 1
                result.append(s)
                if self.ends_doc_part(s):
                    break
            return i
        j = s.find('<<')
        k = s.find('>>') if j > -1 else -1
        if -1 < j < k or '@others' in s:
            #
            # A section reference line or an @others line.
            # Such lines are followed by a pass line.
            #
            # The beautifier may insert blank lines before the pass line.
            kind = 'section ref' if -1 < j < k else '@others'
            # Restore the original line, including leading whitespace.
            result.append(s)
            # Skip blank lines.
            while i < len(lines) and not lines[i].strip():
                i += 1
            # Skip the pass line.
            if i < len(lines) and lines[i].lstrip().startswith('pass'):
                i += 1
            else:
                g.trace(f"*** no pass after {kind}: {p.h}")
        else:
            # A directive line or a comment line.
            result.append(s)
        return i
    #@-others
#@+node:ekr.20191102155252.1: ** class InputTokenizer
class InputTokenizer:
    
    """Create a list of BeautifierTokens from contents."""
    
    trace = False
    
    #@+others
    #@+node:ekr.20191105064919.1: *3* tok.add_token
    def add_token(self, kind, line, s_row, value):
        """
        Add a token to the results list.
        
        Subclasses could override this method to filter out specific tokens.
        """
        tok = BeautifierToken(kind, value)
        tok.line = line
        tok.line_number = s_row
        self.results.append(tok)
    #@+node:ekr.20191102155252.2: *3* tok.create_input_tokens
    def create_input_tokens(self, contents, tokens):
        """
        Generate a list of BeautifierToken's from tokens, a list of 5-tuples.
        
        This is part of the "gem".
        """
        # Create the physical lines.
        self.lines = contents.splitlines(True)
        # Create the list of character offsets of the start of each physical line.
        last_offset, self.offsets = 0, [0]
        for line in self.lines:
            last_offset += len(line)
            self.offsets.append(last_offset)
        # Trace lines & offsets.
        self.show_header()
        # Handle each token, appending tokens and between-token whitespace to results.
        self.prev_offset, self.results = -1, []
        for token in tokens:
            self.do_token(contents, token)
        # Print results when tracing.
        self.check_results(contents)
        if self.trace:
            self.show_results(contents)
        # Return the concatentated results.
        return self.results
    #@+node:ekr.20191102155252.3: *3* tok.do_token
    def do_token(self, contents, token):
        """
        Handle the given token, optionally including between-token whitespace.
        
        This is part of the "gem".
        """
        # self.trace = True

        def show_tuple(aTuple):
            s = f"{aTuple[0]}..{aTuple[1]}"
            return f"{s:8}"
            
        # Unpack..
        tok_type, val, start, end, line = token
        s_row, s_col = start
        e_row, e_col = end
        kind = token_module.tok_name[tok_type].lower()
        # Calculate the token's start/end offsets: character offsets into contents.
        s_offset = self.offsets[max(0, s_row-1)] + s_col
        e_offset = self.offsets[max(0, e_row-1)] + e_col
        # Add any preceding between-token whitespace.
        ws = contents[self.prev_offset : s_offset]
        if ws:
            # No need for a hook.
            self.add_token('ws', line, s_row, ws)
            if self.trace:
                print(
                    f"{'ws':>10} {ws!r:20} "
                    f"{show_tuple((self.prev_offset, s_offset)):>26} "
                    f"{ws!r}")
        # Add the token, if it contributes any real text.
        tok_s = contents[s_offset : e_offset]
        # Bug fix 2019/11/05: always add token, even it contributes text!
        self.add_token(kind, line, s_row, tok_s)
        if self.trace:
            print(
                f"{kind:>10} {val!r:20} "
                f"{show_tuple(start)} {show_tuple(end)} {show_tuple((s_offset, e_offset))} "
                f"{tok_s!r:15} {line!r}")
        # Update the ending offset.
        self.prev_offset = e_offset
    #@+node:ekr.20191102155252.4: *3* tok.show_header
    def show_header(self):
        
        if g.unitTesting:
            return
        if not self.trace:
            return
        # Dump the lines.
        print('Physical lines: (row, offset, line)\n')
        for i, z in enumerate(self.lines):
            print(f"{i:3}: {self.offsets[i]:3}: {z!r}")
        # Print the header for the list of tokens.
        print('\nTokens:')
        print(
            f"{'kind':>10} {'val'} {'start':>22} {'end':>6} "
            f"{'offsets':>12} {'output':>7} {'line':>13}")
    #@+node:ekr.20191102155252.5: *3* tok.show_results
    def show_results(self, contents):

        # Split the results into lines.
        result = ''.join([z.to_string() for z in self.results])
        result_lines = result.splitlines(True)
        if result == contents and result_lines == self.lines:
            # print('\nRound trip passes')
            return
        print('Results:')
        for i, z in enumerate(result_lines):
            print(f"{i:3}: {z!r}")
        print('FAIL')
    #@+node:ekr.20191105072003.1: *3* tok.check_results
    def check_results(self, contents):

        # Split the results into lines.
        result = ''.join([z.to_string() for z in self.results])
        result_lines = result.splitlines(True)
        # Check.
        ok = result == contents and result_lines == self.lines
        assert ok, (
            f"result:   {result!r}\n"
            f"contents: {contents!r}\n"
            f"result_lines: {result_lines}\n"
            f"lines:        {self.lines}"
        )
    #@-others
#@-others
if __name__ == "__main__":
    main()
#@@language python
#@@tabwidth -4
#@@last
#@-leo

