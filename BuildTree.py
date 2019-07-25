import sys


test_list = [4, 2, 6, 3, 7, 5, 1]
probability = [0.1856, 0.0284, 0.1572, 0.1572, 0.1572, 0.1572, 0.1572]



def insert_time_and_tree_list(lists):
    times = [[None] * len(lists) for i in range(len(lists))]
    trees = [[None] * len(lists) for i in range(len(lists))]
    for i in range(len(lists)):
        times[i][i] = lists[i]
        trees[i][i] = [i]
    return times, trees


def calculate_probability(begin, index, end):
    temp_left_probability = 0
    temp_right_probability = 0
    for index in range(begin, index + 1):
        temp_left_probability += probability[index]
    for index in range(index + 1, end + 1):
        temp_right_probability += probability[index]
    temp_probability = temp_left_probability + temp_right_probability
    return temp_left_probability / temp_probability, temp_right_probability / temp_probability


def build_tree(begin, end):
    # print("begin: "+str(begin)+";end: "+str(end))
    if begin > end or end < 0:
        return 0, None
    else:
        tree_time = time_list[begin][end]
        # print("time:"+str(tree_time))
        tree = tree_list[begin][end]
    if tree_time == None:
        tree = []
        tree_time = sys.maxsize
        for index in range(begin, end + 1):
            temp_left_subtree_time, temp_left_subtree = build_tree(begin, index - 1)
            # print("left: "+str(temp_left_subtree_time)+"; "+str(temp_left_subtree))
            temp_right_subtree_time, temp_right_subtree = build_tree(index + 1, end)
            # print("right: "+str(temp_right_subtree_time)+"; "+str(temp_right_subtree))
            left_subtree_probability, right_subtree_probability = calculate_probability(begin, index, end + 1)
            # print left_subtree_probability+ right_subtree_probability
            temp_time = time_list[index][index] + left_subtree_probability * float(
                temp_left_subtree_time) + right_subtree_probability * float(temp_right_subtree_time)
            if temp_time < tree_time:
                tree_time = temp_time
                temp_tree = []
                # print(str(temp_left_subtree)+" + "+str(index)+" + "+str(temp_right_subtree))
                if temp_left_subtree != None:
                    temp_tree.append(temp_left_subtree)
                temp_tree.append(index)
                if temp_right_subtree != None:
                    temp_tree.append(temp_right_subtree)
                tree = temp_tree
        time_list[begin][end] = tree_time
        tree_list[begin][end] = tree
    return tree_time, tree


time_list, tree_list = insert_time_and_tree_list(test_list)
# print(time_list)
final_tree_time, final_tree = build_tree(0, len(time_list) - 1)
# print(time_list)
# print(tree_list)
print(final_tree_time)
print(final_tree)