# Written by Omer Levy, modified by Javad Hosseini

from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet as wn
import numpy as np
from nltk.corpus import verbnet



debug = False

# STOPWORDS = stopwords.words('chinese') [for now we DON'T use stopwords for Chinese.]


def read_vectors(path, topn):  # read top n word vectors, i.e. top is 10000
    lines_num, dim = 0, 0
    vectors = {}
    iw = []
    wi = {}
    with open(path, encoding='utf-8', errors='ignore') as f:
        first_line = True
        for line in f:
            if first_line:
                first_line = False
                dim = int(line.rstrip().split()[1])
                continue
            lines_num += 1
            tokens = line.rstrip().split(' ')
            vectors[tokens[0]] = np.asarray([float(x) for x in tokens[1:]])
            iw.append(tokens[0])
            if topn != 0 and lines_num >= topn:
                break
    for i, w in enumerate(iw):
        wi[w] = i
    return vectors, iw, wi, dim


'''
def is_antonym(x, y):
    pos_tags = ['n', 'v', 'a', 'r']
    x_ants_syns = []
    for pos in pos_tags:
        syns = wn.synsets(x, pos)
        if len(syns) == 0:
            continue
        lemmas = syns[0].lemmas()
        if len(lemmas) == 0:
            continue
        lemma = lemmas[0]
        ants = lemma.antonyms()
        if len(ants) == 0:
            continue
        x_ants_syns.append(ants[0].synset()._name)
    y_syns = [syn._name for syn in wn.synsets(y)]
    # print "x_ant_syns", x_ants_syns
    # print "y_sins: ", y_syns
    # print "intersect: ", set(y_syns).intersection(set(x_ants_syns))

    return len(set(y_syns).intersection(set(x_ants_syns))) > 0
'''


def active_pass_normalize(p):
    if ".1," in p and ".2)" in p:

        idx = p.index(".1")
        a = p[1:idx]
        idx2 = p.index(".2)")
        b = p[idx + 3:idx2]
        if a == b:
            return a
        else:
            return None
    elif ".2," in p and ".by.2)" in p:

        idx = p.index(".2")
        a = p[1:idx]
        idx2 = p.index(".by.2)")
        b = p[idx + 3:idx2]
        if a == b:
            return a
        else:
            return None
    return None

'''
def get_lemmas(phrase, pos=wn.VERB):
    return [LEMMATIZER.lemmatize(w, pos) for w in phrase.split(' ')]
def get_lemmas_only_verbs(phrase, pos=wn.VERB):
    return set([w for w in get_lemmas(phrase, pos) if len(wn.synsets(w, pos)) > 0])
def get_lemmas_no_stopwords(phrase, pos=wn.VERB):
    return set([w for w in get_lemmas(phrase, pos) if w not in STOPWORDS])
'''


def aligned_args_rel(q, a):
    # These are not necessary if the sentences are well formed!
    # in chinese there's no need to lemmatize!
    q1 = q[1].split("::")[0].lower()
    q2 = q[2].split("::")[0].lower()
    a1 = a[1].split("::")[0].lower()
    a2 = a[2].split("::")[0].lower()
    if q1 == a1:
        return True
    elif q1 == a2:
        return False
    else:
        if q2 == a1:
            return False
        elif q2 == a2:
            return True
        if debug:
            print ("not sure if aligned: ", q, a)
        return True  # This is a bad case!


def aligned_args(q, a):
    if debug:
        print ("is_algined: ", q, " ", a)
    q_arg = q[2]
    if q_arg == a[2]:
        return True
    if q_arg == a[0]:
        return False
    return -1


def diff(q, a):
    q_tokens = q.split(' ')
    a_tokens = a.split(' ')
    min_len = min(len(q_tokens), len(a_tokens))

    for start, (qw, qa) in enumerate(zip(q_tokens[:min_len], a_tokens[:min_len])):
        if qw != qa:
            break

    for end, (qw, qa) in enumerate(zip(q_tokens[::-1][:min_len], a_tokens[::-1][:min_len])):
        if qw != qa:
            break

    if end > 0:
        q_tokens = q_tokens[start:-end]
        a_tokens = a_tokens[start:-end]
    else:
        q_tokens = q_tokens[start:]
        a_tokens = a_tokens[start:]

    return ' '.join(q_tokens), ' '.join(a_tokens)


# (see.1,see.2) -> (see.2,see.1)
def swap(p):
    p = p[1:len(p) - 1]
    ps = p.split(",")
    p = "(" + ps[1] + "," + ps[0] + ")"
    return p


