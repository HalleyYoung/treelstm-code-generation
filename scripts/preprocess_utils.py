import os
import platform
import torch
import astor
import logging

from natural_lang.vocab import Vocab
from utils.io import serialize_to_file
from lang.unaryclosure import apply_unary_closures, get_top_unary_closures
from lang.parse import *


base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
lib_dir = os.path.join(base_dir, 'lib')
data_dir = os.path.join(base_dir, 'data')

system = 'w' if platform.system() == 'Windows' else 'nw'

delimiter = ';' if system == 'w' else ':'

classpath = delimiter.join([
        lib_dir,
        os.path.join(lib_dir, 'stanford-parser/stanford-parser.jar'),
        os.path.join(lib_dir, 'stanford-parser/stanford-parser-3.5.1-models.jar'),
        os.path.join(lib_dir, 'easyccg/easyccg.jar')])


def make_dirs(dirs):
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)


def build_vocab_from_token_files(filepaths, lower=False, min_frequency=1):
    freq_dict = {}
    logging.info('Building vocabulary from token files...')
    for filepath in tqdm(filepaths):
        with open(filepath) as f:
            for line in f:
                if lower:
                    line = line.lower()
                for item in line.split():
                    if item in freq_dict:
                        freq_dict[item] += 1
                    else:
                        freq_dict[item] = 1
    vocab = {k for k, v in freq_dict.items() if v >= min_frequency}
    logging.debug('Total items: {}, with min frequency: {}.'.format(len(freq_dict), len(vocab)))
    return vocab


def build_vocab_from_items(items, lower=False, min_frequency=1):
    freq_dict = {}
    logging.info('Building vocabulary from items...')
    for item in tqdm(items):
        if lower:
            item = item.lower()
        if item in freq_dict:
            freq_dict[item] += 1
        else:
            freq_dict[item] = 1
    vocab = {k for k, v in freq_dict.items() if v >= min_frequency}
    logging.debug('Total items: {}, with min frequency: {}.'.format(len(freq_dict), len(vocab)))
    return vocab


def save_vocab(destination, vocab):
    logging.info('Writing vocabulary: ' + destination)
    with open(destination, 'w', encoding='utf-8') as f:
        for w in tqdm(sorted(vocab)):
            f.write(w + '\n')


def tokenize(filepath):
    logging.info('Tokenizing ' + filepath)
    dirpath = os.path.dirname(filepath)
    filepre = os.path.splitext(os.path.basename(filepath))[0]
    tokpath = os.path.join(dirpath, filepre + '.tokens')
    cmd = ('java -cp %s Tokenize -tokpath %s < %s'
           % (classpath, tokpath, filepath))
    os.system(cmd)


def dependency_parse(filepath):
    logging.info('Dependency parsing ' + filepath)
    dirpath = os.path.dirname(filepath)
    filepre = os.path.splitext(os.path.basename(filepath))[0]
    parentpath = os.path.join(dirpath, filepre + '.dependency_parents')
    relpath = os.path.join(dirpath, filepre + '.dependency_rels')
    cmd = ('java -cp %s DependencyParse -parentpath %s -relpath %s < %s'
        % (classpath, parentpath, relpath, filepath))
    os.system(cmd)


def constituency_parse(filepath):
    logging.info('Constituency parsing ' + filepath)
    dirpath = os.path.dirname(filepath)
    filepre = os.path.splitext(os.path.basename(filepath))[0]
    parentpath = os.path.join(dirpath, filepre + '.constituency_parents')
    catpath = os.path.join(dirpath, filepre + '.constituency_categories')
    cmd = ('java -cp {} ConstituencyParse -parentpath {} -catpath {} < {}'.format
        (classpath, parentpath, catpath, filepath))
    os.system(cmd)


def ccg_parse(filepath):
    logging.info('CCG parsing ' + filepath)
    dirpath = os.path.dirname(filepath)
    filepre = os.path.splitext(os.path.basename(filepath))[0]
    parentpath = os.path.join(dirpath, filepre + '.ccg_parents')
    catpath = os.path.join(dirpath, filepre + '.ccg_categories')
    cmd = ('java -cp {} CCGParse -parentpath {} -catpath {} -modelpath '
           'lib/easyccg/model < {}'.format(classpath, parentpath, catpath, filepath))
    os.system(cmd)


