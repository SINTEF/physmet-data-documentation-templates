
""" Program to create project folders / files for SEM data

    Examples of usage:

    > Warning:: replace the "python" command below by "python3" on Linux
    > and "py.exe" on Windows (or "py.exe -3.11" if you have mulitple Python
    > versions installed).

    - create a project folder (run the command and answer the questions):
      $ python physmet-folders.py init

    - another command to create a project folder:
      $ python physmet-folders.py add -p hello-world

    - set the default project to work with:
      $ python physmet-folders.py set-default -p hello-world

    - list the existing projects:
      $ python physmet-folders.py list

    - print the help:
      $ python physmet-folders.py --help

    - print the version of the program:
      $ python physmet-folders.py --version

    - add a measurement on a sample (enter sample identifier and date):
      $ python physmet-folders.py add -s SAMPLE_ID -d YYYY-MM-DD
"""

import os
import getpass
import platform
from pathlib import Path
from datetime import datetime
import json
from argparse import ArgumentParser, Namespace

# name of the folder in the AppData folder
# - on linux: ~/.physmet-folders/
# - on windows: ~/AppData/Local/physmet-folders/
__appname__ = 'physmet-folders'

# version of the app / program
__version__ = '2026-02-19'


def username():
    """ Returns the full name of the computer user """
    usr = ''
    if platform.system() == 'Windows':
        try:
            import ctypes
            GetUserNameEx = ctypes.windll.secur32.GetUserNameExW
            NameDisplay = 3
            size = ctypes.pointer(ctypes.c_ulong(0))
            GetUserNameEx(NameDisplay, None, size)
            nameBuffer = ctypes.create_unicode_buffer(size.contents.value)
            GetUserNameEx(NameDisplay, nameBuffer, size)
            usr = nameBuffer.value
        except Exception:
            usr = getpass.getuser()
    else:
        try:
            import pwd
            user_info = pwd.getpwuid(os.getuid())
            usr = user_info.pw_gecos
        except Exception:
            usr = getpass.getuser()
    return usr


def appdata() -> Path:
    """ Returns the path of the app data """
    path = Path.home() / f'.{__appname__}'
    if 'LOCALAPPDATA' in os.environ:
        path = Path(os.environ['LOCALAPPDATA']) / f'Programs/{__appname__}'
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_config(key=''):
    """ Read a config parameter from the app data file config.json """
    fil = appdata() / 'config.json'
    cfg = json.loads(fil.read_text()) if fil.exists() else {}
    return cfg.get(key, None) if key else cfg


def write_config(key, data):
    """ Write a config parameter to the app data file config.json """
    cfg = read_config()
    cfg[key] = data
    fil = appdata() / 'config.json'
    fil.write_text(json.dumps(cfg, default=str))


def find_project(name) -> Path:
    """ Find an existing project by name """
    path = None
    prj = read_config('projects')
    if prj:
        for item in prj:
            if item['name'] == name:
                path = Path(item['path'])
    if path:
        if not path.exists():
            msg = f'project path not found "{path}" (project="{name}").'
            raise FileNotFoundError(msg)
    else:
        raise KeyError(f'project "{name}" not found.')
    return path


def userinput(msg, default):
    """ Get an user input with default value """
    v = f' [{default}]' if default else ''
    val = input(f'{msg}{v}: ')
    return val if val else default


def mkdir(path: Path):
    print('create directory:')
    print(path)
    path.mkdir(exist_ok=True)


def write_text(path: Path, text: str):
    print('create file:')
    print(path)
    if isinstance(text, list):
        path.write_text('\n'.join(text), encoding='utf-8')
    elif isinstance(text, str):
        path.write_text(text, encoding='utf-8')


def init_project(args: Namespace):
    """ Init a project from user inputs """
    msg = [
        '--- physmet-folders ---',
        'Please enter the project info (simply pressing Enter, leaving ',
        'the prompt empty, will accept the default value shown in brackets.',
        '--- ctrl+c to abort the program ---'
    ]
    print('\n'.join(msg))
    project = userinput('Project/Folder name', args.project)
    if not project:
        print('error: project name can not be empty.')
    else:
        author = userinput('Author name', username())
        cwd = userinput('Destination directory', Path.cwd())
        wd = Path(cwd)
        if wd.exists():
            pdir = wd / project
            if pdir.exists():
                print('error: the project directory already exists.')
            else:
                # create directory and files
                mkdir(pdir)
                write_text(pdir / 'info.txt', [
                    f'Name: {project}',
                    f'Author: {author}'
                ])
                mkdir(pdir / 'SEM')
                write_text(pdir / 'SEM/samples.csv',
                           text='SampleId, Date(YYYY-MM-DD)\n')
                # add the project in the global config.json
                prj = read_config('projects')
                if not prj:
                    prj = []
                prj.append({'name': project, 'path': pdir})
                write_config('projects', prj)
                if len(prj) == 1:
                    write_config('default', project)
        else:
            print('error: the destination directory does not exist.')


def list_projects():
    """ List the project created with this program """
    prj = read_config('projects')
    if not prj:
        print('no projects found.')
    else:
        print(f'{len(prj)} available projects (*=default):')
        name = read_config('default')
        for item in prj:
            default = '*' if item['name'] == name else ' '
            print(f'{default} {item["name"]} ({item["path"]})')


def list_samples(args):
    print(f'error: list the samples "{args.sample}" not yet implemented.')


def set_default(args):
    """ Set the default project """
    if args.project:
        prj = find_project(args.project)
        if prj:
            write_config('default', args.project)
        else:
            print(f'error: project not found "{args.project}".')
    else:
        print('error: cannot set the default project (name not given).')


def datacheck(args: Namespace):
    print('error: datacheck not yet implemented.')


def add_sample(args: Namespace):
    """ Create a folder SAMPLE_YYYYMMDD """
    if args.sample and args.date:
        date = None
        try:
            if '-' in args.date:
                date = datetime.strptime(args.date, '%Y-%m-%d')
            else:
                date = datetime.strptime(args.date, '%Y%m%d')
        except Exception as ex:
            print('error: expected date formats: "yyyymmdd" or "yyyy-mm-dd".')
            print(ex)
            date = None

        if date is not None:
            name = read_config('default')
            prj = find_project(name)
            if prj:
                if prj.exists():
                    cwd = prj / f'SEM/{args.sample}_{args.date}'
                    mkdir(cwd)
                    write_text(cwd / 'info.txt', [
                        f'SampleId: {args.sample}', f'Date: {args.date}'
                    ])
                else:
                    print(f'error: project path does not exists for "{name}":')
                    print(prj)
            else:
                print('error: default project not found.')


def main():
    parser = ArgumentParser(
        prog=__appname__,
        description='Create project folder and files for PhysMet data.',
    )
    parser.add_argument('task', choices=[
        'init', 'datacheck', 'add', 'list', 'set-default'
    ])
    parser.add_argument('-p', '--project')
    parser.add_argument('-s', '--sample')
    parser.add_argument('-d', '--date')

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)

    args = parser.parse_args()

    if args.task == 'init':
        init_project(args)

    elif (args.task == 'add') and args.project:
        init_project(args)

    elif (args.task == 'add') and args.sample:
        add_sample(args)

    elif args.task == 'list':
        if args.sample:
            list_samples(args)
        else:
            list_projects()

    elif args.task == 'set_default':
        set_default(args)

    elif args.task == 'datacheck':
        datacheck(args)


if __name__ == '__main__':
    main()
