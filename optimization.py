# genetic algorithm search of the one max optimization problem
from numpy.random import randint
from numpy.random import rand
from random import shuffle
from copy import deepcopy

class Optimization:
    def __init__(self, origin, power=2, n_iter=200, n_pop=200, r_cross=.9, r_mut=.5, n_cross=1):
        self.origin = [{'id': f'{i}', 'points': s} for i, s in enumerate(origin)]
        self.power = power
        self.pop = list()
        self.n_cross = n_cross
        self.n_iter = n_iter
        self.n_pop = n_pop + 1 if n_pop % 2 == 1 else n_pop
        self.r_cross = r_cross
        self.r_mut = r_mut

    # objective function
    def calculate_cost(self, path):
        total_cost = (path[0]['points'][0][0] ** 2 + path[0]['points'][0][1] ** 2) ** 0.5
        h = total_cost ** self.power
        for idx in range(len(path) - 1):
            end = path[idx]['points'][-1]
            start = path[idx + 1]['points'][0]
            cost = ((start[0] - end[0]) ** 2 + (start[1] - end[1]) ** 2) ** 0.5
            h += cost ** self.power
            total_cost += cost
        return h, total_cost

    # tournament selection
    def selection(self, scores, k=3):
        # first random selection
        selection_ix = randint(self.n_pop)
        for ix in randint(0, self.n_pop, 2):
            # check if better (e.g. perform a tournament)
            if scores[ix][0] < scores[selection_ix][0]:
                selection_ix = ix
        return self.pop[selection_ix]

    @staticmethod
    def is_same_vector(v1, v2):
        return (v1[0] == v2[0] and v1[1] == v2[1]) or (v1[0] == v2[1] and v1[1] == v2[0])

    # crossover two parents to create two children
    def crossover_1(self, p1, p2):
        # children are copies of parents by default
        c1, c2 = p1.copy(), p2.copy()
        # check for recombination
        if rand() < self.r_cross:
            # select crossover point that is not on the end of the string
            pt = randint(1, len(p1) - 3)
            # perform crossover
            seg1, seg2 = p1[pt:pt + 2], p2[pt:pt + 2]
            proto1 = p1[:pt] + seg2 + p1[pt + 2:]
            proto2 = p2[:pt] + seg1 + p2[pt + 2:]
            for idx, vect in enumerate(proto1):
                if pt <= idx <= pt + 1:
                    continue
                elif self.is_same_vector(vect, seg2[0]):
                    if self.is_same_vector(seg1[0], seg2[1]):
                        proto1[idx] = seg1[1]
                    else:
                        proto1[idx] = seg1[0]
                elif self.is_same_vector(vect, seg2[1]):
                    if self.is_same_vector(seg1[1], seg2[0]):
                        proto1[idx] = seg1[0]
                    else:
                        proto1[idx] = seg1[1]

            for idx, vect in enumerate(proto2):
                if pt <= idx <= pt + 1:
                    continue
                elif self.is_same_vector(vect, seg1[0]):
                    if self.is_same_vector(seg2[0], seg1[1]):
                        proto2[idx] = seg2[1]
                    else:
                        proto2[idx] = seg2[0]
                elif self.is_same_vector(vect, seg1[1]):
                    if self.is_same_vector(seg2[1], seg1[0]):
                        proto2[idx] = seg2[0]
                    else:
                        proto2[idx] = seg2[1]
            c1, c2 = proto1[:], proto2[:]
        return [c1, c2]

    @staticmethod
    def is_same_segment(s1, s2):
        if len(s1) != len(s2):
            return False

        for point1 in s1:
            found = False
            for point2 in s2:
                if point1 == point2:
                    found = True
                    break

            if not found:
                return False

        return True

    def crossover(self, p1, p2):
        # children are copies of parents by default
        c1, c2 = p1.copy(), p2.copy()
        num = min(self.n_cross, len(c1) - 1)
        # check for recombination
        if rand() < self.r_cross:
            # select crossover point that is not on the end of the string
            pt = randint(len(p1) - num + 1)
            # perform crossover
            # [{id, points}]
            segs1, segs2 = p1[pt:pt + num], p2[pt:pt + num]
            # {id: points}
            temp1 = {seg['id']: seg['points'] for seg in segs1}
            temp2 = {seg['id']: seg['points'] for seg in segs2}
            # [{id, points}]
            proto1 = p1[:pt] + segs2[:] + p1[pt + num:]
            proto2 = p2[:pt] + segs1[:] + p2[pt + num:]
            # print(pt ,'segs1', segs1)
            # print('temp2', temp2)
            # Mapping relationship
            # {id, [id]}
            m = dict()
            for i in range(num):
                if (id1 := segs1[i]['id']) != (id2 := segs2[i]['id']):
                    m[id1] = list([id2]) if id1 not in m.keys() else m[id1] + [id2] if id2 not in m[id1] else m[id1]
                    m[id2] = list([id1]) if id2 not in m.keys() else m[id2] + [id1] if id1 not in m[id2] else m[id2]
            for _ in range(num ** 2):
                for k1, v in m.items():
                    for k2 in v:
                        v = list(set([v2 for v2 in m[k2] if v2 != k1]) - set(v)) + v
                        m[k1] = v
            # print('mapping', m)

            for idx, seg in enumerate(proto1):
                if pt <= idx < pt + num:
                    continue
                else:
                    # in mapping
                    if seg['id'] in m.keys():
                        for index in m[seg['id']]:
                            # search for
                            if index not in temp2.keys():
                                proto1[idx] = {'id': index, 'points': temp1[index]}

            for idx, seg in enumerate(proto2):
                if pt <= idx < pt + num:
                    continue
                else:
                    if seg['id'] in m.keys():
                        for index in m[seg['id']]:
                            if index not in temp1.keys():
                                proto2[idx] = {'id': index, 'points': temp2[index]}

            c1, c2 = proto1[:], proto2[:]
            # print(f"end crossover {pt}→{pt+num-1}", '\np1', [p['id'] for p in p1], 'p2', [p['id'] for p in p2],
            #       '\nc1', [c['id'] for c in c1], 'c2', [c['id'] for c in c2])
        return [c1, c2]



    # mutation operator
    def mutation(self, path):
        # print("mutation")
        # print(path)
        for i in range(len(path)):
            # check for a mutation
            if rand() < self.r_mut:
                seg = path[i]['points'][:]
                # print("start mutation:", path[i], seg)
                if seg[-1] != seg[0]:
                    # reverse vector
                    seg = seg[::-1]
                else:
                    # translate by one
                    temp = seg[:-1]
                    idx = randint(len(temp))
                    seg = temp[idx:] + temp[:idx]
                    seg = seg + [seg[0]]
                # print("end mutation:", path[i], seg)
                if len(path[i]['points']) != len(seg):
                    exit()
                path[i]['points'] = seg
        # print(path)

    # genetic algorithm
    def run(self):
        # initial population of random bitstring
        # define the total iterations
        # print(sample)
        self.pop.append(self.origin)
        for _ in range(self.n_pop - 1):
            new_parent = deepcopy(self.origin)
            shuffle(new_parent)
            self.mutation(new_parent)
            self.pop.append(new_parent)
        # keep track of best solution
        best, (best_eval, min_cost) = deepcopy(self.origin), self.calculate_cost(self.origin)
        print("origin:", best_eval, min_cost)
        # print(self.origin)
        print("pop:", self.n_pop)
        # enumerate generations
        for gen in range(self.n_iter):
            # self.r_mut = gen / self.n_iter * 0.01
            if gen % 50 == 0:
                print("Iteration", gen + 1)
            # evaluate all candidates in the population
            scores = [self.calculate_cost(c) for c in self.pop]
            # check for new best solution
            for i in range(self.n_pop):
                if scores[i][0] < best_eval:
                    best, best_eval, min_cost = deepcopy(self.pop[i]), scores[i][0], scores[i][1]
                    # print(">%d, new best f(%s) = %.3f" % (gen, pop[i], scores[i]))
                    print(">%d, new best %.3f" % (gen + 1, scores[i][0]))
            # select parents
            selected = [self.selection(scores) for _ in range(self.n_pop)]
            # print("selected\n", selected)
            # create the next generation
            children = list()
            for i in range(0, self.n_pop, 2):
                # get selected parents in pairs
                p1, p2 = selected[i], selected[i + 1]
                # crossover and mutation
                for c in self.crossover(p1, p2):
                    # mutation
                    self.mutation(c)
                    # store for next generation
                    children.append(c)
            # replace population
            self.pop = children[:]
        # print(best)
        return [[seg['points'] for seg in best], min_cost]

