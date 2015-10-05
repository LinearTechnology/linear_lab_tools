import test_ltc2000 as t1
import test_ltc2123 as t2
import test_mini_module as t3
import test_ltc2261 as t4
import test_ltc2268 as t5

print 'High Speed tests'

print 'Test battery 1'
t1.test()
print 'Test battery 2'
t2.test()
print 'Test battery 3'
t3.test()

print 'DC890 tests'
print 'Test battery 4'
t4.test()

print 'DC1371 tests'
print 'Test battery 5'
t5.test()
