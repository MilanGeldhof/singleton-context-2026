import itertools
import random
import numpy as np

# Define the levels
distractors = [0, 1, 2, 3, 4, 5]  # 6 levels
colors = [0, 1]                # 2 levels
responses = [0, 1]             # 2 levels
n_subj = 150

# Create the Full Factorial base 
base_conditions = list(itertools.product(distractors, colors, responses))
reps = np.ceil(n_subj / len(base_conditions))  # Calculate how many times to repeat the base conditions

all_dist = ""
all_color = ""
all_resp = ""

for _ in range(int(reps)):
    # Randomize per rep
    random.shuffle(base_conditions)
    for dist, color, resp in base_conditions:
        all_dist += str(dist)
        all_color += str(color)
        all_resp += str(resp)

# 4. Print the final strings
print(f'factorial_dist = "{all_dist}"')
print(f'factorial_colororder = "{all_color}"')
print(f'factorial_resp = "{all_resp}"')
print(f'Total length of each string: {len(all_dist)}')