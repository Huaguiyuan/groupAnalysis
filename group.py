import numpy as np
from numpy import linalg as LA

def p2r(radii, angles):
    return radii * np.exp(1j*angles)

def r2p(x):
    return abs(x), np.angle(x)

class element():
    def init(self, a):
        a = np.array(a, dtype='float')
        self.D = a[0:3, 0:3]
        self.t = a[:, 3]

    def trans_init(self, a):
        self.D = np.eye(3)
        self.t = np.array(a, dtype='float')

    def element_product(self, a, b):
        self.D = np.dot(a.D, b.D)
        self.t = np.dot(a.D, b.t) + a.t

    def zip_element(self):
        a = np.concatenate((self.D, np.array([self.t]).T), axis=1)
        return a

    def xyz(self):
        x = str(np.sum(self.D[:, 0])) + 'x' + '+' + str(self.t[0])
        y = str(np.sum(self.D[:, 1])) + 'y' + '+' + str(self.t[1])
        z = str(np.sum(self.D[:, 2])) + 'z' + '+' + str(self.t[2])
        return x + ',' + y + ',' + z


class group():
    def init(self, g, boundary=[1, 1, 1]):
        self.g = g
        self.boundary = boundary
        self.order = len(self.g)
        self.multi_table()

    def check_equality(self, a, b):
        equal = False
        if np.allclose(a.D, b.D):
            t = a.t - b.t
            if np.mod(t[0], self.boundary[0]) == 0 and np.mod(t[1], self.boundary[1]) == 0 and \
                            np.mod(t[2],self.boundary[2]) == 0:
                equal = True
        return equal

    def multi_table(self):
        mtable = []
        for i in range(self.order):
            line = []
            for j in range(self.order):
                tmp = element()
                tmp.element_product(self.g[i], self.g[j])
                for k in range(self.order):
                    if self.check_equality(tmp, self.g[k]) == True:
                        line.append(k)

            mtable.append(line)

        self.mtable = np.array(mtable, dtype='int')
        return mtable

    def inverse_elelment(self, a):  # a is the int number of element
        b = list(self.mtable[a]).index(0)
        return b

    def find_class(self):

        classes = [[0]]
        cnt = 1
        i = 1
        while i < self.order and cnt < self.order:
            if i not in [item for sublist in classes for item in sublist]:
                c = [i]
                cnt += 1
                j = 1
                while j < self.order and cnt < self.order:
                    tmp = self.mtable[self.inverse_elelment(j), self.mtable[i, j]]
                    if tmp not in c:
                        c.append(tmp)
                        cnt += 1
                    j += 1
                classes.append(c)
            i += 1
        self.cl = classes
        return classes

    def group_product(self, g1, g2, boundary=[1, 2, 2]):

        glist = []
        for i in range(g1.order):
            for j in range(g2.order):
                tmp = element()
                tmp.element_product(g1.g[i], g2.g[j])
                glist.append(tmp)

        self.init(glist, boundary)
        return self

    def subset_product(self, s1, s2):
        elist = []
        for i in range(len(s1)):
            for j in range(len(s2)):
                tmp = element()
                tmp.element_product(self.g[s1[i]], self.g[s2[j]])
                for k in range(self.order):
                    if self.check_equality(tmp, self.g[k]):
                        elist.append(k)
                        break
        return elist

    def check_class(self, element):
        for i in range(len(self.cl)):
            for j in range(len(self.cl[i])):
                if self.check_equality(element, self.g[self.cl[i][j]]):
                    return i

    def check_class_index(self, element):
        # this differs from above in that the element is index instead of class element
        for i in self.cl:
            for j in i:
                if element == j:
                    return i

    def class_mul_constants(self):
        cl = self.cl
        nc = len(cl)
        H = np.zeros((nc, nc, nc))

        for i in range(nc):
            for j in range(nc):
                elist = self.subset_product(cl[i], cl[j])
                for k in range(nc):
                    H[i, j, k] = elist.count(cl[k][0])
        self.cl_mat = H
        return H

    def burnside_class_table(self):

        def check_same_vec(vec):
            same_vec_index = []
            for i in range(len(vec)):
                x = np.nonzero(vec[i])
                flag = x[0][0]
                for j in range(i + 1, len(vec)):
                    if not np.allclose(vec[j][flag], 0):
                        if np.allclose(vec[i], (vec[i][flag] / vec[j][flag]) * vec[j]):
                            same_vec_index.append(j)

            same_vec_index = list(set(same_vec_index))
            same_vec_index = sorted(same_vec_index, reverse=True)

            for i in same_vec_index:
                del vec[i]
            return vec

        # def check_same_eigenval(w):

        def find_nondegenerate_vec(vec, H, nc):
            for i in range(len(H)):
                w, v = LA.eig(H[i])

                w = np.array(list(w))
                index = []
                # fingding non-equivalent eigenvalues
                for k in range(len(w)):
                    cnt = 0
                    for j in range(len(w)):
                        if abs(w[j] - w[k]) < 1e-3:
                            cnt += 1
                    if cnt == 1:
                        index.append(k)
                # end finding non-equivalent eigenvalues, and its index stored in k

                # start picking out those non-degenerate vecs
                for j in index:
                    vec.append(v[:, j])

            if len(vec) > 1:
                vec = check_same_vec(vec)
            if len(vec) != nc and len(H) > 1:
                h = []
                for i in range(len(H) - 1):
                    h.append(H[i] + H[i + 1])

                return find_nondegenerate_vec(vec, h, nc)
            elif len(vec) == nc:
                return vec
            else:
                print("ERROR IN RECURSION (burnside method)")

        def normalize_vec(vec):

            for i in range(len(vec)):
                vec[i] = vec[i] * (1 / vec[i][0])
            vec = np.array(vec).T
            return vec

        def simul_diag_cl_mat(H, vec):
            nc = len(H)
            cl_table = np.zeros((nc, nc), dtype='complex')
            for i in range(nc):
                diag = np.dot(LA.inv(vec), np.dot(H[i], vec))
                cl_table[:, i] = np.diag(diag)
            return cl_table

        def get_irrep_dim(cl_table):
            nc = len(cl_table)
            d = []
            for i in range(nc):
                tmp = 0
                for j in range(nc):
                    tmp += cl_table[i, j] * np.conj(cl_table[i, j]) / len(self.cl[j])
                d_square = self.order / tmp
                d.append(np.sqrt(d_square))
            return d

        def get_character_table(cl_table, dim):
            nc = len(cl_table)
            character_table = np.zeros((nc, nc), dtype='complex')
            for i in range(nc):
                for j in range(nc):
                    character_table[i, j] = dim[i] / len(cl[j]) * cl_table[i, j]
            character_table = character_table[np.argsort(character_table[:, 0])]
            return character_table

        cl = self.cl
        order = self.order
        nc = len(cl)
        vec = []
        H = [i for i in self.cl_mat]
        vec = find_nondegenerate_vec(vec, H, nc)
        vec = normalize_vec(vec)
        cl_table = simul_diag_cl_mat(H, vec)
        dim = get_irrep_dim(cl_table)
        character_table = get_character_table(cl_table, dim)
        return character_table

    def regular_rep(self, element):  # element is the number of the element in group
        reg_rep = np.zeros((self.order, self.order))
        for i in range(self.order):
            reg_rep[self.mtable[element, i], i] = 1
        return reg_rep

    def element_order(self, element):
        i = 0
        power = 0
        element_order = None
        while i < self.order:
            i += 1
            power = self.mtable[power, element]
            if power == 0:
                element_order = i
                break
        if element_order is None:
            print("ERROR:, can not find element order")
            return
        return element_order

    def reg_eigencolumns(self, reg_rep):
        x = range(self.order)
        y = np.dot(reg_rep, x)
        y = np.array(y, dtype='int')
        # print("after rearrangement", y)
        permutation_cycle = []
        # determine cycle and cycle length
        i = 0
        while i < self.order:
            if i not in [item for sublist in permutation_cycle for item in sublist]:
                j = i
                cnt = 1
                # this count num has no use actually
                l = [i]
                while y[j] != x[i] and cnt <= self.order:
                    cnt += 1
                    j = x[y[j]]
                    l.append(j)
                permutation_cycle.append(l)
            i += 1
        # print("permutation cycle: ", permutation_cycle)

        # permutation cycle determined, the next is to determine the eigenvector
        eigencolumns = np.zeros((self.order, self.order), dtype='complex')
        cnt = 0
        eigenvalues = np.zeros(self.order, dtype='complex')
        for i in range(len(permutation_cycle)):
            length = len(permutation_cycle[i])
            tmp = permutation_cycle[i]
            for j in range(length):
                powers = p2r(1, 2 * np.pi / length * j)

                eigencolumns[tmp[0], cnt] = 1

                for k in range(length - 1):
                    eigencolumns[tmp[k + 1], cnt] = pow(powers, (k + 1))
                eigenvalues[cnt] = eigencolumns[permutation_cycle[i][1], cnt]
                # print(eigenvalues[cnt])
                cnt += 1
        # print(eigencolumns)
        return eigenvalues, eigencolumns

    def projection_operator(self, irrep_index, character_table, reg_rep):
        # irrep_index is the index of the irrep in character table
        dim = character_table[irrep_index, 0]
        projection_operator = np.zeros((self.order, self.order), dtype='complex')
        for i in range(len(self.cl)):
            for j in range(len(self.cl[i])):
                projection_operator += np.conj(character_table[irrep_index, i]) * reg_rep[self.cl[i][j]]
        projection_operator = dim / self.order * projection_operator
        return projection_operator

    def vec_same(self, vec1, vec2):
        flag = None
        for i in range(len(vec1)):
            if not np.allclose(vec1[i], 0):
                flag = i
        if not np.allclose(vec2[flag], 0):
            if np.allclose(vec1, (vec1[flag] / vec2[flag]) * vec2):
                return True
        return False

    def subspace_eigenvector(self, irrep_index, character_table, reg_rep):
        projection_operator = self.projection_operator(irrep_index, character_table, reg_rep)
        dim = int(character_table[irrep_index, 0])

        print("group: projection operator", projection_operator)
        # for we always choose reg_rep[1] as a start point

        for i in range(1, self.order):
            eigenvalues, eigencolumns = self.reg_eigencolumns(reg_rep[i])
            projected_vector = np.dot(projection_operator, eigencolumns)

            # find those eigencolumns that does not change under projection,
            # save them and their corresponding eigenvalues of reg_rep[i]
            vec = []
            vec_val = []
            for j in range(self.order):
                if self.vec_same(projected_vector[:, j], eigencolumns[:, j]):
                    w1 = projected_vector[:, j]
                    vec.append(w1)
                    vec_val.append(eigenvalues[j])

            # check the projected eigencolumns are not degenerate,
            # if degenerate, start from a different reg_rep[i]
            # the standard is whether same eigenvalues appeared more than dim times
            # first count the occurences of eigenvals of those eigencolumns that survived the projection
            if len(vec) != 0:
                same_val = []
                count = []

                for k in range(len(vec_val)):
                    cnt = 0
                    tmp = []
                    for j in range(k, len(vec_val)):
                        if abs(vec_val[j] - vec_val[k]) < 1e-5 and \
                                (j not in [item for sublist in same_val for item in sublist]):
                            cnt += 1
                            tmp.append(j)
                    count.append(cnt)
                    same_val.append(tmp)

                if all(j <= dim for j in count):
                    if dim == 1:
                        return vec[0]
                    elif len(vec) != 0:
                        sub_vec = [vec[0]]
                        for j in range(1, self.order):
                            new_vec = np.dot(reg_rep[j], vec[0])

                            if np.allclose(np.multiply(new_vec, vec[0]), 0):
                                sub_vec.append(new_vec)
                                if len(sub_vec) == dim:
                                    for k in range(len(sub_vec)):
                                        sub_vec[k] = sub_vec[k] / LA.norm(sub_vec[k])

                                    return sub_vec

    def irrep(self, irrep_index):
        # note that the dim of this irrep_index should be >1
        # if the dim ==1, return character table
        ctable = self.burnside_class_table()
        if np.allclose(ctable[irrep_index, 0], 1):
            return ctable[irrep_index]

        reg_rep = np.zeros((self.order, self.order, self.order), dtype='int')
        for i in range(self.order):
            reg_rep[i, :, :] = self.regular_rep(i)
        subspace_vec = self.subspace_eigenvector(irrep_index, ctable, reg_rep)
        vec = np.array(subspace_vec, dtype='complex').T
        print("character table", ctable)

        print("vec", vec)
        irrep = []
        for i in range(self.order):
            tmp = np.dot(np.conj(vec.T), np.dot(reg_rep[i], vec))
            irrep.append(tmp)
        return irrep