def is_sorted(p):
    p = p[1:len(p) - 1]
    ps = p.split(",")
    try:
        ret = ps[0] <= ps[1]
        return ret
    except:
        return True


# def print_all_ants():
#     for i in wn.all_synsets():
#         if i.pos() in ['a', 's']:  # If synset is adj or satelite-adj.
#             for j in i.lemmas():  # Iterating through lemmas for each synset.
#                 if j.antonyms():  # If adj has antonym.
#                     # Prints the adj-antonym pair.
#                     print (j.name(), j.antonyms()[0].name())


# # The name should be lemmatized in advance
# def get_hypernyms(n):
#     ret = [n]
#     try:
#         noun = wn.synset(n + ".n" + ".01")
#         while 1 == 1:
#             hs = noun.hypernyms()
#             if len(hs) == 0:
#                 return ret
#             noun = hs[0]
#             ret.append(str(hs[0].lemmas()[0].name()))
#             # print noun.lemmas()
#     except Exception:
#         pass
#     return ret


def get_tuples(fname):
    f = open(fname, 'r', encoding='utf8')
    lines = f.read().splitlines()
    test = []

    for line in lines:
        ss = line.split("\t")
        q = ss[0].split(",")
        q = [s.strip() for s in q]
        p = ss[1].split(",")
        p = [s.strip() for s in p]
        v = ss[2]
        test.append((q, p, v))
    f.close()
    return test


def get_raws(fname):
    fp = open(fname, 'r', encoding='utf8')
    test = []
    for line in fp:
        line = line.split("\t")
        assert len(line) == 4  # prem, hypo, masked_prem, masked_hypo
        prem = line[0].strip()
        hypo = line[1].strip()
        test.append((prem, hypo))
    fp.close()
    return test


def same_main_words(p, q, prepositions):
    ss_p = p[1:-1].replace(',', ' ').replace('.', ' ').split()
    ss_q = q[1:-1].replace(',', ' ').replace('.', ' ').split()
    s1 = set(ss_p)
    s2 = set(ss_q)
    nums = ['1', '2', '3']
    for x in s1:
        if x in prepositions or x in nums:
            continue
        if x not in s2:
            return False

    for x in s2:
        if x in prepositions or x in nums:
            continue
        if x not in s1:
            return False
    return True


# (appoint.1,appoint.2) , (under.1,under.2) => True
def same_CCG_args(p, q):
    ss_p = p[1:-1].split(",")
    ss_q = q[1:-1].split(",")

    last_dot_p = ss_p[0].rfind('.')
    main_pred_p = ss_p[0][:last_dot_p]

    last_dot_q = ss_q[0].rfind('.')
    main_pred_q = ss_q[0][:last_dot_q]

    voices_p = []
    voices_q = []

    voices_p.append(int(ss_p[0][last_dot_p + 1:]))
    voices_q.append(int(ss_q[0][last_dot_q + 1:]))

    # Check cases like (wash.in.2,wash.on.2)
    if voices_p[0] == 2 and ss_p[0].count(".") > 1:
        voices_p[0] = 4
    if voices_q[0] == 2 and ss_q[0].count(".") > 1:
        voices_q[0] = 4

    last_dot_p = ss_p[1].rfind('.')
    rpred_p = ss_p[1][:last_dot_p]

    last_dot_q = ss_q[1].rfind('.')
    rpred_q = ss_q[1][:last_dot_q]

    if rpred_p == main_pred_p and voices_p[0] != 4:
        voices_p.append(int(ss_p[1][last_dot_p + 1:]))
    else:
        voices_p.append(4)

    if rpred_q == main_pred_q and voices_q[0] != 4:
        voices_q.append(int(ss_q[1][last_dot_q + 1:]))
    else:
        voices_q.append(4)

    return voices_p == voices_q


# def transitive_reverse(p, q, a):
#     if p == q and not a:
#         lemma = p[1:-1].split(',')[0].split('.')[0]
#         ret = is_transitive(lemma)
#         if ret:
#             if debug:
#                 print ("constraint transitive verb: ", p, q, a)
#         return ret
#     return False


# def is_transitive(lemma):
#     try:
#         cids = verbnet.classids(lemma)
#         frames = verbnet.frames(verbnet.vnclass(cids[0]))
#         ret = False
#         # for frame in frames:
#         #     print "primary:", frame['description']['primary']
#         #     ret = ret or "Transitive" in frame['description']['primary']
#
#         ret = "Transitive" in frames[0]['description']['primary']
#         return ret
#     except:
#         return False
