travis_template = '''
language: python
sudo: false

services:
  - mongodb

##### start programmatically generated python section #####
{python}
##### end programmatically generated python section #####

##### start programmatically generated env section #####
{env}
##### end programmatically generated env section #####

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
  - conda create -n testenv --yes pip nose python=$TRAVIS_PYTHON_VERSION pymongo six pyyaml numpy pandas scikit-image h5py matplotlib jsonschema coverage
  # Dependencies not in official conda have been uploaded to binstar orgs.
  - source activate testenv
  - conda install --yes -c soft-matter pims tifffile
  - conda install --yes -c nikea mongoengine
  - conda install --yes -c lightsource2 epics-base readline lmfit prettytable pcaspy
  - conda install --yes -c tacaswell cycler xraylib
  - 'pip install https://github.com/NSLS-II/channelarchiver/zipball/master#egg=channelarchiver'
  # scikit-xray
  - conda install --yes netcdf4
  - conda install --yes -c ericdill pyfai
  # dataportal
  - pip install humanize boltons
  # python 3 deps only
  - if [ $TRAVIS_PYTHON_VERSION == "3.4" ]; then\n
        conda install --yes -c lightsource2 super_state_machine;
    fi;
  # replay
  - if [ $TRAVIS_PYTHON_VERSION == "2.7" ]; then\n
        conda install --yes enaml;
   fi;
  ###### start programmatically generated repo clone/install ######
{clone}
  ###### stop programmatically generated repo clone/install ######
script:
  - echo "debug info"
  - conda list
  - pwd
  - python -c "import prettytable; prettytable.__file__"
  ##### start programmatically generated test running script #####
{script}
  ##### stop programmatically generated test running script #####
'''

python_versions = ['2.7', '3.4']

# for creating the environmental variable matrix
versioned_libraries = [
    ('bluesky', ['v0.1.0', 'master']),
    ('dataportal', ['v0.1.0', 'master']),
    ('filestore', ['v0.1.0', 'master']),
    ('metadatastore', ['v0.1.0', 'master']),
    ('suitcase', ['master']),
    ('replay', ['master']),
    ('skxray', ['master'])
]

# for git cloning
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
        repos = ' '.join(['%s={%s}' % (k.upper(), k) for k in sorted(mat.keys()) if k != 'python'])
        env.append(('  - %s' % repos).format(**mat))

    env = '\n'.join(env)
    env = 'env:\n' + env
    script_template = (
        '  - cd %s;\n'
        '  - python run_tests.py;\n'
        '  - cd ..;')
    script = [script_template % lib for lib in sorted(repo_mapping.keys())
              if lib not in ['python', 'bluesky', 'replay']]
    script.append(
        '  - if [ $TRAVIS_PYTHON_VERSION == "3.4" ]; then\n'
        '        cd bluesky;\n'
        '        python run_tests.py;\n'
        '        cd ..;\n'
        '    fi;'
    )
    script.append(
        '  - if [ $TRAVIS_PYTHON_VERSION == "2.7" ]; then\n'
        '        cd replay;\n'
        '        python run_tests.py;\n'
        '        cd ..;\n'
        '    fi;'
    )
    script = '\n'.join(script)
    clone_template = (
        '  - git clone {url}\n'
        '  - cd {repo_name}\n'
        '  - git checkout ${version}\n'
        '  - python setup.py develop\n'
        '  - cd ..')
    clone = [(clone_template).format(repo_name=repo_name, url=url,
                                     version=repo_name.upper())
              for repo_name, url in sorted(repo_mapping.items(), key=lambda x: x[0])
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
