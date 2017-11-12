import os
import re


base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
lib_dir = os.path.join(base_dir, 'lib')
data_dir = os.path.join(base_dir, 'data')

classpath = ':'.join([
        lib_dir,
        os.path.join(lib_dir, 'stanford-parser\stanford-parser.jar'),
        os.path.join(lib_dir, 'stanford-parser\stanford-parser-3.5.1-models.jar'),
        os.path.join(lib_dir, 'easyccg\easyccg.jar')])


def make_dirs(dirs):
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)


def build_vocab(filepaths):
    vocab = set()
    for filepath in filepaths:
        with open(filepath) as f:
            for line in f:
                line = line.lower()
                vocab |= set(line.split())
    return vocab


def save_vocab(destination, vocab):
    with open(destination, 'w') as f:
        for w in sorted(vocab):
            f.write(w + '\n')


def move_numbers_from_known(vocab, vocab_unk):
    r = re.compile(r"(\+|\-)?\d+(\.\d+)?(\/\d+)?")
    to_move = []
    for v in vocab:
        if r.match(v) is not None:
            to_move.append(v)
    vocab -= set(to_move)
    vocab_unk |= set(to_move)
    return vocab, vocab_unk


def tokenize(filepath):
    print('\nTokenizing ' + filepath)
    dirpath = os.path.dirname(filepath)
    filepre = os.path.splitext(os.path.basename(filepath))[0]
    tokpath = os.path.join(dirpath, filepre + '.tokens')
    cmd = ('java -cp %s Tokenize -tokpath %s < %s'
           % (classpath, tokpath, filepath))
    os.system(cmd)


def parse_for_variables(filepath, vocab_unk):
    print('\nParsing variables ' + filepath)
    dirpath = os.path.dirname(filepath)
    filepre = os.path.splitext(os.path.basename(filepath))[0]
    varpath = os.path.join(dirpath, filepre + '.variables')
    with open(filepath, 'r') as datafile, \
         open(varpath, 'w') as vfile:
        for line in datafile:
            tokens = set(line.split(" "))
            variables = tokens & vocab_unk
            ln = " ".join(variables) + "\n"
            vfile.write(ln)


def dependency_parse(filepath, vocabpath):
    print('\nDependency parsing ' + filepath)
    dirpath = os.path.dirname(filepath)
    filepre = os.path.splitext(os.path.basename(filepath))[0]
    parentpath = os.path.join(dirpath, filepre + '.dependency_parents')
    relpath = os.path.join(dirpath, filepre + '.dependency_rels')
    cmd = ('java -cp %s DependencyParse -parentpath %s -relpath %s < %s'
        % (classpath, parentpath, relpath, filepath))
    os.system(cmd)


def constituency_parse(filepath, vocabpath):
    print('\nConstituency parsing ' + filepath)
    dirpath = os.path.dirname(filepath)
    filepre = os.path.splitext(os.path.basename(filepath))[0]
    parentpath = os.path.join(dirpath, filepre + '.constituency_parents')
    cmd = ('java -cp %s ConstituencyParse -parentpath %s < %s'
        % (classpath, parentpath, filepath))
    os.system(cmd)


def ccg_parse(filepath, vocabpath):
    print('\nCCG parsing ' + filepath)
    dirpath = os.path.dirname(filepath)
    filepre = os.path.splitext(os.path.basename(filepath))[0]
    parentpath = os.path.join(dirpath, filepre + '.ccg_parents')
    cmd = ('java -cp %s CCGParse -parentpath %s -modelpath lib/easyccg/model < %s'
           % (classpath, parentpath, filepath))
    os.system(cmd)


def parse(filepath, vocabpath):
    dependency_parse(filepath, vocabpath)
    constituency_parse(filepath, vocabpath)
    ccg_parse(filepath, vocabpath)