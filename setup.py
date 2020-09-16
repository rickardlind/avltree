from distutils.core import setup, Extension

setup(name='cavltree',
      version='1.0',
      ext_modules=[Extension('cavltree', ['cavltree.c'])],
      script_args=['build_ext'],
      options={'build_ext': {'build_temp': '.',
                             'build_lib': '.'}})
