travis_template = '''
language: python
sudo: false

services:
  - mongodb

{python}

{env}

before_install:
  - wget http://repo.continuum.io/miniconda/Miniconda3-3.5.5-Linux-x86_64.sh -O miniconda.sh
  - chmod +x miniconda.sh
  - ./miniconda.sh -b -p /home/travis/mc
  - export PATH=/home/travis/mc/bin:$PATH
  # next 3 lines are needed to spawn a GUI
  - "export DISPLAY=:99.0"
  - "sh -e /etc/init.d/xvfb start"
  - "/sbin/start-stop-daemon --start --quiet --pidfile /tmp/custom_xvfb_99.pid --make-pidfile --background --exec /usr/bin/Xvfb -- :99 -ac -screen 1920x1080x32"
  # Set up config for MDS
  - export MDS_HOST=localhost
  - export MDS_DATABASE=test
  - export MDS_TIMEZONE=US/Eastern
  - mkdir -p /home/travis/.config/metadatastore
  - 'echo ''port: 27017'' > /home/travis/.config/metadatastore/connection.yml'
  # Set up config for FS
  - export FS_HOST=localhost
  - export FS_DATABASE=test
  - mkdir -p /home/travis/.config/filestore
  - 'echo ''port: 27017'' > /home/travis/.config/filestore/connection.yml'

install:
  - export GIT_FULL_HASH=`git rev-parse HEAD`
  - conda update conda --yes
  - conda create -n testenv --yes pip nose python=$TRAVIS_PYTHON_VERSION pymongo six pyyaml numpy pandas scikit-image h5py matplotlib coverage jsonschema
  # Dependencies not in official conda have been uploaded to binstar orgs.
  - conda install -n testenv --yes -c soft-matter pims tifffile
  - conda install -n testenv --yes -c nikea mongoengine
  - source activate testenv
  - 'pip install coveralls'
  - pip install codecov
  - 'pip install prettytable'
  - 'pip install humanize'
  - 'pip install boltons'
{clone}
  - 'pip install https://github.com/NSLS-II/channelarchiver/zipball/master#egg=channelarchiver'
  - python setup.py install

script:
{script}

after_success:
  coveralls
  codecov
'''
python_versions = ['2.7', '3.4']

versioned_libraries = [
    ('bluesky', ['v0.1.0', 'master']),
    ('dataportal', ['v0.1.0', 'master']),
    ('filestore', ['v0.1.0', 'master']),
    ('metadatastore', ['v0.1.0', 'master']),
    ('suitcase', ['master']),
    ('replay', ['master']),
    ('skxray', ['master'])
]

repo_mapping = {'bluesky': 'https://github.com/NSLS-II/bluesky',
                'dataportal': 'https://github.com/NSLS-II/dataportal',
                'filestore': 'https://github.com/NSLS-II/filestore',
                'metadatastore': 'https://github.com/NSLS-II/metadatastore',
                'suitcase': 'https://github.com/NSLS-II/suitcase',
                'replay': 'https://github.com/NSLS-II/replay',
                'scikit-xray': 'https://github.com/scikit-xray/scikit-xray'}

def nest_all_the_loops(iterable, matrix=None, matrices=None):
    if matrix is None:
        matrix = {}
    if matrices is None:
        matrices = []
    local_iterable = iterable.copy()
    try:
        lib, versions = local_iterable.pop(0)
    except IndexError:
        matrices.append(matrix.copy())
        return
    for version in versions:
        matrix[lib] = version
        nest_all_the_loops(local_iterable, matrix, matrices)
    return matrices

def generate():
    python = ['  - %s' % pyver for pyver in python_versions]
    python = '\n'.join(python)
    python = 'python:\n' + python
    envs = nest_all_the_loops(versioned_libraries.copy())
    env = []
    for mat in envs:
        repos = ' '.join(['%s={%s}' % (k.upper(), k) for k, v in mat.items() if k != 'python'])
        env.append(('  - %s' % repos).format(**mat))

    env = '\n'.join(env)
    env = 'env:\n' + env
    script = ['  - python %s/run_tests.py' % lib[0] for
              lib in versioned_libraries if lib[0] not in ['python', 'skxray']]
    script.append('  - python scikit-xray/run_tests.py')
    script = '\n'.join(script)
    clone_template = (
        '  - git clone {url}\n'
        '  - cd {repo_name}\n'
        '  - git checkout ${version}\n'
        '  - python setup.py develop\n'
        '  - cd ..')
    clone = [(clone_template).format(repo_name=repo_name, url=url,
                                     version=repo_name.upper())
              for repo_name, url in repo_mapping.items()
              if repo_name not in ['python', 'scikit-xray']]
    clone.append(clone_template.format(repo_name='scikit-xray',
                                       url=repo_mapping['scikit-xray'],
                                       version='SKXRAY'))
    clone = '\n'.join(clone)
    yml_file = travis_template.format(env=env, script=script,
                                      clone=clone, python=python)
    with open('.travis.yml', 'w') as f:
        f.write(yml_file)

# might be able to use https://github.com/bjfish/travis-matrix-badges as a
# launching point to create a cool matrix badge for this repo


if __name__ == "__main__":
    generate()
