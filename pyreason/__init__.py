from pyreason.pyreason import *
import os
print('Imported PyReason for the first time. Initializing ... this will take a minute')
package_path = os.path.abspath(pyreason.__file__)
print(package_path)
cache_path = os.path.join(package_path, 'cache')
print(cache_path)
print(os.system('ls -a'))
print(os.path.exists(cache_path))
# print(os.path.exists('./docs'))