'''

# @U
g = [
    [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]], [[-1, 0, 0, 0], [0, -1, 0, 0], [0, 0, 1, 0.5]],
    [[-1, 0, 0, 0], [0, 1, 0, 0.5], [0, 0, -1, 0.5]], [[1, 0, 0, 0], [0, -1, 0, 0.5], [0, 0, -1, 0]],
    [[-1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0]], [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0.5]],
    [[1, 0, 0, 0], [0, -1, 0, 0.5], [0, 0, 1, 0.5]], [[-1, 0, 0, 0], [0, 1, 0, 0.5], [0, 0, 1, 0]]
]

# @UX 1,2,7,8
# @ZU 1,4,6,8


t = [[0, 0, 0], [0, 1, 0]]
gk = []

# x = [i for i in range(len(g))]
x = [0, 1, 6, 7]  # UX
# x = [0,2,5,7] #UZ

for i in x:
    tmp = element()
    tmp.init(g[i])
    gk.append(tmp)

tk = []
for i in t:
    tmp = element()
    tmp.trans_init(i)
    tk.append(tmp)

Gk = group()
Gk.init(gk)
Tk = group()
Tk.init(tk)
print(Gk.find_class())

G = group()
G.group_product(Gk, Tk, boundary=[1, 2, 1])
print("g1 element", G.g[1].zip_element())
print(G.order)
print(G.find_class())
print(len(G.find_class()))

H = G.class_mul_constants()
# print(H)

character_table = G.burnside_class_table()
np.set_printoptions(precision=3)
np.savetxt('ct', character_table, '%5.2f')

'''
