from scipy import interpolate
from copy import deepcopy
import sys
import numpy as np

debug = False

class Graph:

    num_feats = -1
    zeroFeats = None
    certainFeats = None
    certainFeats = None
    num_edges = 0
    num_edges_threshold = 0#cos >1e-4
    threshold = -1
    featIdx = 4

    #There are two ways to init!
    def __init__(self,gpath=-1,idxes=-1,idx2Node=-1,idx2ArrIdx = None, idxpair2score = None, nodes=-1,name=-1, args=None):
        if gpath!=-1:
            self.args = args
            self.buildGraphFromFile(gpath)
        else:
            self.idx2Node = idx2Node
            self.idxes = idxes
            self.nodes = nodes
            self.name = name
            self.idx2ArrIdx = idx2ArrIdx
            self.idxpair2score = idxpair2score
            self.args = args


    def set_num_feats(self,gpath):
        #get the first pred
        f = open(gpath, encoding='utf-8', encoding='utf-8')
        if debug:
            print ("gpath: ", gpath)

        if self.args and self.args.saveMemory:
            Graph.num_feats = 2
            return

        seen_preds = 0
        num_feats = 0
        for line in f:
            line = line.strip()
            if line.startswith("predicate:"):
                seen_preds +=1
                if seen_preds==2:
                    Graph.num_feats = 2*num_feats#half if for rank
                    Graph.zeroFeats = np.zeros(shape=Graph.num_feats)
                    Graph.certainFeats = np.repeat(0.99902344, Graph.num_feats)
                    Graph.certainFeats = np.around(Graph.certainFeats, decimals=4)
                    Graph.certainFeats = np.repeat(0.99902344, Graph.num_feats)
                    Graph.certainFeats = np.around(Graph.certainFeats, decimals=4)
                    break
            if line.endswith("sims") or line.endswith("sim"):
                num_feats += 1
        if debug:
            print ("num_feats: ", Graph.num_feats)
        f.close()

    def buildGraphFromFile(self,gpath):
        if Graph.num_feats==-1:
            self.set_num_feats(gpath)
        if self.args and self.args.threshold:
            Graph.threshold = self.args.threshold
        f = open(gpath, encoding='utf-8', encoding='utf-8')
        Graph.featIdx = 0 if self.args and self.args.saveMemory else Graph.featIdx
        self.pred2Node = {}#This should be mainly because we read from file, in other inits, we don't need it!
        self.idx2Node = {}
        self.nodes = []
        self.idx2ArrIdx = None #This means if nIdx == arrIdx (contiguous blocks of idxes)
        self.idxpair2score = {}
        self.unary2nodeIdxes = {}

        first = True
        #read the lines and form the graph
        lIdx = 0

        isConj = False

        for line in f:
            line = line.replace("` ","").rstrip()
            # print (line)
            if debug and lIdx % 1000000 == 0 and lIdx!=0:
                print ("lidx: ", lIdx)

                s1 = sys.getsizeof(self.pred2Node)
                s2 = sys.getsizeof(self.idx2Node)
                s3 = sys.getsizeof(self.nodes)

                print ("pred2Node size: ", s1)
                print ("idx2Node size: ", s2)
                print ("nodes array size: ", s3)


                idx2OedgesSize = 0
                oedgessize = 0
                allnodesSize = 0
                alloedgesSize = 0
                simsOrderSize = 0

                for n in self.nodes:
                    idx2OedgesSize += sys.getsizeof(n.idx2oedges)
                    oedgessize += sys.getsizeof(n.oedges)
                    allnodesSize += sys.getsizeof(n)
                    for oedge in n.oedges:
                        alloedgesSize += sys.getsizeof(oedge)
                        simsOrderSize  += sys.getsizeof(oedge.sims) + sys.getsizeof(oedge.orders)
                print ("idx2Oedges size: ", idx2OedgesSize)
                print ("oedges size: ", oedgessize)
                print ("all nodes size: ", allnodesSize)
                print ("all oedges size: ", alloedgesSize)
                print ("simsOrderSize: ", simsOrderSize)

                allSize = s1 + s2 + s3+ idx2OedgesSize + oedgessize + allnodesSize + alloedgesSize + simsOrderSize
                print ("all size: ", allSize)

            lIdx += 1
            if first:  # such as: types: art#art, num preds: 129  # such as: types: art#art, num preds: 129
                self.name = line
                self.types = line.split(",")[0].split(" ")[1].split("#")
                if len(self.types) < 2:
                    self.types = line.split(" ")[0].split("#")
                    # raise AssertionError
                if len(self.types) == 2:
                    if self.types[0] == self.types[1]:
                        self.types[0] += "_1"
                        self.types[1] += "_2"

                first = False

            elif line == "":
                continue

            elif line.startswith("predicate:"):  # such as: "predicate: (成为.1, 成为.2)#art_1#art_2"  # such as: "predicate: (成为.1, 成为.2)#art_1#art_2"
                #time to read a predicate
                pred = line[11:]
                if self.args.CCG and Graph.is_conjunction(pred):
                    isConj = True
                    continue
                else:
                    isConj = False

                #The node
                if pred not in self.pred2Node:
                    nIdx = len(self.nodes)
                    #print "nIdx: ", nIdx
                    node = Node(pred,nIdx)
                    self.insertNode(node)
                node = self.pred2Node[pred]

                if not self.args or not self.args.saveMemory:
                    feat_idx = -1
                else:
                    feat_idx = 0

                sim_name = "none"

            else:
                if self.args.CCG and isConj:
                    # print "isConj"
                    continue
                if "num neighbors" in line:  # such as "num neighbors: 22"  # such as "num neighbors: 22"
                    continue
                #This means we have #cos sim, etc
                if line.endswith("sims") or line.endswith("sim"):
                    order = 0  # number of out edges for this predicate  # number of out edges for this predicate
                    if not self.args or not self.args.saveMemory:
                        feat_idx += 1
                    sim_name = line.lower()
                    # print ("line was: ", line)
                    #cos: 0, lin's prob: 1, etc

                else:  # the actual lines of similarity scores, such as: (记录.1,记录.2)#art_1#art_2 0.23808833179205025  # the actual lines of similarity scores, such as: (记录.1,记录.2)#art_1#art_2 0.23808833179205025
                    #Now, we've got sth interesting!
                    if self.args and self.args.saveMemory and not "binc" in sim_name:  # only calculate BInc in saveMemory mode -- Teddy
                        continue

                    try:
                        ss = line.split(" ")
                        assert len(ss) == 2
                        assert len(ss) == 2
                        nPred = ss[0]  # name of predicate  # name of predicate
                        if self.args.CCG and Graph.is_conjunction(nPred):
                            continue
                        sim = ss[1]
                    except:
                        continue

                    order += 1

                    if self.args.maxRank and order>self.args.maxRank:  # if number of edges exceeds threshold (if specified) -- Teddy  # if number of edges exceeds threshold (if specified) -- Teddy
                        continue

                    if nPred not in self.pred2Node:  # the target predicate node.  # the target predicate node.
                        nIdx = len(self.nodes)
                        nNode = Node(nPred,nIdx)
                        self.insertNode(nNode)
                    nNode = self.pred2Node[nPred]

                    #It checks and see if we have the node, then it doesn't add it!
                    node.addNeighbor(nNode)
                    # print "adding: ", sim, " ", line, " ", pred, " ", nPred
                    node.add_sim(nNode,sim,feat_idx,order)

        f.close()

        print ("num edges in gr: ", Graph.num_edges, str(Graph.threshold), Graph.num_edges_threshold, gpath)

        self.idxes = range(len(self.nodes))

    #in: (go.1,go.2)#person#location
    #adding: go.1#person=>node and go.2#location=>node
    def add_unary2binary(self, node):
        # print "adding unary 2 binary for:", node.id
        try:
            if "__" in node.id:
                return

            # (pred.1, pred.2)#type_1#type_2
            # (pred.1, pred.2)#type_1#type_2
            ss = node.id.replace("_1", "").replace("_2", "").split("#")
            unaries = ss[0][1:-1].split(",") # [pred.1, pred.2] # [pred.1, pred.2]

            thisType0 = ss[1] # type # type
            thisType1 = ss[2] # type # type
            unaries[0] += "#"+ thisType0
            unaries[1] += "#"+ thisType1

            if unaries[0] not in self.unary2nodeIdxes:
                self.unary2nodeIdxes[unaries[0]] = []
            if unaries[1] not in self.unary2nodeIdxes:
                self.unary2nodeIdxes[unaries[1]] = []
            # print "adding unary 2 binary: ", unaries[0], node.id
            # print "adding unary 2 binary: ", unaries[1], node.id
            self.unary2nodeIdxes[unaries[0]].append(node.idx)
            self.unary2nodeIdxes[unaries[1]].append(node.idx)
        except:
            if debug:
                print ("unary exception for: ", node.id)
            pass



    #idexes is the list of indices, c is the component number (just for the name)
    def getSubset(self,idxes, c):
        idx2Node = {}
        idx2ArrIdx = {}
        nodes = []
        name = self.name + "_" + str(c)

        for arrIdx,idx in enumerate(idxes):
            #print "idx: ", idx
            idx2ArrIdx[idx] = arrIdx

        for arrIdx,idx in enumerate(idxes):
            node = self.idx2Node[idx].getSubset(idxes,idx2ArrIdx)
            nodes.append(node)
            idx2Node[idx] = node


        idxpair2score = {}

        for (i,j) in self.idxpair2score.keys():
            if i in idx2ArrIdx and j in idx2ArrIdx:
                a = idx2ArrIdx[i]
                b = idx2ArrIdx[j]
                idxpair2score[(a,b)] = self.idxpair2score[(i,j)]

        g = Graph(idx2Node=idx2Node, idx2ArrIdx = idx2ArrIdx, idxpair2score = idxpair2score, nodes=nodes,name=name,idxes=idxes)
        return g

    def set_Ws(self):
        for node in self.nodes:
            node.setWPs(self)

    def __str__(self):
        ret = ""
        for node in self.nodes:
            ret += node.__str__() + "\n"
        return ret


    def insertNode(self,node):
        self.pred2Node[node.id] = node
        self.idx2Node[node.idx] = node
        self.nodes.append(node)
        if len(self.types) == 2:
            self.add_unary2binary(node)

    def get_w_fast(self,i,j):
        if i==j:
            return 1
        elif (i,j) not in self.idxpair2score:
            return 0
        else:
            return self.idxpair2score[(i,j)]


    def get_w(self,i,j):
        node = self.idx2Node[i]
        return node.get_w(j)

    def get_sim(self,i,j,lmbda):
        return self.get_w(i,j) - lmbda

    #Given (speaks.1,speaks.2) and (evacuate.1,evacuate.2),
    def get_features(self,p,q):
        if p not in self.pred2Node or q not in self.pred2Node:
            return None

        elif p==q:
            return Graph.certainFeats
        else:
            node1 = self.pred2Node[p]
            node2 = self.pred2Node[q]

            if node2.idx not in node1.idx2oedges:
                return Graph.zeroFeats

            sims = node1.idx2oedges[node2.idx].sims
            orders = node1.idx2oedges[node2.idx].orders
            ret = np.zeros(shape=(2*len(sims)))
            ret[:len(sims)] = deepcopy(sims)
            ret[len(sims):] = orders
            return ret


    #Just the similarities, not ranks
    def get_features_unary(self, u, v):
        # print "get feats unary: ", u, v

        if u not in self.unary2nodeIdxes or v not in self.unary2nodeIdxes:
            return None, -1
        else:

            sims = np.zeros(shape=(Graph.num_feats//2))

            sum_coefs = 0

            node1s = [self.nodes[idx] for idx in self.unary2nodeIdxes[u]]
            node2s = [self.nodes[idx] for idx in self.unary2nodeIdxes[v]]

            for node1 in node1s:
                for node2 in node2s:
                    coef = np.minimum(len(node1.oedges),len(node2.oedges))
                    sum_coefs += coef
                    if u!=v and node2.idx in node1.idx2oedges:
                        this_sims = node1.idx2oedges[node2.idx].sims
                        sims += coef * this_sims

            if u == v:
                sims = np.ones(shape=(Graph.num_feats / 2))
            elif sum_coefs!=0:
                sims /= sum_coefs
            return sims, sum_coefs

    @staticmethod
    def is_conjunction(p):
        p = p.split("#")[0][1:-1]
        ps = p.split(",")
        return len(ps)<2 or ps[0]==ps[1]


class Node:

    eps = 1e-4
    maxp = .99
    minp = .01
    minw = np.log(minp/(1-minp))


    def __init__(self,id,idx,oedges=-1,idx2oedges=-1):
        self.id = id
        self.idx = idx

        if oedges==-1:
            self.oedges = []
        else:
            self.oedges = oedges

        if idx2oedges==-1:
            self.idx2oedges = {}
        else:
            self.idx2oedges = idx2oedges


    def addNeighbor(self, neighNode):
        nIdx = neighNode.idx
        if (nIdx not in self.idx2oedges):
            oedge = OEdge(nIdx)
            self.oedges.append(oedge)
            self.idx2oedges[nIdx] = oedge

    def add_sim(self,neighNode,sim,feat_idx,order):
        nIdx = neighNode.idx
        oedge = self.idx2oedges[nIdx]
        oedge.add_sim(sim,feat_idx,order)


    def getSubset(self,idxes,idx2ArrIdx):
        id = self.id
        idx = idx2ArrIdx[self.idx]
        oedges = []
        idx2oedges = {}
        for nidx in idxes:
            arrIdx = idx2ArrIdx[nidx]
            if nidx not in self.idx2oedges:
                continue
            oedge = self.idx2oedges[nidx]
            oedge = oedge.copy(arrIdx)
            oedges.append(oedge)
            idx2oedges[arrIdx] = oedge
        node = Node(id,idx,oedges=oedges,idx2oedges=idx2oedges)
        return node


    def set_features(self,feats):
        self.feats = feats


    def setWPs(self,gr):
        if (len(self.oedges)==0):
            return
        for oedge in self.oedges:
            s = oedge.setPW(-1)
            gr.idxpair2score[(self.idx,oedge.idx)] = s

    def get_w(self,j):
        if j==self.idx:
            return 1
        elif (j not in self.idx2oedges):
            return 0
        else:
            return self.idx2oedges[j].w

    def getInterpolationW(self):
        numNeigh = len(self.oedges);
        halfIdx = np.int(numNeigh * .9)
        val2 = self.oedges[halfIdx].sims[2]+Node.eps/2
        val2 = min(val2,1)
        val3 = self.oedges[0].sims[2]+Node.eps
        val3 = min(val3,1)
        x = [0,val2,val3]
        y = [Node.minp,.5,Node.maxp]
        f = interpolate.interp1d(x, y,kind='quadratic')
        return f

    #NotUsed
    def set_label(self,l):
        self.l = l

    def __str__(self):
        ret = ""
        ret += "predicate:"+self.id +"\n\n"
        for oedge in self.oedges:
            ret += str(oedge) + "\n"
        ret += "\n"
        return ret

#outgoing edge
class OEdge:
    #We will have a list of similarities, but only one p and w

    def __init__(self,idx,sims=None,orders=None,p=-1,w=-1):
        self.idx = idx
        if sims is None:
            self.sims = np.zeros(shape=(Graph.num_feats//2))  # why?  # why?
            self.orders = np.zeros(shape=(Graph.num_feats//2))
            #To be set in setWPs
            self.p = -1
            self.w = -1
        else:
            self.sims = sims
            self.orders = orders
            self.p = p
            self.w = w

    def add_sim(self,sim, idx,order):
        if ")" in sim or "_" in sim:
            return
        try:
            self.sims[idx] = np.float(sim)
            self.orders[idx] = 1.0/order
            if idx==0:
                Graph.num_edges += 1
                if self.sims[0]>Graph.threshold:
                    Graph.num_edges_threshold += 1
        except ValueError:
            if debug:
                print ("exception for: ", sim)
            self.sims[idx] = 0


    def setPW(self,p):
        self.w = self.sims[Graph.featIdx]
        return self.w


    def __str__(self):
        ret = " sim: " + str(self.sims)+ " p: " + str(self.p) +" w: " + str(self.w)
        return ret

    def copy(self,idx):
        return OEdge(idx,self.sims,self.orders,self.p,self.w)
