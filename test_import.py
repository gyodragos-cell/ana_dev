import sys
import os
print('cwd:', os.getcwd())
print('sys.path[0:5]:', sys.path[0:5])

try:
    from ana.config.loader import ConfigLoader
    print('SUCCESS: imported ConfigLoader')
except Exception as e:
    import traceback
    print('FAILED to import ConfigLoader')
    traceback.print_exc()
