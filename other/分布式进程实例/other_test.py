# encoding:utf-8
# from __future__ import absolute_import, division, print_function, unicode_literals
import sys
reload(sys)
sys.setdefaultencoding("utf-8")


##a = ['a', 'b', 'c', 'd']
##b = ''.join(reversed(a))
##print b

##def a():
##    return 1
##print a

'''文件操作Start'''
#from random import randint
#with open('1.txt', 'w') as text:
#    for x in [x % 10 for x in range(100)]:
#        line = hex(randint(0, 15 ** 7))
#        while len(line) < 10:
#            line += str(x)
#        text.write(line + '\n')
'''文件操作End'''

# def arg(*args):
#     print args
# arg(1, 2, 3)

# print '收到'

# import time
# time_struct = time.localtime(time.time())
# print time.strftime("%Y-%m-%d %H:%M:%S", time_struct)

# import re, json, os
# string = 'AssertionError'
# print json.dumps([x for x in os.__all__], indent=4)

# print [x for x in dir(Exception)]
# print dir(Exception.args)

import os, json, shutil, time
# print json.dumps(dict(os.environ), indent=4)
# print json.dumps(dir(shutil.os), indent=4)

# print sys.argv

# print os.listdir('.')
# print [x for x in os.listdir('.') if os.path.isfile(x) and os.path.splitext(x)[1] == '.py']

def search(s, path='.'):
    res = []
    res += [os.path.join(path, x) for x in os.listdir(path) if os.path.isfile(os.path.join(path, x)) and s in x]
    dirs = [x for x in os.listdir(path) if os.path.isdir(os.path.join(path, x))]
    for d in dirs:
        res += search(s, os.path.join(path, d))
    return res

# print search('.txt')


# from multiprocessing import Process

# def run_proc(name):
#     print 'Run child process %s (%s)...' % (name, os.getpid())

# if __name__ == '__main__':
#     print 'Parent process %s.' % os.getpid()
#     p = Process(target=run_proc, args=('test',))
#     print 'Process will start.'
#     p.start()
#     p.join()
#     print 'Process end.'



from multiprocessing import Pool
import os, time, random

def long_time_task(name):
    print 'Run task %s (%s)...' % (name, os.getpid())
    start = time.time()
    time.sleep(random.random() * 3)
    end = time.time()
    print 'Task %s runs %0.2f seconds.' % (name, (end - start))

if __name__=='__main__':
    print 'Parent process %s.' % os.getpid()
    start = time.clock()
    p = Pool()
    for i in range(5):
        p.apply_async(long_time_task, args=(i,))
    print 'Waiting for all subprocesses done...'
    p.close()
    p.join()
    print 'All subprocesses done.'
    print 'run time : %0.2f' % (time.clock() - start)
    os.system('pause')

