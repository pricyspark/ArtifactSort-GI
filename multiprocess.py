import numpy as np
from multiprocessing import Process, Queue
from fast_benchmark import test_coefs, eval_fun
import random

def worker(q, data):
    # Generate new data (a row of size 5)
    coefs = np.array((0, random.random(), random.random(), (random.random() - 0.5) / 500))
    coefs /= np.sum(np.abs(coefs))
    row = test_coefs(coefs, 200, eval_fun, 185, 50)
    # Send the new data to the queue
    q.put(row)

def aggregator(q, final_array, num_workers):
    count = 0
    while count < num_workers:
        new_row = q.get()
        final_array = np.vstack((final_array, new_row))
        count += 1
    # final_array now has all rows appended
    return final_array
    #print(final_array)

if __name__ == '__main__':
    try:
        results = np.load('multi.npy') 
        backup = np.load('backup.npy')
        if backup.size > results.size:
            results = backup
        del backup
    except:
        results = np.zeros((0, 5))
    q = Queue()
    # Start with an empty array with shape (0, 5)
    num_workers = 5
    while True:
        np.save('backup.npy', results)
        processes = []
        
        # Create worker processes with sample data
        for i in range(num_workers):
            data = [i, i+1, i+2, i+3, i+4]
            p = Process(target=worker, args=(q, data))
            processes.append(p)
            p.start()

        # Aggregator process collects data from the queue
        results = aggregator(q, results, num_workers)

        for p in processes:
            p.join()
        
        np.save('multi.npy', results)