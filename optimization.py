from numpy.random import randint
from numpy.random import rand
from random import shuffle
from copy import deepcopy


class Optimization:
    """
    Genetic Algorithm Optimization
    Gene as a dictionary with id and array of points
    Closed segment has the same first point and last point
    Crossover operator exchanges two set of segments in two solutions then applies mapping sections
    Mutation operator rotate the closed segment or reverse the disclosed segment
    Cost are the total distance between the last target and first target of two neighboring segments
    """
    def __init__(self, origin, power=2, n_iter=200, n_pop=200, r_cross=.9, r_mut=.5, n_cross=1):
        """
        Initialize the optimizer

        :param origin: list, array of segments as list [points]
        :param power: scalar value, degree for cost calculation
        :param n_iter: integer, number of iterations
        :param n_pop: integer, number of population
        :param r_cross: scalar value, rate of crossover
        :param r_mut: scalar value, rate of mutation
        :param n_cross: scalar value, number of crossing chromosome
        """
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
        """
        Return cost of each solution
        First movement from (0, 0) origin to the first target included
        Aggregate the distance between the last target of previous segment and first target of the next one

        :param path: list, array of segments as dict {'points', 'id'}
        :return h: scalar value, sum of cost of each segment powered by degree
        :return total_cost: scalar value, sum of cost of each segment as original traveling distance
        """
        total_cost = (path[0]['points'][0][0] ** 2 + path[0]['points'][0][1] ** 2) ** 0.5
        h = total_cost ** self.power
        for idx in range(len(path) - 1):
            end = path[idx]['points'][-1]
            start = path[idx + 1]['points'][0]
            cost = ((start[0] - end[0]) ** 2 + (start[1] - end[1]) ** 2) ** 0.5
            h += cost ** self.power
            total_cost += cost
        return h, total_cost

    def selection(self, scores):
        """
        Select two random solution and return the better one

        :param scores: list, array of cost of each solution
        :return: list, the winning solution as dict {'points', 'id'}
        """
        # first random selection
        selection_ix = randint(self.n_pop)
        for ix in randint(0, self.n_pop, 2):
            # check if better (e.g. perform a tournament)
            if scores[ix][0] < scores[selection_ix][0]:
                selection_ix = ix
        return self.pop[selection_ix]

    def crossover(self, p1, p2):
        """
        Crossover operator
        Exchange two parts in solutions and use mapping sections to resolve conflicts

        :param p1: list, the first selected solution as dict {'points', 'id'}
        :param p2: list, the second selected solution as dict {'points', 'id'}
        """
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

            # Mapping relationship
            # {id, [id]}
            m = dict()
            for i in range(num):
                if (id1 := segs1[i]['id']) != (id2 := segs2[i]['id']):
                    m[id1] = list([id2]) if id1 not in m.keys() else m[id1] + [id2] if id2 not in m[id1] else m[id1]
                    m[id2] = list([id1]) if id2 not in m.keys() else m[id2] + [id1] if id1 not in m[id2] else m[id2]
            # TODO: find a way to make this mapping selection more efficient
            for _ in range(num ** 2):
                for k1, v in m.items():
                    for k2 in v:
                        v = list(set([v2 for v2 in m[k2] if v2 != k1]) - set(v)) + v
                        m[k1] = v

            # Resolve conflicts in each prototype
            for idx, seg in enumerate(proto1):
                if pt <= idx < pt + num:
                    continue
                elif seg['id'] in m.keys():
                    for index in m[seg['id']]:
                        # search for
                        if index not in temp2.keys():
                            proto1[idx] = {'id': index, 'points': temp1[index]}

            for idx, seg in enumerate(proto2):
                if pt <= idx < pt + num:
                    continue
                elif seg['id'] in m.keys():
                    for index in m[seg['id']]:
                        if index not in temp1.keys():
                            proto2[idx] = {'id': index, 'points': temp2[index]}

            c1, c2 = proto1[:], proto2[:]
        return [c1, c2]

    def mutation(self, path):
        """
        Mutation operator
        Randomly rotate the closed segment or reverse direction of disclose segment

        :param path: list, solution as dict {'points', 'id'}
        """
        for i in range(len(path)):
            # check for a mutation
            if rand() < self.r_mut:
                seg = path[i]['points'][:]
                if seg[-1] != seg[0]:
                    # reverse vector
                    seg = seg[::-1]
                else:
                    # translate by one
                    temp = seg[:-1]
                    idx = randint(len(temp))
                    seg = temp[idx:] + temp[:idx]
                    seg = seg + [seg[0]]
                path[i]['points'] = seg

    # genetic algorithm
    def run(self):
        """
        Execute Genetic Algorithm
        :return: the best generated outcome and its score
        """
        # initial population of random bitstring
        # define the total iterations
        self.pop.append(self.origin)
        for _ in range(self.n_pop - 1):
            new_parent = deepcopy(self.origin)
            shuffle(new_parent)
            self.mutation(new_parent)
            self.pop.append(new_parent)

        # keep track of best solution
        best, (best_eval, min_cost) = deepcopy(self.origin), self.calculate_cost(self.origin)
        print("origin:", best_eval, min_cost)
        print("pop:", self.n_pop)

        # enumerate generations
        for gen in range(self.n_iter):
            if gen % 50 == 0:
                print("Iteration", gen + 1)

            # evaluate all candidates in the population
            scores = [self.calculate_cost(c) for c in self.pop]
            # check for new best solution
            for i in range(self.n_pop):
                if scores[i][0] < best_eval:
                    best, best_eval, min_cost = deepcopy(self.pop[i]), scores[i][0], scores[i][1]
                    print(">%d, new best %.3f" % (gen + 1, scores[i][0]))

            # select parents
            selected = [self.selection(scores) for _ in range(self.n_pop)]
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