def parse(filepath):
    dependency_parse(filepath)
    constituency_parse(filepath)
    ccg_parse(filepath)


# loading GLOVE word vectors
# if .pth file is found, will load that
# else will load from .txt file & save
def load_word_vectors(path):
    if os.path.isfile(path+'.pth') and os.path.isfile(path+'.vocab'):
        logging.info('Glove file found, loading to memory...')
        vectors = torch.load(path+'.pth')
        vocab = Vocab(filename=path+'.vocab')
        return vocab, vectors
    # saved file not found, read from txt file
    # and create tensors for word vectors
    logging.info('Glove file not found, preparing, be patient...')
    count = sum(1 for line in open(path+'.txt'))
    with open(path+'.txt', 'r') as f:
        contents = f.readline().rstrip('\n').split(' ')
        dim = len(contents[1:])
    words = [None]*(count)
    vectors = torch.zeros(count,dim)
    with open(path+'.txt','r') as f:
        idx = 0
        for line in f:
            contents = line.rstrip('\n').split(' ')
            words[idx] = contents[0]
            vectors[idx] = torch.Tensor(list(map(float, contents[1:])))
            idx += 1
    with open(path+'.vocab', 'w') as f:
        for word in words:
            f.write(word+'\n')
    vocab = Vocab(filename=path+'.vocab')
    torch.save(vectors, path+'.pth')
    return vocab, vectors


def parse_code_trees(code_file, code_out_file):
    logging.info('Parsing code trees from file {}'.format(code_file))
    parse_trees = []
    codes = []
    rule_num = 0.
    example_num = 0
    for line in tqdm(open(code_file).readlines()):
        lb = 'В§' if system == 'w' else '§'
        code = line.replace(lb, '\n').replace('    ', '\t')
        code = canonicalize_code(code)
        codes.append(code)

        p_tree = parse_raw(code)
        # sanity check
        pred_ast = parse_tree_to_python_ast(p_tree)
        pred_code = astor.to_source(pred_ast)
        ref_ast = ast.parse(code)
        ref_code = astor.to_source(ref_ast)

        if pred_code != ref_code:
            raise RuntimeError('code mismatch!')

        rules, _ = p_tree.get_productions(include_value_node=False)
        rule_num += len(rules)
        example_num += 1

        parse_trees.append(p_tree)

    serialize_to_file(codes, code_out_file)
    return parse_trees


def write_grammar(parse_trees, out_file):
    grammar = get_grammar(parse_trees)

    serialize_to_file(grammar, out_file + '.bin')
    with open(out_file, 'w') as f:
        for rule in tqdm(grammar):
            str = rule.__repr__()
            f.write(str + '\n')

    return grammar


def write_terminal_tokens_vocab(grammar, parse_trees, out_file, min_freq=2):
    terminal_token_seq = []

    for parse_tree in tqdm(parse_trees):
        for node in parse_tree.get_leaves():
            if grammar.is_value_node(node):
                terminal_val = node.value
                terminal_str = str(terminal_val)

                terminal_tokens = get_terminal_tokens(terminal_str)

                for terminal_token in terminal_tokens:
                    terminal_token_seq.append(terminal_token)

    terminal_vocab = build_vocab_from_items(terminal_token_seq, False, min_freq)
    save_vocab(out_file, terminal_vocab)


def do_unary_closures(parse_trees, k):
    logging.info('Applying unary closures to parse trees...')
    unary_closures = get_top_unary_closures(parse_trees, k=k)
    for parse_tree in tqdm(parse_trees):
        apply_unary_closures(parse_tree, unary_closures)


def write_trees(parse_trees, out_file):
    # save data
    with open(out_file, 'w') as f:
        for tree in tqdm(parse_trees):
            f.write(tree.__repr__() + '\n')
    serialize_to_file(parse_trees, out_file + '.bin')